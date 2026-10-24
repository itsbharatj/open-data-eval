# A12: CodaBench platform mechanics for RoboWorld 2026 Track 2 (competition 18135)

Author: research agent A12. Date: 2026-10-24.

Evidence base:
- CodaBench source cloned from https://github.com/codalab/codabench:
  - `master` = release v1.34 (merge 2026-10-13), checked out at `$CB=/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/codabench-master`.
  - `develop` = v1.35, version bump 2026-10-21, not yet tagged, at `$CBD=/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/codabench`.
- CodaBench GitHub issues, fetched with WebFetch: #2679, #2557, #2586, #2627, #2676, #1540, #1840, #2251, #2540.
- Third-party outage threads: Sophelio #13, Agenthon #33 and #44.
- Track 1, 2 and 3 toolkit READMEs, including the git history of the earlier Track 2 toolkit (`ext/havln-challenge`).

Limits on this research:
- www.codabench.org could not be reached. It failed DNS from here, and it has been down for everyone since Oct 21.
- I found no cached or indexed copy of competition 18135 (one search attempt). The shared WebSearch budget then ran out. Archive and proxy fetches are not allowed. So every competition-specific setting below is inferred, and it is listed under "confirm on live site".

Version caveat: production codabench.org most likely runs v1.34 (master). v1.35 has not been tagged. It may be deployed when the site comes back, which could be in the middle of Phase 2. Where the two versions behave differently, I say so.

---

## 0. Top findings (decision-relevant)

