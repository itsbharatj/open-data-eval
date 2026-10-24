"""Official HA-VLN Track 2 metrics and composite Score.

Sources (verified 2026-10-24):
  * roboworld2026/track2 README, section "Evaluation" / "Composite Score".
  * UWMILab/HA-VLN HASimulator/metric.py (per-episode TCR/CR/SR adjustment).
  * UWMILab/HA-VLN agent/VLN-CE/vlnce_baselines/common/base_il_trainer.py (aggregation).

Per-episode (metric.py):
    TCR_ep = max(0, collisions_count - collision_num[episode_id])
    CR_ep  = min(TCR_ep, 1)
    SR_ep  = success_ep * (TCR_ep == 0)
where collisions_count = number of simulator steps whose `previous_step_collided`
flag was True (walls AND humans; humans are static navmesh obstacles) and
collision_num is the organizer-released per-episode baseline count.

Aggregates (README): SR, NE, TCR are means over ALL episodes. CR is described as the
"collision-episode rate over human-influenced episodes" (682 / 1,593 / 2,859 episodes
for val_seen / val_unseen / test), while the released trainer code simply averages
CR_ep over all episodes. The published CMA row (CR .623) is consistent with the
all-episode mean and would exceed 0.7 under the human-influenced denominator, so the
default here is `cr_mode="all"`; `cr_mode="human_influenced"` is provided for the
README reading. Confirm against the scorer package inside the official image
(/opt/havln-challenge/scoring) on day 1. For a zero-collision tape both give CR = 0.

Composite (README, full precision, higher is better):
    Navigation = 0.80*SR + 0.20*3/(3+NE)
    Social     = 0.75*(1-CR) + 0.25*1/(1+TCR)
    Score      = 100 * Navigation * (0.70 + 0.30*Social)
Ties: higher SR, lower NE, lower CR, lower TCR, earlier submission.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional

SUCCESS_DISTANCE_M = 3.0

#: Episodes per split (toolkit README).
SPLIT_SIZES: Dict[str, int] = {
    "train": 10819,
    "val_seen": 778,
    "val_unseen": 1839,
    "test": 3408,
}

#: Human-influenced episode counts (organizer README table, havln-challenge@8e36fa7 L87-91; also = beta * split size
#: with beta from HASimulator/metric.py: 1-1615/10819, 1-96/778, 1-246/1839, 1-549/3408).
HUMAN_INFLUENCED: Dict[str, int] = {
    "train": 9204,
    "val_seen": 682,
    "val_unseen": 1593,
    "test": 2859,
}


@dataclass(frozen=True)
class EpisodeResult:
    """Raw replay outcome for one episode."""

    episode_id: str
    distance_to_goal: float  # metres, at STOP / step limit
    collisions_count: int  # steps with previous_step_collided == True
    stopped_within_success_distance: Optional[bool] = None

    @property
    def success_geom(self) -> bool:
        if self.stopped_within_success_distance is not None:
            return bool(self.stopped_within_success_distance)
        return self.distance_to_goal <= SUCCESS_DISTANCE_M


@dataclass(frozen=True)
class SplitMetrics:
    n: int
    SR: float
    NE: float
    CR: float
    TCR: float
    Score: float
    cr_mode: str

    def as_dict(self) -> Dict[str, float]:
        return {
            "n": self.n,
            "SR": self.SR,
            "NE": self.NE,
            "CR": self.CR,
            "TCR": self.TCR,
            "Score": self.Score,
            "cr_mode": self.cr_mode,
        }


def episode_metrics(result: EpisodeResult, baseline_collisions: int) -> Dict[str, float]:
    """Apply HASimulator/metric.py to one episode."""
    tcr = max(0, int(result.collisions_count) - int(baseline_collisions))
    cr = min(tcr, 1)
    sr = int(result.success_geom) * int(tcr == 0)
    return {"SR": sr, "NE": float(result.distance_to_goal), "CR": cr, "TCR": tcr}


def navigation_term(sr: float, ne: float) -> float:
    return 0.80 * sr + 0.20 * 3.0 / (3.0 + ne)


def social_term(cr: float, tcr: float) -> float:
    return 0.75 * (1.0 - cr) + 0.25 * 1.0 / (1.0 + tcr)


def composite_score(sr: float, ne: float, cr: float, tcr: float) -> float:
    return 100.0 * navigation_term(sr, ne) * (0.70 + 0.30 * social_term(cr, tcr))


def aggregate(
    results: Iterable[EpisodeResult],
    baseline_collisions: Mapping[str, int],
    split: str = "val_unseen",
    cr_mode: str = "all",
) -> SplitMetrics:
    """Aggregate per-episode replay outcomes into official-style split metrics.

    cr_mode:
      "all"              -> CR = mean(CR_ep) over all episodes          (trainer aggregation; default)
      "human_influenced" -> CR = sum(CR_ep) / HUMAN_INFLUENCED[split]   (README wording; may exceed 1)
    """
    rows = list(results)
    n = len(rows)
    if n == 0:
        raise ValueError("no episodes")
    sr_sum = ne_sum = cr_sum = tcr_sum = 0.0
    for r in rows:
        m = episode_metrics(r, baseline_collisions.get(str(r.episode_id), 0))
        sr_sum += m["SR"]
        ne_sum += m["NE"]
        cr_sum += m["CR"]
        tcr_sum += m["TCR"]
    sr = sr_sum / n
    ne = ne_sum / n
    tcr = tcr_sum / n
    if cr_mode == "human_influenced":
        denom = HUMAN_INFLUENCED.get(split)
        if denom is None:
            raise ValueError(f"unknown split {split!r} for human-influenced normalisation")
        cr = cr_sum / denom  # not clipped: the README reading can exceed 1 if non-influenced episodes collide
    elif cr_mode == "all":
        cr = cr_sum / n
    else:
        raise ValueError(f"unknown cr_mode {cr_mode!r}")
    return SplitMetrics(n=n, SR=sr, NE=ne, CR=cr, TCR=tcr, Score=composite_score(sr, ne, cr, tcr), cr_mode=cr_mode)
