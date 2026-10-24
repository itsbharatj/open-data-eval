# W0 — Ops & organizer liaison (start today)

Goal: remove every external blocker in the first 48 hours and keep the submission channel healthy.

Tasks (today):
- Register the team: https://forms.gle/P2jH3c2VoGsNNWXG8 (one account per team; note the CodaBench user that will submit).
- File the five questions from `01-strategy.md` §7 as ONE GitHub issue on https://github.com/roboworld2026/track2/issues,
  post the same on Discord https://discord.gg/S8s8JcxtT, and email roboworld2026@gmail.com. Ask specifically whether branch
  `bohan/clarification-Oct14` is binding. Record answers verbatim in `research/organizer-answers.md`.
- Matterport3D: download the Terms of Use PDF from https://niessner.github.io/Matterport/, sign, email matterport3d@googlegroups.com
  from an institutional address; send a second request from a second affiliated person; look for an existing lab licence.
  Anecdotal latency is weeks — this is the zero-float item. Daily follow-up.
- Pull the image now (6.1 GB): `docker pull ghcr.io/jostarxiong/havln-challenge-2026@sha256:e1a0544f66beaf5218cc9df63da51b4a1a22a6bf0471ca0c2f75e81ee02a6556`
  and run `bash scripts/download_data.sh --destination $DATA_ROOT --target all` from the toolkit (HF + GitHub assets, no MP3D needed).
- Watch CodaBench status (down since Oct 21; codalab/codabench issue #2679). If still down on Oct 29, ask organizers for an
  alternate channel (Q5).

Submission policy: 5 per UTC day, 100 per phase; first Phase 2 upload = STOP-only anchor (predictable Score, confirms Euclidean NE),
second = v0 pipeline; keep 30 slots in reserve; never upload in the last 2 h of a UTC day; log every upload in `RESULTS.md`.

Report: a dated log of requests sent, answers received, data on disk (paths + sha256), and CodaBench status.
