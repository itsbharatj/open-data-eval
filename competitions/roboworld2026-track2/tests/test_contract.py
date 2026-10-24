import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from havln_tools import ContractError, check_rows, validate_submission_zip, write_submission


class ContractTests(unittest.TestCase):
    def test_six_actions_and_budget_boundary(self):
        rows = [{"episode_id": "1", "actions": ["LOOK_UP", "LOOK_DOWN", "STOP"]},
                {"episode_id": "2", "actions": ["MOVE_FORWARD"] * 500}]
        check_rows(rows, ["1", "2"])
        for actions in ([], ["MOVE_FORWARD"], ["STOP", "STOP"], ["STOP"] * 501, ["WAIT"], ["STOP", "MOVE_FORWARD"]):
            with self.assertRaises(ContractError, msg=str(actions)[:40]):
                check_rows([{"episode_id": "1", "actions": actions}], ["1"])

    def test_exact_coverage(self):
        row = {"episode_id": "1", "actions": ["STOP"]}
        for rows, expected in (([row], ["1", "2"]), ([row], ["2"]), ([row, row], ["1"])):
            with self.assertRaises(ContractError):
                check_rows(rows, expected)

    def test_roundtrip_write_and_validate(self):
        with tempfile.TemporaryDirectory() as d:
            preds = {"val_seen": {"1": ["MOVE_FORWARD", "STOP"], "2": ["STOP"]},
                     "val_unseen": {"5": ["TURN_LEFT"] * 500}}
            expected = {"val_seen": ["1", "2"], "val_unseen": ["5"]}
            zp = write_submission(Path(d), preds, expected)
            self.assertEqual(validate_submission_zip(zp, expected), {"val_seen": 2, "val_unseen": 1})
            with zipfile.ZipFile(zp) as zf:
                names = sorted(zf.namelist())
            self.assertEqual(names, ["val_seen.json", "val_unseen.json"])

    def test_nested_member_and_missing_split_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            zp = Path(d) / "bad.zip"
            with zipfile.ZipFile(zp, "w") as zf:
                zf.writestr("sub/val_seen.json", json.dumps({"format_version": 1, "split": "val_seen", "episodes": []}))
            with self.assertRaises(ContractError):
                validate_submission_zip(zp, {"val_seen": []})
            zp2 = Path(d) / "missing.zip"
            with zipfile.ZipFile(zp2, "w") as zf:
                zf.writestr("val_seen.json", json.dumps({"format_version": 1, "split": "val_seen",
                                                          "episodes": [{"episode_id": "1", "actions": ["STOP"]}]}))
            with self.assertRaises(ContractError):
                validate_submission_zip(zp2, {"val_seen": ["1"], "val_unseen": ["2"]})


if __name__ == "__main__":
    unittest.main()
