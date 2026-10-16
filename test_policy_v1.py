"""Checks specific to the submitted v1 policy (in addition to the kit's own tests)."""
import json
import os
import subprocess
import sys
import time
import unittest

import policy
from evaluate import validate_response, VARIANTS
from kit import Simulator, generate, eligibility


def fresh(request):
    policy._START = time.monotonic()
    return policy.decide(request)


class V1Tests(unittest.TestCase):
    def test_empty_state_both_phases(self):
        state = Simulator(generate(42, 0)).observe()
        for phase, key in (('ask', 'asks'), ('match', 'pairs')):
            out = fresh({'schema_version': '1.0.0', 'phase': phase, 'state': state, 'memory': None})
            self.assertEqual(out, {key: [], 'memory': {}})

    def test_cli_without_arguments_like_container(self):
        state = Simulator(generate(7, 30)).observe()
        raw = json.dumps({'schema_version': '1.0.0', 'phase': 'ask', 'state': state, 'memory': None})
        proc = subprocess.run([sys.executable, 'policy.py'], input=raw, capture_output=True, text=True, timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        validate_response(json.loads(proc.stdout), 'ask')

    def test_full_episodes_valid_in_every_family(self):
        for variant in VARIANTS:
            sim = Simulator(generate(900 + len(variant), 200, variant=variant))
            for _ in range(60):
                asks = fresh({'phase': 'ask', 'state': sim.observe(), 'memory': None})['asks']
                self.assertLessEqual(sum(3 if a['field'] == 'constraints' else 1 for a in asks), 12)
                sim.resolve_asks(asks)
                state = sim.observe()
                pairs = fresh({'phase': 'match', 'state': state, 'memory': None})['pairs']
                by = {m['member_id']: m for m in state['members']}
                used = [x for p in pairs for x in p]
                self.assertEqual(len(used), len(set(used)))
                for a, b in pairs:
                    self.assertEqual(eligibility(by[a], by[b])['status'], 'feasible')
                sim.advance(pairs)

    def test_shield_drops_invalid_actions(self):
        state = Simulator(generate(5, 60)).observe()
        bad_asks = [{'member_id': 'nobody', 'field': 'constraints'}, {'member_id': 1, 'field': 'x'}] * 3
        self.assertEqual(policy.shield_asks(state, bad_asks), [])
        ids = [m['member_id'] for m in state['members']][:2]
        self.assertTrue(len(policy.shield_pairs(state, [ids, ids, [ids[0], ids[0]], ['a', 'b']])) <= 1)

    def test_degrades_safely_when_component_fails(self):
        state = Simulator(generate(5, 60)).observe()
        saved = policy.CONFIGS['v1']
        policy.CONFIGS['v1'] = (lambda s: 1 / 0, lambda s: 1 / 0)
        try:
            validate_response(fresh({'phase': 'ask', 'state': state, 'memory': None}), 'ask')
            validate_response(fresh({'phase': 'match', 'state': state, 'memory': None}), 'match')
        finally:
            policy.CONFIGS['v1'] = saved

    def test_docker_context_includes_vendored_networkx(self):
        rules = open('.dockerignore').read().split()
        self.assertIn('!vendor/**', rules)
        self.assertTrue(os.path.isfile('vendor/networkx/__init__.py'))


if __name__ == '__main__':
    unittest.main()
