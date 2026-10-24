import json
import unittest
from pathlib import Path

from havln_tools import (EpisodeResult, HUMAN_INFLUENCED, SPLIT_SIZES, aggregate, composite_score,
                         episode_metrics, navigation_term, social_term)

ROOT = Path(__file__).resolve().parents[1]

# Reference baseline rows from roboworld2026/track2 README (display-rounded components, full-precision Score).
CMA = {
    "val_seen": dict(SR=0.180, NE=6.223, CR=0.623, TCR=13.726, Score=16.509450),
    "val_unseen": dict(SR=0.129, NE=6.387, CR=0.684, TCR=17.536, Score=12.945387),
}


class ScoreFormulaTests(unittest.TestCase):
    def test_reproduces_published_cma_scores_within_rounding(self):
        # Components are rounded to 3 decimals in the README; the Score is full precision.
        # Rounding SR by ±0.0005 alone moves Score by ~±0.04, so a 0.06 tolerance is the honest bound.
        for split, m in CMA.items():
            got = composite_score(m["SR"], m["NE"], m["CR"], m["TCR"])
            self.assertAlmostEqual(got, m["Score"], delta=0.06, msg=split)

    def test_official_integer_counts_reproduce_val_seen_score(self):
        # research/A4: exact counts behind the published val_seen row (NE is only known to 3 decimals).
        sr, cr, tcr = 140 / 778, 425 / 682, 10679 / 778
        self.assertAlmostEqual(composite_score(sr, 6.223, cr, tcr), 16.509450, delta=0.002)
        sr2, cr2 = 237 / 1839, 1090 / 1593
        self.assertAlmostEqual(composite_score(sr2, 6.387, cr2, 17.536), 12.945387, delta=0.003)

    def test_default_cr_mode_is_human_influenced(self):
        rows = [EpisodeResult(str(i), distance_to_goal=1.0, collisions_count=(1 if i < 10 else 0)) for i in range(100)]
        m = aggregate(rows, {str(i): 0 for i in range(100)}, split="val_unseen")
        self.assertEqual(m.cr_mode, "human_influenced")
        self.assertAlmostEqual(m.CR, 10 / 1593)

    def test_perfect_run_scores_100(self):
        self.assertAlmostEqual(composite_score(1.0, 0.0, 0.0, 0.0), 100.0)

    def test_zero_collisions_gives_full_social_multiplier(self):
        self.assertAlmostEqual(social_term(0.0, 0.0), 1.0)
        # Social multiplier range is 0.70..1.00
        self.assertAlmostEqual(social_term(1.0, 1e9), 0.0, places=6)

    def test_navigation_term_monotone(self):
        self.assertGreater(navigation_term(0.6, 2.0), navigation_term(0.5, 2.0))
        self.assertGreater(navigation_term(0.6, 1.0), navigation_term(0.6, 2.0))

    def test_episode_adjustment_rules(self):
        r = EpisodeResult("7", distance_to_goal=1.2, collisions_count=2)
        self.assertEqual(episode_metrics(r, baseline_collisions=2), {"SR": 1, "NE": 1.2, "CR": 0, "TCR": 0})
        self.assertEqual(episode_metrics(r, baseline_collisions=1), {"SR": 0, "NE": 1.2, "CR": 1, "TCR": 1})
        self.assertEqual(episode_metrics(r, baseline_collisions=5)["TCR"], 0)
        far = EpisodeResult("8", distance_to_goal=3.01, collisions_count=0)
        self.assertEqual(episode_metrics(far, 0)["SR"], 0)
        edge = EpisodeResult("9", distance_to_goal=3.0, collisions_count=0)
        self.assertEqual(episode_metrics(edge, 0)["SR"], 1)

    def test_aggregate_cr_modes(self):
        rows = [EpisodeResult(str(i), distance_to_goal=1.0, collisions_count=(1 if i < 10 else 0)) for i in range(100)]
        base = {str(i): 0 for i in range(100)}
        m_all = aggregate(rows, base, split="val_unseen", cr_mode="all")
        m_hi = aggregate(rows, base, split="val_unseen", cr_mode="human_influenced")
        self.assertAlmostEqual(m_all.CR, 0.10)
        self.assertAlmostEqual(m_hi.CR, 10 / HUMAN_INFLUENCED["val_unseen"])
        self.assertEqual(HUMAN_INFLUENCED["val_seen"], 682)
        self.assertEqual(HUMAN_INFLUENCED["test"], 2859)
        # beta from HASimulator/metric.py reproduces the organizer table
        for split, n, non_influenced in (("val_seen", 778, 96), ("val_unseen", 1839, 246), ("test", 3408, 549)):
            self.assertEqual(HUMAN_INFLUENCED[split], n - non_influenced)
        self.assertAlmostEqual(m_all.SR, 0.90)
        self.assertAlmostEqual(m_all.TCR, 0.10)

    def test_released_collision_baselines_match_split_sizes(self):
        for split in ("val_seen", "val_unseen", "test"):
            d = json.loads((ROOT / "data" / f"collision_num_{split}.json").read_text())
            self.assertEqual(len(d), SPLIT_SIZES[split], split)
            self.assertTrue(all(isinstance(v, int) and v >= 0 for v in d.values()))


if __name__ == "__main__":
    unittest.main()
