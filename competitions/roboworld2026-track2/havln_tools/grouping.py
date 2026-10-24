"""Group HA-R2R episodes that share a trajectory (R2R has 3 instructions per path).

Phase 2 may or may not expose `trajectory_id`; fall back to grouping by
(scene, rounded start position, rounded start rotation).
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Mapping, Tuple


def _key(ep: Mapping, pos_decimals: int = 2, rot_decimals: int = 3) -> Tuple:
    if ep.get("trajectory_id") is not None:
        return ("traj", str(ep["trajectory_id"]), ep.get("scene_id"))
    pos = tuple(round(float(x), pos_decimals) for x in ep["start_position"])
    rot = tuple(round(float(x), rot_decimals) for x in ep.get("start_rotation", ()))
    return ("pose", ep.get("scene_id"), pos, rot)


def group_by_path(episodes: Iterable[Mapping]) -> Dict[Tuple, List[str]]:
    """Return {group_key: [episode_id, ...]}; groups of size 3 are expected for R2R-derived data."""
    groups: Dict[Tuple, List[str]] = defaultdict(list)
    for ep in episodes:
        groups[_key(ep)].append(str(ep["episode_id"]))
    return dict(groups)
