"""Submission contract for RoboWorld 2026 Track 2.

Mirrors roboworld2026/track2 scripts/export_cma_submission.py::check_rows and
the README "Submission Format" + FAQ Q6 rules:
  * six actions: STOP, MOVE_FORWARD, TURN_LEFT, TURN_RIGHT, LOOK_UP, LOOK_DOWN
  * 1..500 actions per episode; sequences shorter than 500 MUST end with STOP;
    STOP may appear only once and only as the last action
  * every official episode id exactly once per split
  * JSON: {"format_version": 1, "split": <split>, "episodes": [{"episode_id": str, "actions": [...]}, ...]}
  * ZIP: flat members only (no nested paths), no unsafe members; one JSON per required split,
    identified by its "split" value (file names are free).
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Mapping, Sequence

ACTIONS = ("STOP", "MOVE_FORWARD", "TURN_LEFT", "TURN_RIGHT", "LOOK_UP", "LOOK_DOWN")
MAX_ACTIONS = 500
FORMAT_VERSION = 1


class ContractError(ValueError):
    pass


def check_actions(actions: Sequence[str]) -> None:
    if not 1 <= len(actions) <= MAX_ACTIONS:
        raise ContractError(f"sequence length {len(actions)} outside 1..{MAX_ACTIONS}")
    bad = [a for a in actions if a not in ACTIONS]
    if bad:
        raise ContractError(f"invalid action names: {sorted(set(bad))[:5]}")
    if "STOP" in actions[:-1]:
        raise ContractError("STOP must occur only as the final action")
    if len(actions) < MAX_ACTIONS and actions[-1] != "STOP":
        raise ContractError("sequences shorter than 500 actions must end with STOP")


def check_rows(rows: Iterable[Mapping], expected_ids: Iterable[str]) -> None:
    rows = list(rows)
    ids = [str(r["episode_id"]) for r in rows]
    expected = set(str(i) for i in expected_ids)
    if len(ids) != len(set(ids)):
        dup = sorted({i for i in ids if ids.count(i) > 1})
        raise ContractError(f"duplicate episode ids: {dup[:5]}")
    if set(ids) != expected:
        missing = sorted(expected - set(ids), key=lambda s: (len(s), s))
        extra = sorted(set(ids) - expected, key=lambda s: (len(s), s))
        raise ContractError(f"coverage mismatch: missing={missing[:5]} ({len(missing)}), extra={extra[:5]} ({len(extra)})")
    for r in rows:
        try:
            check_actions(list(r["actions"]))
        except ContractError as e:
            raise ContractError(f"episode {r['episode_id']}: {e}") from None


def load_prediction_file(path: Path) -> Dict:
    data = json.loads(Path(path).read_text())
    for key in ("format_version", "split", "episodes"):
        if key not in data:
            raise ContractError(f"{path}: missing key {key!r}")
    if data["format_version"] != FORMAT_VERSION:
        raise ContractError(f"{path}: format_version must be {FORMAT_VERSION}")
    return data


def write_submission(out_dir: Path, predictions: Mapping[str, Mapping[str, Sequence[str]]],
                     expected_ids: Mapping[str, Iterable[str]], zip_name: str = "submission.zip") -> Path:
    """predictions: {split: {episode_id: actions}}. Validates, writes <split>.json files and a flat ZIP."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    names: List[str] = []
    for split, per_ep in predictions.items():
        rows = [{"episode_id": str(k), "actions": list(v)} for k, v in per_ep.items()]
        check_rows(rows, expected_ids[split])
        rows.sort(key=lambda r: (len(r["episode_id"]), r["episode_id"]))
        payload = {"format_version": FORMAT_VERSION, "split": split, "episodes": rows}
        name = f"{split}.json"
        (out_dir / name).write_text(json.dumps(payload, indent=None, separators=(",", ":"), allow_nan=False) + "\n")
        names.append(name)
    zip_path = out_dir / zip_name
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in names:
            zf.write(out_dir / name, arcname=name)
    return zip_path


def validate_submission_zip(zip_path: Path, expected_ids: Mapping[str, Iterable[str]]) -> Dict[str, int]:
    """Validate a ZIP the way the organizer validator is documented to. Returns {split: n_episodes}."""
    seen: Dict[str, int] = {}
    with zipfile.ZipFile(zip_path) as zf:
        for info in zf.infolist():
            p = PurePosixPath(info.filename)
            if info.is_dir() or len(p.parts) != 1 or p.is_absolute() or ".." in p.parts or "\\" in info.filename:
                raise ContractError(f"unsafe or nested zip member: {info.filename!r}")
            if not info.filename.lower().endswith(".json"):
                continue  # harmless extra root files are allowed
            data = json.loads(zf.read(info.filename))
            split = data.get("split")
            if split not in expected_ids:
                if split is None:
                    continue
                raise ContractError(f"{info.filename}: unexpected split {split!r}")
            if split in seen:
                raise ContractError(f"duplicate split {split!r}")
            if data.get("format_version") != FORMAT_VERSION:
                raise ContractError(f"{info.filename}: bad format_version")
            check_rows(data["episodes"], expected_ids[split])
            seen[split] = len(data["episodes"])
    missing = set(expected_ids) - set(seen)
    if missing:
        raise ContractError(f"missing required splits: {sorted(missing)}")
    return seen
