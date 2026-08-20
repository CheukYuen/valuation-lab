import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lab"))

from record_contract import STATES, validate_record  # noqa: E402

RECORDS = ROOT / "cases" / "00-records"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


class RecordContractTests(unittest.TestCase):
    def test_samples_exist(self):
        self.assertTrue(sorted(RECORDS.glob("*.json")), "no record fixtures found")

    def test_each_sample_fires_exactly_its_expected_codes(self):
        # The point of the fixture set is that it pins both directions: a sample
        # declaring no expected codes must stay silent, not merely "mostly quiet".
        failures = []
        for path in sorted(RECORDS.glob("*.json")):
            record = load(path)
            expected = sorted(record.get("expect_codes", []))
            actual = sorted(finding.code for finding in validate_record(record))
            if actual != expected:
                failures.append(f"{path.name}: expected {expected}, got {actual}")
        self.assertEqual(failures, [], "\n".join(failures))

    def test_negative_control_is_silent(self):
        # A validator that flags a fully-documented consensus is an indiscriminate
        # alarm; DAY-1 teaches that "when not to flag" is half the skill.
        record = load(RECORDS / "10-negative-control.json")
        self.assertTrue(record.get("labelled_as_consensus"))
        self.assertEqual(validate_record(record), [])

    def test_clean_record_is_silent(self):
        self.assertEqual(validate_record(load(RECORDS / "01-clean.json")), [])

    def test_every_failure_state_has_at_least_one_sample(self):
        covered = set()
        for path in RECORDS.glob("*.json"):
            covered.update(load(path).get("expect_codes", []))
        self.assertEqual(set(STATES) - covered, set(), "failure states with no fixture")

    def test_codes_never_leave_the_documented_vocabulary(self):
        for path in sorted(RECORDS.glob("*.json")):
            for finding in validate_record(load(path)):
                self.assertIn(finding.code, STATES, path.name)
                self.assertTrue(finding.message and finding.field, path.name)

    def test_pit_ordering_is_enforced_in_both_directions(self):
        base = load(RECORDS / "01-clean.json")
        self.assertEqual(validate_record(base), [])

        future_source = dict(base, source_published_at="2026-04-20", adopted_at="2026-04-20")
        self.assertEqual([f.code for f in validate_record(future_source)], ["pit"])

        adopted_before_publication = dict(base, adopted_at="2026-03-20")
        self.assertEqual([f.code for f in validate_record(adopted_before_publication)], ["pit"])

    def test_page_number_change_does_not_downgrade(self):
        # The regression case from DAY-1's test-writing exercise: a pointer that
        # merely becomes more precise must not move any status.
        base = load(RECORDS / "01-clean.json")
        moved = dict(base, evidence_pointer="2026-03-28指引公告 第4页 表1")
        self.assertEqual(validate_record(moved), [])


if __name__ == "__main__":
    unittest.main()
