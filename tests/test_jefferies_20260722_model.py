import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs" / "yofc"))

import jefferies_20260722_model as model  # noqa: E402


class Jefferies20260722ModelTests(unittest.TestCase):
    def test_pb_and_pe_paths(self):
        result = model.independent_bridge()
        self.assertAlmostEqual(result["pb_tp_rmb"], 124.962582, places=6)
        self.assertAlmostEqual(result["pe_tp_rmb"], 132.117, places=6)
        self.assertAlmostEqual(
            result["simple_average_of_tp_rmb"], 128.539791, places=6
        )

    def test_missing_average_bridge_is_not_silently_closed(self):
        result = model.independent_bridge()
        audit = model.audit_summary()
        self.assertAlmostEqual(result["average_bridge_gap_rmb"], -6.759791, places=6)
        self.assertTrue(audit["average_bridge_gap_detected"])
        self.assertEqual(audit["average_bridge_status"], "MISSING")

    def test_reported_component_bridge_and_rounding(self):
        result = model.reported_bridge()
        self.assertAlmostEqual(result["component_sum_rmb"], 132.74, places=2)
        self.assertAlmostEqual(result["reported_sotp_pt_rmb"], 132.73, places=2)
        self.assertAlmostEqual(result["component_rounding_gap_rmb"], -0.01, places=2)
        self.assertAlmostEqual(result["reported_sotp_pt_hkd"], 153.74, places=2)

    def test_currency_direction(self):
        result = model.reported_bridge()
        fx = result["implied_cny_per_hkd"]
        self.assertAlmostEqual(fx, 0.863340705, places=9)
        self.assertAlmostEqual(model.rmb_to_hkd(132.73, fx), 153.74, places=2)

    def test_2026_eps_implies_old_share_denominator(self):
        audit = model.audit_summary()
        self.assertAlmostEqual(audit["implied_2026_share_count_m"], 760.664336, places=6)
        self.assertAlmostEqual(
            audit["reported_period_end_share_count_m"], 827.905108, places=6
        )
        self.assertAlmostEqual(audit["share_count_gap_m"], -67.240772, places=6)

    def test_upstream_component_statuses_remain_explicit(self):
        audit = model.audit_summary()
        self.assertEqual(audit["everprox_upstream_status"], "PARTIAL")
        self.assertEqual(audit["diversified_upstream_status"], "MISSING")

    def test_simple_average_rejects_empty_input(self):
        with self.assertRaises(ValueError):
            model.simple_average()


if __name__ == "__main__":
    unittest.main()