1. **The platform is down now, and has been since about 14:00–15:00 UTC on Oct 21** (codalab/codabench#2679, labels P1 and Production).
   - Cause, stated by maintainers ObadaS and Didayolo: Université Paris-Saclay blocks all inbound HTTP(S) as a precaution against a PHP vulnerability. Codabench does not use PHP.
   - On Oct 23 and Oct 24 the maintainers said "we do not have any timeline to share". Their only workaround is that organizers can email info@codabench.org to get a leaderboard CSV.
   - Other challenges are reacting differently. Sophelio moved Final entries to its own pointer website and extended its deadline 48 h. Agenthon kept its deadline and allowed no other channel.
   - Phase 1 of Track 2 ends Oct 30. Phase 2 (test) opens the same day. The test bundle may only be served through CodaBench.
   - Confidence: high.
2. **Submission limits (verified in code): 5 per UTC day and 100 per phase, counted per user account, with failed submissions free.**
   - The count includes every top-level submission by that user in the phase **except status `Failed`** (`$CB/src/apps/competitions/models.py:338-357`).
   - Cancelled, stuck (`Submitting`/`Submitted`/`Running`), soft-deleted and finished submissions all count.
   - The daily window is the UTC calendar date of the upload (`created_when__date=now().date()`, with `TIME_ZONE='UTC'` and `USE_TZ=True` in `$CB/src/settings/base.py:126-129`). The docs say "midnight UTC to midnight the next day UTC". The README's 5/100 are also CodaBench's defaults (`models.py:317-318`).
   - Confidence: high.
3. **"Best score retained" means the `Force_Best` leaderboard rule. It is automatic, and the participant cannot choose or remove the counted entry.**
   - After each scored submission, the platform re-selects the user's single best FINISHED, non-deleted submission in that phase (`$CB/src/apps/leaderboards/strategies.py:72-102`).
   - Ordering: primary column, then every other column left to right, then **earliest `created_when`**.
   - Non-superusers cannot add or remove leaderboard entries under auto rules (`$CB/src/apps/api/views/submissions.py:302`).
   - **If the bundle left `submission_rule` unset, the default is `Add`, which is manual.** Nothing would then reach the leaderboard unless we push it. Confirm on the live site.
   - Confidence: high on mechanics, medium that Force_Best is configured.
4. **Precision: our own scores are visible to 10 decimal places through the API. The public leaderboard is rounded. Ranking uses the stored 10-dp values.**
   - Scores are stored as `DecimalField(max_digits=20, decimal_places=10)` (`$CB/src/apps/leaderboards/models.py:82`).
   - `/api/submissions/` returns them as 10-dp strings for the owner's own submissions, all of them and not only the leaderboard one (`serializers/submissions.py:79-81`).
   - The public `get_leaderboard` rounds each value to the column's `precision` (default 2, maximum 10) on the server (`views/competitions.py:943`).
   - Ranking sorts on the stored values (`serializers/leaderboards.py:181-222`).
   - So if SR, NE, CR and TCR are leaderboard columns, every probe returns exact integer counts (successes, collision episodes, total adjusted collisions) and the sum of final distances to about 3.4e-7 m.
   - Confidence: high.
5. **What participants can see per submission is set by organizer flags, and the Phase 2 values are unknown.**
   - Unless `hide_output` is set, the owner sees 8 log tabs, including scoring stdout and stderr live over a websocket. Unless `hide_score_output` is set, the owner can download the full **"Output from scoring step" ZIP**: everything the scorer writes to `/app/output`, plus `metadata` (`serializers/submissions.py:304-329`, `submission_modal.tag:3-58`).
   - The sibling Track 1 README tells participants to "check the scoring log for validation results and evaluation metrics". Track 2's FAQ quotes scorer log prefixes (`SUBMISSION REJECTED:` / `PASS:` / `SCORING DATA ERROR (organizer):`). Both suggest logs are visible, at least in Phase 1.
   - If the Phase 2 scorer writes per-episode results to its output directory, they could leak. Check this in Phase 1. If anything per-episode appears in Phase 2, report it and do not exploit it (see §8).
   - Confidence: high on mechanics, low on the Phase 2 settings.
6. **The phase boundary times are ambiguous.** This refines C2, which assumed 23:59 UTC.
   - Track 1 states 23:59 UTC.
   - Track 3 states "Phase boundaries on CodaBench follow UTC+8".
   - The **earlier Track 2 README** used Phase 1 "September 30, 2026, 16:00 UTC" to "October 31, 2026, 15:59 UTC", i.e. midnight UTC+8 (`ext/havln-challenge` commits 8e36fa7..4a793d6, README L56-57 in 5ad4380).
   - Conservative assumption until confirmed: **Phase 2 closes Nov 30 15:59 UTC** (= 23:59 UTC+8), not 23:59 UTC.
   - The daily-limit reset stays at 00:00 UTC (08:00 Beijing, 16:00/17:00 US-Pacific).
   - Confidence: medium.
7. **Throughput risk: compute workers run one job at a time, and a timeout only fails the submission.**
   - Each compute worker processes **one job at a time** (`worker_concurrency = 1`, `$CB/compute_worker/celery_config.py:9`).
   - Every submission needs two jobs: a "prediction/ingestion" job, then a scoring job at priority 10 (`tasks.py:311`).
   - Scoring Habitat replay needs a GPU and Matterport3D scenes. The default public queue caps jobs at `MAX_EXECUTION_TIME_LIMIT` (600 s by default, `tasks.py:121-123,192-194`). So Track 2 almost certainly runs on an organizer-owned GPU worker on a custom queue, where `phase.execution_time_limit` applies uncapped (`tasks.py:283-302`). That worker can mount `$HOST_DIRECTORY/data` read-only at `/app/data` for MP3D (`compute_worker.py:1258-1267`).
   - A job that exceeds the limit is killed and marked **Failed**, which is free but wastes the turnaround (`compute_worker.py:1521-1556`).
   - Very long action sequences, such as 500-step look-around agents, raise the risk of a timeout if the limit was tuned on CMA-length sequences.
   - Expect queue congestion near the deadline.
   - Confidence: high on mechanics, medium on the setup inference.
8. **Moving from Phase 1 to Phase 2 resets the counters and is unlikely to carry anything over.**
   - Limits are per phase.
   - Phase 1 history stays under the Phase 1 tab.
   - Auto-migration happens only if `auto_migrate_to_this_phase=True` (default False). Even then it re-runs only finished leaderboard submissions with their old ZIP (`models.py:126-180`), and a val-only ZIP would be rejected for the missing `test` split.
   - Submission acceptance follows the exact `start < now < end` timestamps, not the hourly phase-status job (`models.py:359-365`, `serializers/submissions.py:208`).
   - The bundle unpacker attaches **the same leaderboard object (`leaderboards[0]`) to every phase** (`unpackers/base_unpacker.py:324`). Unless the organizers edited it afterwards, Phase 1 and Phase 2 share the same columns.
   - Confidence: high.
9. **Known v1.34 bugs that matter to us.**
   - (a) Force_Best orders the primary column with Postgres `DESC` and NULLS FIRST. A FINISHED submission with a missing primary score (N/A) would therefore be chosen as "best" and show N/A (`strategies.py:85`). This is fixed in develop (#2619), not in v1.34.
   - (b) Multi-task parent submissions are marked Finished even when every child failed (#2627, fixed in develop #2630).
   - (c) Duplicate score uploads have been summed in ranking (#1540, #2676).
   - (d) Status-update HTTP 500s leave submissions stuck. A stuck submission still counts, and under Force_Best it can keep a better score off the leaderboard (#2557).
   - (e) The execution limit is sometimes not enforced while the worker blocks on the scorer (#2586).
   - (f) Organizer bulk re-runs create new submissions under **our** account that count toward our daily and total limits in v1.34 (`models.py:631-667`, saved with `parent=None`). v1.35 exempts only the new "resubmit" action.
   - Confidence: high on the code, medium on what production actually runs.
10. **Realistic probe budget for Phase 2: 100 uploads, at most 5 per UTC day, which needs at least 20 distinct UTC days.**
    - The window spans 31–32 UTC days, so the 100 cap binds, not the daily cap.
    - With the outage risk and end-of-phase congestion, plan about 60–70 informative uploads and about 30 reserve.
    - Phase 1 has an independent 100/5 budget and is the best place to calibrate the official grader, because val ground truth is public.
    - Confidence: high on the arithmetic, medium on the plan.

---

## 1. Platform status (outage), verified 2026-10-24

| Item | Value | Source | Conf. |
|---|---|---|---|
| Unreachable since | ≥14:00 UTC Oct 21 (China report), ≥15:00 UTC (Vietnam), "still inaccessible as of 06:39 UTC Oct 22" | codalab/codabench#2679 comments | high |
| Cause | "all incoming HTTP(S) requests have been temporarily blocked" because of a PHP vulnerability. The host university blocks HTTP/HTTPS as a precaution. Codabench does not use PHP. | #2679, ObadaS and Didayolo (maintainers), Oct 22 | high |
| ETA | "we do not have any timeline to share" (Oct 23). On Oct 24 the only workaround offered was a leaderboard CSV by email to info@codabench.org. | #2679 | high |
| Server state | Ping answers, HTTP times out. Application reported as running fine. | #2679 | high |
| Other competitions' responses | Sophelio: alternate pointer website (HF commit plus manifest) and a +48 h extension to Oct 28 00:00 UTC, with quota shared across routes. Agenthon: deadline unchanged, no alternate channel ("can't be accepted"). NeurIPS AIMO organizers (3,000+ submissions, 50–100/day) are asking for alternatives. | Sophelio issue #13, Agenthon #44, #2679 | high |
| History | Planned maintenance Sep 15 00:01 to Sep 16 11:00 CEST (#2540). Upgrade downtime Mar 2026 (#2251, back the same day). Agenthon's own worker outage Oct 8 (#33). | issues | high |
| Roboworld response | No issue on roboworld2026/track2 (0 issues when fetched). The website repo's last commit (Oct 23) is unrelated (QR codes). | WebFetch of the issues page, `ext/roboworld2026.github.io` git log | medium |

**Implications:**
- (i) Phase 1 calibration may be impossible if the outage lasts past Oct 30.
- (ii) The Phase 2 bundle, if delivered as CodaBench `public_data` or `starting_kit`, is blocked.
- (iii) The organizers may extend Phase 1, shift Phase 2, or open an alternate channel. We must watch Discord, WeChat, email and the GitHub repos, and have pre-validated ZIPs ready to upload the moment the site returns.
- (iv) A long outage close to Nov 30 is the single largest platform risk. Do not leave the final candidate to the last days.

---

## 2. Phases and transitions (code-verified mechanics; Track 2 values inferred)

- **Acceptance window.** A submission is accepted only if `phase.start < now() < phase.end` at upload time (`$CB/src/apps/competitions/models.py:359-365`; checked in `SubmissionCreationSerializer.validate`, `$CB/src/apps/api/serializers/submissions.py:208`).
  - There is no grace period. Comparison is to the second, in UTC.
  - Phase "status" labels (Previous/Current/Next) are recomputed every 5 min (`do_phase_migrations`, `tasks.py:866-931`, beat 300 s at `settings/base.py:251-254`) and hourly (`update_phase_statuses`). Acceptance does not depend on these labels.
- **Scoring after the deadline.** A submission created before `end` is still processed and placed on the leaderboard after `end`: `upload_submission_scores` has no phase-active check (`views/submissions.py:623-655`). Organizers could still freeze results by hand.
- **Phases must be sequential with no overlap** (YAML docs, `$CB/documentation/docs/Organizers/Benchmark_Creation/Yaml-Structure.md:83`). Phase 1 end = Phase 2 start.
- **Migration.**
  - Applies only if Phase 2 has `auto_migrate_to_this_phase: True` (default False, `models.py:310`; v2 unpacker default False, `unpackers/v2.py:199`).
  - If enabled, only Phase 1 submissions that are FINISHED, on the leaderboard and not yet migrated are re-submitted into Phase 2 with their **old data ZIP**, with `ignore_submission_limit=True` (`models.py:152-176`).
  - Under Force_Best that means at most one per user.
  - A Phase 1 ZIP has no `test` split, so the validator would reject it. A rejection that exits non-zero becomes **Failed**, which does not count.
  - Probability that migration affects us: low.
- **Counters reset per phase.** Limits are counted over `self.submissions` of the phase (`models.py:347`). Phase 1 usage does not reduce Phase 2's 100.
- **Shared leaderboard object.**
  - The bundle unpacker sets `phase['leaderboard'] = leaderboards[0]` for **every** phase (`unpackers/base_unpacker.py:324`).
  - Unless the organizers re-configured it in the editor, both phases share one set of columns and one primary column.
  - Phase 1 "reports both splits; ranks by val_unseen Score" (README L71). So either Phase 2 reuses split-agnostic keys (e.g. `score`, `sr`, …) or there are extra test columns that stay N/A in Phase 1.
  - Inference, low-medium. Check the column names on the live site.
- **Phase boundary timestamps, unconfirmed.**
  - Track 2 README gives only dates: Phase 1 Oct 15–Oct 30, Phase 2 Oct 30–Nov 30 (`ext/track2/README.md:55-72`).
  - Sibling evidence: Track 1 says "Phase 1 closes / Phase 2 opens October 30, 2026, 23:59 UTC; Final … November 30, 2026, 23:59 UTC" (`ext/track1/README.md:70-72`).
  - Track 3 says "Phase boundaries on CodaBench follow UTC+8" (`ext/track3/README.md:62`).
  - The earlier Track 2 README (havln-challenge 8e36fa7 → 4a793d6, e.g. `git show 5ad4380:README.md` L56-57) said "Phase 1 opens September 30, 2026, 16:00 UTC | Phase 1 deadline October 31, 2026, 15:59 UTC", i.e. 00:00 and 23:59 UTC+8.
  - **Working assumption: Phase 2 closes no earlier than Nov 30 15:59 UTC**, so plan to that. Phase 2 may open Oct 30 15:59/16:00 UTC or Oct 30 23:59 UTC.
  - The Phases tab shows dates in the browser's local timezone (luxon `DATETIME_FULL`, `$CB/src/static/riot/competitions/detail/_tabs.tag:420`); the timeline widget uses UTC (`_timeline.tag:102`). Read the timezone label carefully.

## 3. Submission limits: exact semantics

Code: `Phase.can_user_make_submissions` (`$CB/src/apps/competitions/models.py:338-357`)

```python
qs = self.submissions.filter(owner=user, parent__isnull=True).exclude(status='Failed')
total_submission_count = qs.count()
daily_submission_count = qs.filter(created_when__date=now().date()).count()
```

| Question | Answer | Evidence | Conf. |
|---|---|---|---|
| Daily reset | 00:00 UTC (Django `TIME_ZONE='UTC'`, `USE_TZ=True`). UI tooltip: "resets at midnight server time". Docs: "from midnight UTC to midnight the next day UTC". | `settings/base.py:126-129`; `submission_limit.tag:7`; `Competition-Creation-Form.md:61` | high |
| Which day a submission is charged to | The UTC date of **upload/creation** (`created_when`), not of completion | `models.py:349,491` | high |
| Unit | **Per user account** (`owner=user`). Organizations do not pool or limit quota. Each member submitting "for an organization" would get their own 5/100 and their own Force_Best leaderboard row. | `models.py:347`; `views/submissions.py:169-178`; `strategies.py:75` | high |
| Failed submissions | **Do not count** (`exclude(status='Failed')`). This includes validator rejections that exit non-zero, timeouts, Docker pull failures, organizer-side worker failures, and runs older than 24 h auto-failed by `submission_status_cleanup`. | `models.py:347`; `compute_worker.py:1521-1556, 366-400`; `tasks.py:989-1000` | high |
| Cancelled | **Count** | same filter | high |
| Stuck `Submitting`/`Submitted`/`Preparing`/`Running`/`Scoring` | **Count** while stuck. Only `Running` older than 24 h + limit is auto-failed. `Submitted` and `Submitting` are not cleaned. | `tasks.py:989-1000`; #2557/#2651 | high |
| Soft-deleted by participant | **Still count** (no `is_soft_deleted` filter). They are excluded from Force_Best selection. | `models.py:347`; `strategies.py:89` | high |
| A finished submission that scored but whose ZIP was "rejected" | Counts if the scorer exits 0, which depends on the organizer scorer. **Test this in Phase 1.** | n/a | low |
| Organizer re-runs (single or "re-run all") | v1.34: a new top-level submission under our account, saved with `ignore_submission_limit=True` but **counted afterwards** toward our total and that day's quota. v1.35 adds `resubmit` (exempt) but `re_run` is still counted. | `models.py:631-667`; `$CBD` diff `models.py:347` | high (code) |
| Check remaining quota | `GET /api/can_make_submission/<phase_id>/` → `{"can":…, "reason":…}`. The phase serializer exposes `used_submissions_per_day` and `used_submissions_per_person` (shown as badges in the My Submissions tab). | `api/urls.py:45`; `views/submissions.py:657-675`; `serializers/competitions.py:176-202` | high |
| Approval needed | Only **approved** participants can submit (`CompetitionParticipant.APPROVED`). `registration_auto_approve` defaults to False, so an organizer may have to approve us manually. | `serializers/submissions.py:199-206`; `models.py:45`; `unpackers/v2.py:14` | high |
| Storage quota | 15 GB per user by default. Submission ZIPs count. A Phase 2 ZIP is a few MB, so this is negligible. | `settings/base.py:524`; `views/datasets.py:117-122` | high |

## 4. Leaderboard mechanics

- **Submission rules.** Values (`$CB/src/apps/leaderboards/models.py:7-22`): `Add` (model default), `Add_And_Delete`, `Add_And_Delete_Multiple`, `Force_Last`, `Force_Latest_Multiple`, `Force_Best`.
  - "Best score is retained" (README L53) matches `Force_Best`. Track 1 ("retains the team's best-scoring submission") and Track 3 ("keeps the best Score") use the same wording.
- **How `Force_Best` works** (`strategies.py:69-102`), run on every score upload (`views/submissions.py:653`):
  1. Clear the leaderboard pointer of all this owner's submissions in the phase.
  2. Pick among `status=FINISHED, is_soft_deleted=False` submissions, ordered by the primary column (desc for Score), then all other columns by index, then `created_when` ascending.
  3. Put the winner on the leaderboard.
  - Participants **cannot** override this: POST/DELETE to `submission_leaderboard_connection` is refused for auto rules unless superuser (`views/submissions.py:302-303`).
  - A FINISHED leaderboard submission cannot be deleted by its owner (`views/submissions.py:196-197, 237-238`).
- **If the rule is manual (`Add` / `Add_And_Delete*`).** Score uploads do nothing (`ManualModeStrategy`). The participant must click to add a submission, and with `Add` it can be replaced but never removed (`views/submissions.py:304-321`).
  - **Risk:** if the organizers forgot to set the rule, an un-pushed best submission never appears on the leaderboard. Confirm on the live site with the first Phase 1/2 upload.
- **Ranking order** (`serializers/leaderboards.py:181-222`; docs `Leaderboard-Functionality.md:58-71`):
  - Primary column, then the remaining *non-hidden* columns left to right (NULLS LAST for secondary columns), then `created_when`, so earlier wins.
  - The README tie-break "higher SR, lower NE, lower CR, lower TCR, then earlier submission time" (L211-213) implies the column order **Score(primary), SR(desc), NE(asc), CR(asc), TCR(asc)**. Inference, medium.
- **Precision.**
  - Storage: Decimal with 10 dp (`models.py:82`).
  - Display: the public leaderboard API rounds on the server to `column.precision` (`views/competitions.py:929-946`). The editor allows 1–10 (`editor/_leaderboard.tag:186`).
  - The README shows the baseline Score to 6 decimals ("16.509450") and components "rounded for display", which suggests Score precision 6 and components 3. Inference, low-medium.
  - Ranking compares the stored 10-dp values, consistent with "Calculation and comparison retain full precision".
  - Our own submissions return raw 10-dp strings via `/api/submissions/` (DRF Decimal → string). The UI rounds with `toFixed(precision)` (`submission_manager.tag:829`).
- **Hidden columns** (`column.hidden`) are dropped from both the participant's own score list (`serializers/submissions.py:79-81`) and the public leaderboard (`views/competitions.py:945`). Organizers can hide components if they want to limit feedback.
- **Visibility.** `get_leaderboard` is `AllowAny` (`views/competitions.py:802`), so competitors' rows are publicly readable at display precision. The leaderboard CSV download is organizer-only (docs `Leaderboard-Functionality.md:89-91`).
- **Known v1.34 ordering bugs.**
  - Primary-column ordering uses `-primary_col`, which in Postgres puts NULLs (N/A) first. That affects both the public order (#2618) and **Force_Best selection (#2619)**.
  - Duplicate score rows were summed in ranking (#1540 root cause; #2676 open).
  - Develop (v1.35) fixes the NULL ordering (`$CBD/src/apps/leaderboards/strategies.py` `_null_last_order`).
  - **Operational consequence:** if one of our submissions ever shows status Finished with N/A scores, ask the organizers immediately to delete or fail it, because it can capture our Force_Best slot.

## 5. Execution pipeline, queues, timeouts and failure modes

- **Two jobs per submission.**
  1. "Prediction/ingestion" job, priority 0: copies the result files.
  2. On status `Scoring`, the scoring job, **priority 10** (`tasks.py:309-331`; `serializers/submissions.py:252-258`).
- **Queue choice.** Group queue > competition queue > default queue (`docs/.../Participant-Routing.md:65`).
  - On the **default public queue** the job limit is `min(MAX_EXECUTION_TIME_LIMIT, phase.execution_time_limit)`, with `MAX_EXECUTION_TIME_LIMIT` = 600 s by default (`tasks.py:121-123,192-194`).
  - On a **custom queue** the phase limit applies uncapped (`tasks.py:283-302`). The phase default is 600 s (`models.py:309`).
  - The production value of `MAX_EXECUTION_TIME_LIMIT` is printed into every page's HTML (`templates/base.html:245`). Read it when the site is back. C1 cites 20 min; I could not verify that.
- **Inference (medium-high): Track 2 uses an organizer GPU worker.**
  - The toolkit describes GPU replay with `--gpu-ids` and needs licensed MP3D scenes, which cannot be redistributed.
  - The image carries a CodaBench layout: `/opt/havln-challenge/codabench/phase1/reference/public_reference_manifest.json` (`ext/track2/scripts/export_cma_submission.py:189`).
  - A private worker can expose host data read-only at `/app/data` (`compute_worker.py:1258-1267`; docs `Compute-Worker-Management---Setup.md:214`).
  - The default queue's 10-minute CPU jobs could not replay 2,617–3,408 Habitat episodes.
- **One job per worker** (`worker_concurrency = 1`, `celery_config.py:9`). Queue delay ≈ jobs ahead × scoring time ÷ number of workers.
  - Example: 40 active teams × 2 uploads/day × 45 min scoring ÷ 2 workers ≈ 30 h of backlog per day, i.e. an unbounded queue.
  - Expect congestion in the final week. That is when everyone submits 5 a day.
- **Timeouts.**
  - A SIGALRM at `execution_time_limit` kills the containers and fails the submission with "Execution Time Limit exceeded. Limit was N seconds" (`compute_worker.py:1521-1556`).
  - The Celery soft limit is the phase limit + 20 min (`tasks.py:281-283`).
  - A run stuck in `Running` for more than 24 h is auto-failed hourly (`tasks.py:989-1000`).
  - All of these are **Failed**, so they do not count toward quota, but the turnaround is lost.
  - #2586 (open, P1): sometimes the limit is not enforced while the worker blocks on the scorer container.
- **Our action lengths drive scoring time.**
  - Worst case 3,408 × 500 = 1.704 M simulator steps, against roughly 0.2–0.5 M for CMA-like lengths (inference).
  - If the organizers tuned `execution_time_limit` on CMA-length Phase 1 runs, a 500-step look-around submission could time out.
  - **Measure this in Phase 1** by submitting a val ZIP with long sequences and recording the time to Finished. Also ask the organizers for the limit.
- **Human timing is non-deterministic in official scoring.**
  - The older README says: "Humans move in real time, so repeat runs can differ" (`git show 5ad4380:README.md` L314-316).
  - The clarification branch says: "there is no single fixed wall-clock duration for each action … All official submissions are replayed in the standardized organizer-controlled CodaBench environment" (`ext/jostar-track2`, branch `bohan/clarification-Oct14`).
  - So identical ZIPs can score differently. Under Force_Best, resubmitting the same file gives the max of noisy draws (see §8 on ethics and magnitude).
- **Other failure modes in v1.34.**
  - Status PATCH returns HTTP 500 and the submission stays stuck in Submitted/Running. It counts toward quota, and a scored but stale-status submission was kept off the Force_Best leaderboard (#2557).
  - Frontend upload stuck in "Submitting" (#2651): counts.
  - Worker misconfiguration on the organizer side: "evaluation worker is not correctly configured" (Agenthon #33). Failed, free.
  - Fixes in develop/v1.35: retry with backoff on status updates (#2567), parent-status fix (#2630), N/A ordering (#2618/#2619).

## 6. What a participant can see and do (owner view)

Submission detail modal (`$CB/src/static/riot/competitions/detail/submission_modal.tag:3-70`; API `GET /api/submissions/<id>/get_details/`, `views/submissions.py:515-532`):

| Item | Visible to owner unless… | Source |
|---|---|---|
| LOGS: 8 tabs (prediction stdout/stderr, ingestion stdout/stderr, **scoring stdout/stderr**, scoring-ingestion stdout/stderr) | `phase.hide_output` (default False). Live streaming through the websocket also honours `hide_output` (`competitions/consumers.py:46`). The worker can disable log upload entirely (`COMPUTE_WORKER_DISABLE_LOG_UPLOAD`). | `serializers/submissions.py:304-307`; `compute_worker.py:124,1612-1620` |
| "Output from prediction step" ZIP | `hide_output` or `hide_prediction_output` | `serializers/submissions.py:312-316` |
| **"Output from scoring step" ZIP**: the whole scorer `/app/output` (scores.json, any extra files, `metadata` with exit codes and elapsed times) | `hide_output` or `hide_score_output` | `serializers/submissions.py:324-329`; `compute_worker.py:1776-1810` |
| Detailed results (`detailed_results.html`, VISUALIZATION tab) | Only if `enable_detailed_results` (default False). In v1.34, if enabled and the competition is published, `get_detail_result` serves it for any submission id (v1.35 tightens this). | `models.py:50`; `views/submissions.py:534-575` |
| Scores of **all** own submissions (not only the leaderboard one), 10 dp, non-hidden columns | always | `serializers/submissions.py:79-81` |
| Status / status_details (failure reason) | always | `serializers/submissions.py:37-60` |
| Elapsed time | `metadata` file inside the scoring ZIP (`elapsedTime`, `ingestionElapsedTime`) | `compute_worker.py:1778-1786` |
| Make submission public | Allowed by default (`can_participants_make_submissions_public=True`). **Never do this:** it makes our ZIP (all predicted trajectories) downloadable. | `models.py:78`; `views/submissions.py:581-590` |
| Programmatic access | Token auth is enabled: `POST /api/api-token-auth/` (username/password → token). Then `GET /api/submissions/?phase=<id>`, `GET /api/phases/<id>/get_leaderboard/`, `GET /api/can_make_submission/<phase_id>/`. | `settings/base.py:308-312`; `api/urls.py:45,50` |

## 7. Competition 18135 page: what is known

- **Not retrievable.** codabench.org is down, and a WebSearch for "codabench.org competitions 18135 HA-VLN" returned no indexed copy (2026-10-24). After that the search budget was used up.
- From the toolkit: README link text "CodaBench — HA-VLN"; "Participation is governed by the Terms displayed on the official CodaBench competition" (`ext/track2/README.md:52,321`). Site index button "Evaluation Server 2" (`ext/roboworld2026.github.io/index.html:1770`).
- **Generic page structure** (docs `Competition-Detail-Page.md`):
  - Tabs: Get Started (organizer pages plus **Terms**), Phases (dates; `public_data` and starting-kit download links), My Submissions (upload, quota badges, submissions table), Results (leaderboard), and Forum if enabled.
  - Registration is through My Submissions: accept the terms, then possibly wait for organizer approval.
  - An optional "fact sheet" may require per-submission answers (`serializers/submissions.py:170-186`).

## 8. Information content of one probe, and the ethics boundary

If Phase 2 leaderboard columns include SR, NE, CR and TCR (the README lists all four), the 10-dp API values of our own submission give these exactly:

- number of successes = SR·3408 (resolution 1/3408 = 2.93e-4 ≫ 1e-10);
- Σ final distances = NE·3408, to ±3.4e-7 m;
- number of collision episodes = CR·2859 (β·L = 3408 − 549);
- total adjusted collisions = TCR·3408.

That is roughly 4 independent aggregate statistics per upload, and the public leaderboard shows the same data for competitors at display precision.

**Sensitivity of Score.**
- dScore/dSR = 80·(0.7 + 0.3·Social). With zero collisions, one extra success on test = +80/3408 ≈ **+0.0235** points.
- One metre less final distance on one episode at mean NE≈2 m changes the Score by about 20·3/25/3408 ≈ **+7.0e-4**.
- Rankings are therefore resolved at the single-episode level.

**Ethics and rules (strong recommendation).**
- Differential probing works: change one episode's endpoint between uploads and read off the exact change in its distance. So does group-testing encoding of many episodes per upload. Either one turns the leaderboard into a test-label oracle (goal trilateration).
- That is test-label extraction, contrary to the spirit of a held-out test ("reference trajectories … remain withheld"). It would be obvious in our 100-upload history, which the organizers can see, and in the code and technical report that winners must provide.
- It would put both the award and the RoboPAD oral at risk. **Do not do it.** C4 should treat these numbers as a defensive and integrity analysis only.
- Likewise:
  - **one CodaBench account per team** for submitting. Multiple accounts would multiply quota and leaderboard rows, which almost certainly breaks the Terms. Confirm the Terms.
  - **if per-episode test diagnostics appear in Phase 2 logs or the scoring ZIP**, report them to the organizers and do not use them.
- Re-submitting an identical file to collect favourable human-timing noise is technically allowed under Force_Best, but it is low value and looks bad. Keep it to a reserve tie-breaker at most, if at all. For a zero-collision planner with clearance, the noise should be about 0.

**Legitimate use.**
- Model selection among genuinely different method variants, with the multiple-comparison caveat. Note that under Force_Best the max over our uploads *is* the final ranking.
- Using Phase 1, where val ground truth is public, to calibrate the official grader: its speed, the human frames it uses, collision accounting, STOP/500-step handling, time limits, and what is exposed.

## 9. Submission-ops playbook

### 9.1 Before the site returns (now → reconnection)
1. Pick **one submitter account** (the team's CodaBench username or display name must match the Google-Form team registration). Record the credentials in the team vault. Get an API token once the site is up (`/api/api-token-auth/`).
2. Pre-build and **locally validate** (`havln-validate`) and locally replay every ZIP we may upload. The Phase 1 calibration set is listed in 9.2. Store sha256 and local metrics. A Failed submission is free, but every upload costs turnaround.
3. Monitoring: subscribe to codalab/codabench#2679. Poll `https://www.codabench.org/` hourly; a scheduled task is enough. Watch Discord, WeChat, roboworld2026/track2, JostarXiong/track2 (including branches), and the HF dataset `fly1113/HA-VLN` for the test bundle.
4. Email roboworld2026@gmail.com, one consolidated message, reusing C2's question list. Ask for:
   - (a) exact Phase 1/2 timestamps and timezone;
   - (b) whether Phase 1 will be extended because of the outage;
   - (c) an alternate channel for the Phase 2 bundle and submissions;
   - (d) `submission_rule`, column list and precision, and `hide_output`/`hide_score_output` for Phase 2;
   - (e) `execution_time_limit` and grader hardware/throughput;
   - (f) one-account-per-team policy;
   - (g) whether FINISHED-but-rejected uploads count.

### 9.2 Phase 1 remainder (if the site is back before Phase 1 ends): calibration, not ranking
Budget: 5 per UTC day, 100 total. Phase 1 has no ranking value. Use every slot to learn the grader.

| # | Upload (val_seen + val_unseen) | What it tells us |
|---|---|---|
| P1-a | Official CMA export (README reference) | Parity: official vs README (16.509450 / 12.945387) and vs our local replay. Turnaround time. What appears in logs and the scoring ZIP. Column names and precision. Whether the entry appears on the leaderboard automatically (Force_Best vs manual). |
| P1-b | STOP-only (every episode `["STOP"]`) | Exact predictable NE = mean Euclidean start→goal distance. SR=0. Checks the NE definition and metric plumbing (C2's anchor). |
| P1-c | Our best planner on val (zero-collision gate) | Official CR/TCR vs local. Collision-episode counts are exact (TCR·L). |
| P1-d | Same as P1-c resubmitted unchanged | Run-to-run noise of the official grader (human timing). |
| P1-e | Long sequences (e.g. look-around agents near 500 actions) | Scoring duration ⇒ timeout margin, and the grader's steps/s (from `metadata.elapsedTime`). |
| P1-f | Deliberately malformed ZIP (e.g. one duplicated episode id) | Does a `SUBMISSION REJECTED` run end as Failed (free) or Finished (counted)? What does the error look like? |
| P1-g | Timing probes: agents that approach moving humans at controlled step counts | Which human frames the official grader uses (grader speed S), feeding C1's FrameScheduler calibration. |

Record for every upload:
- submission id, created_when (UTC), time to `Scoring` and to `Finished`, all 10-dp scores (via the API), logs, scoring ZIP contents, sha256.

### 9.3 Phase 2 schedule (100 uploads, ≤5 per UTC day, hard end conservatively Nov 30 15:59 UTC)
- **D0, as soon as Phase 2 is open and the bundle is in hand.**
  - Verify the bundle with `havln-validate` for the `test` split.
  - Upload **one safe candidate**, our best collision-free model at that time. This gets an entry on the leaderboard, measures Phase 2 turnaround, and confirms Phase 2 visibility settings (logs and scoring ZIP).
- **Days 1–20, the main exploration window.**
  - 2–4 uploads per UTC day. Submit **just after 00:00 UTC**: the quota resets then, and it avoids end-of-day stacking. Keep one or two slots per day unused for reruns of infrastructure failures.
  - Only upload candidates that passed the local zero-collision gate and differ meaningfully from earlier uploads (per C6/C10 protocol).
- **Days 21–27, exploitation.**
  - Converge on the final candidate family.
  - By **Nov 27** the intended final candidate must be **Finished on CodaBench** (C2 gate G8).
- **Nov 28–29: buffer only.**
  - Reserve about 10 uploads for outage recovery, platform bugs (e.g. N/A-captured Force_Best slot), and late fixes.
- **Nov 30: emergencies only**, before 15:59 UTC unless 23:59 UTC is confirmed.
- **Quota arithmetic.** 31–32 UTC days in the window × 5 = 155–160 > 100, so the total cap binds.
  - Spending all 100 needs at least 20 active days.
  - An outage of k days in the middle of Phase 2 removes nothing from the total, provided at least 20 days remain. It does compress the schedule.
  - If an outage hits the last week, uploads that already Finished are safe on the leaderboard.

### 9.4 Per-upload checklist
1. Run `havln-validate`, compute sha256, check the local replay metrics (all four). Run the 4-mode zero-collision replay gate (C1/C7).
2. Give the ZIP filename the experiment id (the filename is shown in My Submissions), e.g. `p2_e037_goalens_r0.35.zip`.
3. Check `GET /api/can_make_submission/<phase>/` first. Never upload if there is any chance of an accidental double upload (cancelled uploads still count).
4. After upload, poll status with backoff. Log the timestamps. On `Failed`, read status_details and the logs. If the cause is on the organizer side, report the submission id ("report the submission identifier rather than changing valid predictions", README Q6). Failed uploads are free.
5. If stuck in `Submitted`/`Running` for more than 3× the median turnaround, contact the organizers. Do not cancel, because cancelled uploads count. Under Force_Best a stuck better submission may never be placed (#2557).
6. When Finished:
   - Pull the 10-dp scores.
   - Check that the leaderboard row is the intended best.
   - If any of our Finished uploads shows **N/A**, contact the organizers at once (v1.34 N/A-first bug).
7. Never toggle a submission public.

### 9.5 Interpreting official feedback
- Compare official vs local *per metric*. Convert to exact counts: successes = SR·L; collision episodes = CR·βL; collisions = TCR·L.
  - Success counts within the measured run-to-run noise (from P1-d) are a tie.
  - Any official collision count above local means the grader saw humans at frames we did not plan for. Increase clearance.
- NE·L − local Σd gives the aggregate distance gap. Do **not** try to attribute it per episode by differential uploads (§8).
- Choosing the max over many uploads biases our view of true quality upwards. Rank final candidates on local val metrics plus the official test score together, not on test alone.

## 10. Numbers

| Quantity | Value | Source |
|---|---|---|
| Daily limit / total per phase | 5 / 100 (also the CodaBench defaults) | `ext/track2/README.md:53`; `$CB/src/apps/competitions/models.py:317-318`; `unpackers/v2.py:197-198` |
| Daily reset | 00:00 UTC | `settings/base.py:126-129`; `Competition-Creation-Form.md:61` |
| Score storage precision | 10 decimal places (max 20 digits) | `leaderboards/models.py:82` |
| Column display precision | default 2, configurable 1–10 | `leaderboards/models.py:67`; `editor/_leaderboard.tag:186` |
| Default phase execution limit | 600 s | `models.py:309`; YAML docs L87 |
| Default-queue cap | `MAX_EXECUTION_TIME_LIMIT`, default 600 s (production value unverified) | `tasks.py:121-123` |
| Celery soft limit padding | +1,200 s | `tasks.py:281-283` |
| Stuck-Running auto-fail | > 24 h | `tasks.py:989-1000` |
| Phase migration / status job period | 300 s / 3,600 s | `settings/base.py:251-258` |
| Compute worker concurrency | 1 job per worker | `compute_worker/celery_config.py:9` |
| Scoring vs ingestion queue priority | 10 vs 0 | `tasks.py:311` |
| User storage quota | 15 GB | `settings/base.py:524` |
| Outage start | ~14:00–15:00 UTC Oct 21 2026; no ETA as of Oct 24 | codalab/codabench#2679 |
| Phase 2 UTC days | 31 (23:59 UTC boundaries) or 32 (UTC+8 boundaries) → 155–160 slots > 100 cap | derived |
| Minimum active days to spend 100 uploads | 20 | derived |
| Test SR resolution | 1/3408 = 2.934e-4 | derived |
| Test Σd resolution via NE | 3408 × 1e-10 = 3.4e-7 m | derived |
| CR denominator (test) | 3408 − 549 = 2859 | CONTEXT fact 3 |
| ΔScore for +1 test success (Social=1) | +0.0235 | derived from README formula |
| Worst-case replay length | 3,408 × 500 = 1,704,000 steps | derived |

## 11. Things to confirm on the live site (in this order)

1. Competition 18135: title, description, **Terms** (account/team policy, use of external data/APIs, prohibition of multiple accounts, probing).
2. Our registration status (approved or pending). Is `registration_auto_approve` off?
3. Phases tab: exact Phase 1 end and Phase 2 start/end timestamps, with the timezone label. Is Phase 1 extended? Any third phase?
4. Phase 2 bundle location (`public_data` / starting kit on CodaBench vs HF/GitHub). Contents: test episodes, test-scan human placements, `collision_num_test`, manifest.
5. Leaderboard: submission rule (does an upload appear automatically? does the UI offer an add/remove button?), column titles/keys, which column is primary, precision per column, hidden columns, whether Phase 1 and Phase 2 share columns.
6. My Submissions: quota badges ("x out of 5", "y out of 100"). After a test failed upload, check that the count did not increase.
7. Submission detail for our first upload: which log tabs are populated, what the scoring stdout prints (per-episode lines?), whether the "Output from scoring step" ZIP is downloadable and what it contains, `metadata.elapsedTime`, and whether detailed results/VISUALIZATION exist.
8. Platform: `MAX_EXECUTION_TIME_LIMIT` (page source of any page, `templates/base.html:245`), footer version (v1.34 vs v1.35), the platform-wide announcement banner, the server status page (queue of our submissions, worker hostname).
9. Forum tab: organizer announcements about the outage or extensions.
10. Fact sheet questions, if any (e.g. method description, open-weight vs API usage).

## 12. Contradictions and refinements vs CONTEXT and other agents

- CONTEXT fact 1 ("5 submissions/day, 100/phase, best retained") holds. Refinements:
  - Limits are **per user account**, not per team.
  - **Failed uploads are free**; cancelled, stuck and soft-deleted uploads are charged.
  - Organizer re-runs are charged in v1.34.
- C2 assumes 23:59 UTC boundaries (Track 1 analogy). The Track 2 toolkit's own earlier timeline used **UTC+8** boundaries (16:00/15:59 UTC), and Track 3 states UTC+8. Plan to Nov 30 15:59 UTC until confirmed.
- C1 cites a "public queue 20 min cap". In code the default is 600 s and the production value is unverified. It is irrelevant if the organizers use a private GPU queue, which is likely.
- The older toolkit README (Sep 28 – Oct 7) advertised a $2,800 prize pool ($1,500/$800/$500). The current README lists certificates only. FYI for C3/B8.

## 13. Open questions

- Production CodaBench version once restored (v1.34 or v1.35)? That decides whether the N/A Force_Best fix and the status-retry fix are present.
- The actual Track 2 `submission_rule`, columns, precision and hide flags for Phase 2.
- `execution_time_limit` and the number of organizer GPU workers. The typical Phase 2 turnaround.
- Does a validator rejection exit non-zero (Failed, free)?
- Will the outage lead to a Phase 1 extension, a Phase 2 shift, or an alternate submission route? If there is an alternate route, does it share quota (as Sophelio's did)?
- Do the Terms forbid multiple accounts per team and leaderboard probing explicitly? Are API or scripted uploads allowed?

## Sources

- CodaBench source, v1.34 master (cloned): `$CB/src/apps/competitions/models.py`, `$CB/src/apps/competitions/tasks.py`, `$CB/src/apps/leaderboards/{models,strategies}.py`, `$CB/src/apps/api/serializers/{submissions,leaderboards,competitions,submission_leaderboard}.py`, `$CB/src/apps/api/views/{submissions,competitions}.py`, `$CB/src/apps/competitions/consumers.py`, `$CB/src/apps/competitions/unpackers/{v2,base_unpacker}.py`, `$CB/compute_worker/{compute_worker,celery_config}.py`, `$CB/src/settings/base.py`, `$CB/src/static/riot/competitions/detail/{submission_limit,submission_modal,submission_manager,_tabs,_timeline}.tag`, `$CB/documentation/docs/...` (Yaml-Structure, Leaderboard-Functionality, Competition-Creation-Form, Compute-Worker-Management---Setup, Participant-Routing, Server-status-page).
- CodaBench develop (v1.35) diff: `git -C $CBD diff master develop`.
- https://github.com/codalab/codabench/issues/2679 (outage), /2557, /2586, /2627, /2676, /1540, /1840, /2251, /2540
- https://github.com/Sophelio/fusion-equilibrium-challenge-starter/issues/13 ; https://github.com/Agenthon-2026/track1-coding-public/issues/44 ; https://github.com/Agenthon-2026/track1-coding-public/issues/33
- https://github.com/roboworld2026/track2/issues (0 issues on 2026-10-24)
- `ext/track2/README.md` (L52-72, L184-188, L211-213, L274-286, L321); `ext/track1/README.md` (L64-75, L236-252); `ext/track3/README.md` (L52-62, L318); `ext/havln-challenge` git history (commits 8e36fa7, 5ad4380, 4a793d6); `ext/jostar-track2` branch `bohan/clarification-Oct14`; `ext/track2/scripts/export_cma_submission.py:189`; `ext/roboworld2026.github.io/{index,track2}.html`.
