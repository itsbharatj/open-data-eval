"""Group HA-R2R episodes that share a trajectory (R2R has 3 instructions per path).

Preferred key: `trajectory_id` (= R2R path_id). Fallback when it is absent: contiguous integer episode ids form
blocks 3k+1..3k+3 per trajectory (verified 1,136/1,136 on test and 613/613 on val_unseen; val_seen has one
4-instruction trajectory, so always prefer trajectory_id there). Start pose is NOT a valid key: 788 distinct
starts serve 1,136 test trajectories (research/A1, C10). Pose is only used as a consistency check.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List, Mapping, Tuple


def _pose_key(ep: Mapping, pos_decimals: int = 2) -> Tuple:
    pos = tuple(round(float(x), pos_decimals) for x in ep.get("start_position", ()))
    return (ep.get("scene_id"), pos)


def group_by_path(episodes: Iterable[Mapping], check_pose: bool = True) -> Dict[Tuple, List[str]]:
    """Return {group_key: [episode_id, ...]}; groups of size 3 are expected for R2R-derived data."""
    eps = list(episodes)
    groups: Dict[Tuple, List[str]] = defaultdict(list)
    if eps and all(ep.get("trajectory_id") is not None for ep in eps):
        for ep in eps:
            groups[("traj", str(ep["trajectory_id"]))].append(str(ep["episode_id"]))
    elif eps and all(str(ep["episode_id"]).isdigit() for ep in eps):
        for ep in eps:
            k = (int(ep["episode_id"]) - 1) // 3
            groups[("idblock", k)].append(str(ep["episode_id"]))
    else:
        for ep in eps:
            groups[("pose",) + _pose_key(ep)].append(str(ep["episode_id"]))
    if check_pose:
        by_id = {str(ep["episode_id"]): ep for ep in eps}
        for key, ids in groups.items():
            poses = {_pose_key(by_id[i]) for i in ids if by_id[i].get("start_position") is not None}
            if len(poses) > 1:
                raise ValueError(f"group {key} mixes different start poses: {sorted(ids)}")
    return dict(groups)
