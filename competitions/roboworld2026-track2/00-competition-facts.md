# RoboWorld 2026 Track 2 (HA-VLN 2.0) — verified fact sheet

Compiled 2026-10-24 from the official toolkit (`roboworld2026/track2`), the challenge website source
(`roboworld2026/roboworld2026.github.io`), the upstream benchmark code (`UWMILab/HA-VLN`) and the earlier
toolkit copy (`F1y1113/havln-challenge`). Every line below was read from source, not from memory.

## Identity and links
| Item | Value |
|---|---|
| Track | Track 2 · HA-VLN 2.0 · Human-Aware Social Navigation (continuous, Habitat 0.1.7) |
| Benchmark paper | HA-VLN 2.0, IROS 2026, arXiv 2503.14229 (v2 title: "HA-VLN: A Benchmark for Human-Aware Navigation in Discrete–Continuous Environments…") |
| Toolkit | https://github.com/roboworld2026/track2 (mirror: JostarXiong/track2; older copy: F1y1113/havln-challenge) |
| Upstream code | https://github.com/UWMILab/HA-VLN (pinned revision f46f936) |
| Data | HF dataset `fly1113/HA-VLN` (revision c5f1cec…) + Google Drive mirrors; Matterport3D under its own licence |
| Submission | CodaBench competition 18135 (Track 1 = 18185, Track 3 = 18333) |
| Registration | Google Form https://forms.gle/P2jH3c2VoGsNNWXG8 (required for leaderboard/awards) |
| Docker image | `ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f…` (6.1 GB; tags v0.1.0-test-*, cr-domain-20261004) |
| Contact | roboworld2026@gmail.com · Discord https://discord.gg/S8s8JcxtT · GitHub issues on the toolkit |
| Organizers | Lingdong Kong (NUS), Yifei Dong, Fengyi Wu, Yetong Sha, Bohan Xiong (UW, UWMILab), Shaoyuan Xie, Junhao Liu (UCI), Wei Chow (NUS), Zihan Zhang (UCSD), Qing Wu (NTU) … affiliated with RoboPAD @ NeurIPS 2026 |

## Timeline (all 2026)
| Date | Event |
|---|---|
| Oct 08 | Registration opens |
| Oct 15 | Phase 1 (validation) opens; data, baselines, servers online |
| **Oct 30** | Phase 1 closes · **Phase 2 (test) opens — held-out bundle released** |
| **Nov 30** | Phase 2 closes (final) |
| Dec 12 | Awards announced |

Submission limits: 5 per day, 100 per phase, best score retained. Phase 1 and Phase 2 are not combined;
**final ranking and awards are decided entirely by Phase 2.**

## Task contract
* Input per episode: episode ID, initial position and yaw, instruction, "released human-aware episode inputs".
* Output: one action sequence from `STOP, MOVE_FORWARD (0.25 m), TURN_LEFT/TURN_RIGHT (15°), LOOK_UP, LOOK_DOWN`;
  1–500 actions; `STOP` at most once and only last; sequences < 500 must end with `STOP`; LOOK actions count.
* No code, weights or containers are submitted. Scoring = replay of the sequences in the organizers' image
  (`TASK.SENSORS=[INSTRUCTION_SENSOR]`, humans added, seed 0, scan-sharded).
* JSON: `{"format_version":1,"split":"val_unseen","episodes":[{"episode_id":"…","actions":[…]}]}`; flat ZIP, one file per
  required split (Phase 1: `val_seen` 778 + `val_unseen` 1,839; Phase 2: single `test` split, 3,408).
* Award winners (Top-5, Best Innovative Solution, oral) must contribute to a technical report and may be asked for code/models.

## Metrics (exact)
Per episode (`HASimulator/metric.py`): `collisions` = number of steps where Habitat's `previous_step_collided` is true
(walls **and** humans — humans are inserted as static objects and the navmesh is recomputed around them);
`TCR_ep = max(0, collisions − collision_num[ep])` (released per-episode baseline), `CR_ep = min(TCR_ep, 1)`,
`SR_ep = (final distance ≤ 3 m) × (TCR_ep == 0)`.
Aggregates: SR, NE (mean final distance), TCR = means over all episodes; CR normalised by the human-influenced
episode count (96 / 246 / 549 for val_seen / val_unseen / test).

```
Navigation = 0.80·SR + 0.20·3/(3+NE)
Social     = 0.75·(1−CR) + 0.25·1/(1+TCR)
Score      = 100 · Navigation · (0.70 + 0.30·Social)        # ties: SR↑, NE↓, CR↓, TCR↓, earlier submission
```

Baseline (released CMA checkpoint): val_seen SR .180 NE 6.223 CR .623 TCR 13.726 → 16.509;
val_unseen SR .129 NE 6.387 CR .684 TCR 17.536 → 12.945 (reproduced by `havln_tools`, see `benchmarks/score_landscape.md`).

## Data facts
* HA-R2R = R2R-CE episodes (10,819 / 778 / 1,839 / 3,408) with LLM-rewritten instructions (avg 112 words, 20–60 % human content).
  Test = the 18 standard R2R test scans: `2t7WUuJeko7 5ZKStnWn8Zo ARNzJeq3xxb RPmz2sHmrrY UwV83HsGsw3 Vt2qJdWjCF2 WYY7iVyf5p8
  YFuZgdQ5vWj YVUC4YcDtcY fzynW3qQPVF gYvKGZ5eRqb gxdoqLR6rwA jtcxE69GiFV pa4otMbVnkk q9vSo1VnCiC rqfALeAoiTq wc2JMjhGNzB yqstnuAEVhm`.
* Val splits ship with ground-truth `goals` and `reference_path` (standard VLN-CE JSON) → Phase 1 cannot rank anyone.
* Humans: HAPS 2.0 (486 motions × 120 frames; 910 instances). Public `human_motion.json` covers the 72 non-test scans
  (749 humans). Human translation extent: median 0.03 m, mean 0.25 m, p90 0.8 m, max 3.47 m; 6.8 % move > 1 m.
* Human animation is driven by a wall-clock thread (0.1 s signals, frames 0–119, then frozen); actions do not advance frames.
* Collision baselines (`collision_num_*.json`, incl. test) are public in the HA-VLN repo: 93 % of test episodes have baseline 0.
* MP3D connectivity graphs for all 90 scans (incl. test) and HA-VLN-1.0-era human text annotations for all 90 scans
  (`human_motion_text.json`, 374 humans) are public in the HA-VLN repo.
* Simulator config: RGB 224×224 HFOV 90, depth 256×256, forward 0.25 m, turn 15°, sliding allowed, max 500 steps, success 3 m.
