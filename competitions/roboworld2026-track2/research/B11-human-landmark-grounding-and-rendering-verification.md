# B11: Human-landmark grounding and rendering verification

Author: research agent B11, 2026-10-24. Regime tags: **[C]** = compliant (egocentric RGB-D + GPS/compass at inference; no human_motion.json or other privileged human data at inference). **[P]** = privileged (annotations or simulator state, allowed only for training supervision, local evaluation and val diagnostics, per organizer FAQ Q11 on branch `bohan/clarification-Oct14`).
WebSearch worked for 6 queries. Every number below comes from local files parsed with Python (`json`). The scripts are in `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b11/` (stats1.py to stats11.py, matcher.py, vocab.py, attrs.py). The derived activity attribute table is `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/b11/activity_attributes.json`.

## 0. Bottom line (decision-relevant)
1. **The activity vocabulary is closed and public.** All 115 distinct activity strings used by the 749 public HA-VLN 2.0 humans are verbatim members of the 144-sentence HA-VLN 1.0 MDM prompt list (`HA-VLN_human_motion_prompts.txt`). Grounding text to an activity is therefore a 144-way classification, not open vocabulary. [C] (high)
2. **A zero-training lexical+GloVe matcher already works on the text side.** On HA-VLN 1.0 HA instructions with gold human labels (proxy), it maps the instruction to the gold activity at top-1 for 88–90% of human-bearing instructions, and at top-3 for 89–90% of gold mentions. At score ≥0.6 it fires on only 0.9–2.1% of no-human instructions. Restricting candidates to the scan's annotated humans [P] lifts top-1 to 96–97%. (medium: HA-R2R 2.0 texts are ~2x longer and more paraphrased)
3. **Humans are strong goal landmarks when one is near the goal.** In 44–47% of R2R-CE/HA-R2R episodes a same-floor human stands within 3 m of the goal. In HA 1.0, 'End'-tagged humans are 100% within 3 m of the goal (median 0.3–0.9 m). An oracle that stops at the first reference-path point within 1.0 m (1.5 m) of the human nearest the goal gets SR 92% (85–87%) on those episodes. This is an upper bound for an "end-mention" stopping rule. [P-measured, C-applicable] (high for the numbers, medium for transfer)
4. **The visual activity signal is weak; presence and region are strong.** Humans are untextured dark-grey neutral SMPL meshes with no props (demo figures; MDM pipeline, 3 samples per prompt). "Couple/friends/family" activities are usually a SINGLE body: 25 of 28 group-subject activities are mostly single instances. Zero-shot motion-to-text recognition on BABEL is only about 30–43% top-1 even from full 3D skeletons (TMR, WaMo). So the verification module should confirm **a person at roughly the expected place, in the expected room type**, and should treat activity-level visual matching as a weak tiebreaker. [C] (medium-high)
5. **Rendering verification is a training and diagnostic tool [P], not a matching necessity.** With annotations, the string match already identifies the human. Renders are still needed to produce visibility and instance-mask labels (habitat-sim 0.1.7 `set_object_semantic_id` + semantic sensor), to measure detector recall on SMPL renders (never measured anywhere public), and to audit annotation bugs. **In [C], the detector IS the grounding channel.**
6. **If Phase 2 withholds test-scan human placements**, a [C] agent running locally sees NO humans in test scans (environments.py uses `.get(scan, {})`). Neither visual grounding nor perceptual human avoidance is then possible locally. The only legitimate substitutes are text-derived priors: region and anchor-object zones for mentioned activities, used as soft cost and stop-placement constraints. The HA 1.0 test-scan anchors (`human_motion_text.json`, 70 humans) are quarantined [P-only]. Even if permitted, they would cover only ~47% of 2.0 humans within 3 m. Evidence suggests the organizers do hold 2.0 placements for test scans: the HA-VLN overview figure shows test scans ARNzJeq3xxb and RPmz2sHmrrY populated with many humans. FAQ Q11 also says human_motion.json "is provided to support simulator rendering", so shipping it is likely (medium).

## 1. Statistics of human_motion.json (HA-VLN 2.0 public, 72 scans)
File: `ext/HA-VLN/Data/Multi-Human-Annotations/human_motion.json`. Structure: scan → key → {category, index, translation[120][3], rotation[120][3]}. Exactly one human per key.

| Quantity | Value | Script |
|---|---|---|
| scans / humans | 72 / 749 (0 of the 18 test scans) | stats1/2 |
| humans per scan | min 6, median 10, mean 10.4, max 19. Histogram {6:1, 7:4, 8:14, 9:8, 10:20, 11:5, 12:5, 13:5, 14:4, 15:4, 16:1, 19:1} | stats1 |
| distinct category strings `<region>:<Activity>` | **331** | stats1 |
| distinct (category, index) = distinct GLB motion assets | **419** of 486 HAPS-2.0 dirs (67 assets unused in public scans) | stats1 |
| distinct activities (after the colon) | **115**, all inside the 144-sentence 1.0 prompt list (0 new) | stats5 |
| distinct region prefixes | 25 (MP3D region names with underscores: hallway 136, bedroom 71, living_room 65, other_room 57, kitchen 50, …) | stats1 |
| index (MDM repetition 0/1/2) | 0: 560, 1: 149, 2: 40 | stats1 |
| scans where ≥2 humans share a full category | 63/72. 250 humans (33.4%) share their category with another human in the same scan | stats1 |
| humans sharing an activity in-scan | 317 (42.3%). Unique by activity in scan: 57.7%. Unique by full category: 66.6% | stats1/5 |
| anchor groups with ≥1 scan-unique activity | 450/547 (82.3%) | stats5 |
| regions per activity | 48 activities appear in 1 region; the rest are reused across 2–16 regions (e.g. "Friends laughing and sharing stories over dinner" in tv, hallway, family_room, dining_room) | stats5 |
| most frequent activities | talking on the phone while pacing (78), couple quiet intimate conversation (53), friends laughing over dinner (53), taking photographs of the view (32), cleaning/vacuuming (29) | stats5 |
| group subject in text vs instances | 28 couple/group activities seen in public data, 25 of them mostly rendered as ONE body. 89 of 127 multi-human anchors mix DIFFERENT categories | attrs, stats2 |
| train (61 scans) vs val_unseen (11 scans) | 637 vs 112 humans. 7/112 val_unseen humans (6%) have an activity unseen in train scans (incl. "someone ironing clothes"). 43/112 (38%) use a GLB asset unseen in train | stats8 |
| HA-R2R-2.0 vocabulary check | Content-word coverage of the 115 used activities in the 5,079-word HA-R2R vocab = 99.4%. For the 29 unused activities it is 88.9%: 'brainstorming', 'woodworking', 'crafting', 'homework', 'scooters', 'muddy', 'backpack', 'manager', 'club' never occur in HA-R2R train text. These 29 are candidates for test-only (or unused) activities | vocab.py |
| HA 1.0 file | `human_motion_text.json`: 90 scans, 374 humans (70 in the 18 test scans, 2–7 per scan), value = [region:activity, MDM index, heading°] | stats2 |

Paper/README totals (HA-VLN Data/README.md L127-129): 910 humans, 428 regions, 72 pairs / 59 triples / 15 quads. Public: 749 humans, 66/47/14 groups. **Implied test-scan content ≈ 161 humans, ≈ 19 groups** (inference, medium).

## 2. Viewpoint ids: are they MP3D graph nodes? (task item 2)
- Keys are a 32-hex MP3D viewpoint id (419 keys) or that id plus one digit 1–4 (330 keys = members of a multi-human group anchored at that viewpoint). **747/749 base ids are image_ids in the same scan's connectivity file**, 745 of them `included: true`. The 2 exceptions are copy errors: ULsKaCPVFJR/84cc1504… belongs to Vvot9Ly1tCj and VVfe2KiqLaN/af73d4fc… belongs to X7HyMhZNoso. (high; stats2)
- Coordinate mapping verified: Habitat (x, y, z) = MP3D (x, z, −y), using the connectivity pose translation (pose[3], pose[7], pose[11]). Frame-0 human translation vs anchor viewpoint (horizontal): **35% < 0.5 m (many exactly 0), 46% < 1 m, 66% < 2 m, 79% < 3 m; median 1.06 m, p90 4.2 m, max 13.5 m.** The anchor is the nearest included viewpoint for only 336/749 (45%) humans. The distance to the nearest included node has median 0.44 m, p90 1.18 m. (high; stats2)
- Vertical: translation y (mesh origin ≈ pelvis) sits a median **0.72 m** above the floor of a reference-path node within 0.3 m (p10 0.62, p90 0.86). Relative to the MP3D camera height it is −0.68 m. (high; stats4) A9 reports 0.84 m against the anchor floor (a different reference), which is consistent.
- **The simulator never uses the key.** `HASimulator/environments.py` L182-213 uses only translation and rotation. Category plus index select the GLB template `category.replace(' ','_').replace('/','_') + '_' + index` (L189-192; dirs sorted, 120 frames each, L224-233). So tie humans to graph nodes and regions by **nearest node / region polygon from the translation**, and use the key only as a hint.
- Regions: the category prefix is an MP3D region name. A9 found ~95% agreement with MP3D region labels. To tie a human to a region polygon you need the MP3D `.house` file (MP3D licence).

## 3. How instructions refer to humans (generation process = the grounding target)
- HA-R2R 2.0 generation prompt (Data/README.md L77-94): the LLM (GPT-4o / Llama-3-8B) receives the R2R-CE instruction plus `[start]`, `[during]`, `[end]` fields, each a `"region: Activity."` string. The output must describe the human activities "at each stage of the navigation (beginning, during, and end)". **Each mention therefore carries an implicit stage label, and the end-stage human is by construction near the goal.** (high)
- Spatial evidence on 2.0 placements vs R2R-CE reference paths (stats4/6, same-floor test |Δfloor| < 1 m):
  - Episodes with a human within 0.5 / 1 / 2 / 3 m of the reference path: train 35/47/63/77%, val_seen 39/51/66/81%, val_unseen 36/50/68/79%. This cross-checks the paper's "35.5% of paths physically intersect human motion" (A10).
  - Path-near humans (<2 m) are concentrated at the path ends. Quintiles of path progress: train [23, 16, 16, 18, 27]%, val_unseen [27, 16, 17, 19, 22]%. This is consistent with start/during/end generation.
  - Goal has a same-floor human within 1.5 / 3 / 5 m: train 15.5/43.5/69.9%, val_seen 16.2/44.7/73.4%, val_unseen 14.4/46.8/64.6%. Nearest human to goal: median 3.1–3.5 m, p10 1.1–1.3 m.
  - Start has a human within 1.5 / 3 m: 15–19% / 39–45%. Start mentions are useful for initial-heading disambiguation.
  - Path-local ambiguity: among humans within 2 m of the path, the activity alone is unique for 79% (train) / 65% (val_unseen). Same-activity duplicates are co-located (<2 m) in a further 10% / 27%. **Only 8–10% are genuinely ambiguous (same activity ≥2 m apart).** (stats11)
- HA 1.0 proxy with explicit labels (`ext/HA3D_simulator/tasks/HA/data/HA_{split}.json`; field `human` = [{human_viewpoint, human_rel_pos, human_description}]) (stats3/7):
  - Paths with ≥1 human: train 75%, val_seen 79%, val_unseen 65%.
  - rel_pos mix (train): Around 4,072, Obstacle 1,004, End 283, Beginning 274.
  - 'End' humans: 100% within 3 m of the goal viewpoint (median 0.31 / 0.57 / 0.91 m).
  - 'Beginning' humans: 100% at the start node.
  - 'Obstacle' humans: on the path (median 0 m), 38–47% within 3 m of the goal.
  - 'Around' humans: median ~4 m off the path. They are mentioned but are not path landmarks.

## 4. Text side: matching algorithm and measured proxy accuracy
**M1 Mention extraction [C].** Split the instruction into sentences or clauses containing person words (person, someone, individual, couple, family, friends, group, child, people, he/she/they, …).
- Primary extractor: an open-weight LLM (e.g. Qwen2.5-7B-Instruct, per the organizers' preference). Constrained JSON output: {activity_id ∈ 144 | NONE, region word, stage ∈ {start, during, end}, spatial relation (left/right/pass/near object X/stop near), negation or generic flag}.
- Fallback and cross-check: the deterministic matcher `b11/matcher.py`.

**M2 Lexical+GloVe activity scorer (implemented, zero training).** For a clause c and a canonical activity a:
s(a, c) = Σ_{t∈content(a)} idf(t)·match(t, c) / Σ idf(t)
- match = 1 on a stem match, otherwise 0.7·(cos−0.75)/0.25 if the GloVe-50d cosine to the best clause token exceeds 0.75.
- idf is computed over the 144 activities.
- The score of a is the max over person-bearing clauses.
- GloVe vectors come from the public `Data/HA-R2R-tools/embeddings_glove_50d.json.gz`.

Measured on HA 1.0 val (instructions vs gold `human_description`):

| split | instr with humans | top-1 activity ∈ gold | any gold in top-3 | per-gold top-1 / top-3 | scan-restricted top-1 [P] |
|---|---|---|---|---|---|
| val_seen | 805 | 0.884 | 0.938 | 0.565 / 0.894 | 0.968 |
| val_unseen | 1,527 | 0.901 | 0.925 | 0.682 / 0.898 | 0.959 |

Calibration (val_unseen; val_seen similar):

| threshold | share of gold mentions scoring ≥ thr | share of top-5 non-gold scoring ≥ thr | share of no-human instructions whose max ≥ thr |
|---|---|---|---|
| 0.4 | 0.910 | 0.385 | 0.437 |
| 0.5 | 0.877 | 0.145 | 0.367 |
| **0.6** | **0.851** | **0.055** | **0.021** |

Top-3 recall by rel_pos: Obstacle 0.91–0.93, End 0.87–0.94, Beginning 0.87–0.91, Around 0.89.
Confidence: medium. HA-R2R 2.0 instructions average ~112 words vs ~50 here and paraphrase more ("a person actively searching for a lost item, perhaps checking under the bed"). Expect the lexical scorer to lose some points and an LLM extractor to recover them. Validate on HA-R2R 2.0 train instructions using the [P] labels from M4 (training data, allowed).

**M3 Confidence.** p_k(a) = softmax(s(a, c_k)/τ) with τ ≈ 0.05, fit on train. The mention is accepted if max s ≥ 0.6, or if the LLM and the lexical top-3 agree. A mention is flagged generic ("be careful of any human activity", "others around you") if no activity scores ≥ 0.4. The 1.0 no-human example in the README is of this type.

**M4 [P] Training-label generation (mention → human instance).** This uses the train split only; val is for diagnostics only.
- Candidates = the scan's humans from human_motion.json (mean 10.4).
- Score = s(a_h, c_k) + α·log P(stage | progress of the human's projection on the reference path) + β·log P(dist to path). Stage prior from §3: start = first 20%, end = last 20% or within 3 m of the goal.
- Hungarian assignment; group members sharing an anchor are merged into one candidate.
- Expected label accuracy ≥ 95%: 1.0 proxy scan-restricted top-1 96–97%; only 8–10% residual spatial ambiguity, which the path prior removes.
- Outputs: (i) per-instruction mention→human position labels; (ii) per-frame "mention k visible" labels via the semantic sensor (§6); (iii) goal-offset statistics.

## 5. Perception side [C]: what can be seen
- Sensor: one forward RGB 224×224, HFOV 90 (focal ≈ 112 px), and depth 256×256 (`HASimulator/config/HAVLNCE_task.yaml`). A 1.7 m standing body spans ≈ 190/d px: **95 px at 2 m, 63 px at 3 m, 38 px at 5 m, 24 px at 8 m, 16 px at 12 m.** Detection is plausible out to ~8 m. Activity-level detail is plausible only within ~3 m. Panoramas cost 24 TURN actions (15° each) out of the 500 budget.
- Appearance: untextured dark-grey SMPL meshes, no props or clothing (viewed `ext/HA-VLN/demo/figs/overview_example-1.png`, `demo/gifs/nav1.gif`). The bodies come from MDM `humanml_trans_enc_512` with 3 repetitions per prompt (`human_motion_model/README.md`, `skeleton2smpl.py` MODEL_NUM=3). They therefore have the default (adult, neutral) body shape, so "child" mentions are not visually distinguishable (inference, medium).
- Recommended detector stack:
  1. YOLO-seg (COCO person) or GroundingDINO "person." as the off-the-shelf baseline. HA-VLN's own `human_counting` uses GroundingDINO SwinT-OGC with box 0.35 / text 0.25 (`HASimulator/detector.py` L91-178); it is off by default.
  2. Fine-tune on [P] instance masks from the 61 train scans.
  3. Depth median inside the mask + GPS/compass → 3D position, fused into a human layer of the occupancy map. The same layer serves collision avoidance.
- Attributes worth estimating per detected human:
  - presence, 3D position and count at a location (strong);
  - room type of the surrounding space (strong; A9 shows region labels align ~95% with activity prefixes);
  - coarse posture (standing / sitting / lying from mask aspect ratio and pelvis height above the depth-floor; medium);
  - activity (weak; a CLIP/VLM or crop classifier fine-tuned on HAPS renders over the 144 classes; expected low accuracy given the TMR/WaMo zero-shot BABEL 30–43% top-1 from full skeletons);
  - motion (weak: 93% of humans move ≤1 m and all freeze after ~12 s of wall time).

## 6. Rendering-based verification: needed? (task item 3)
- **[P] With exact annotations, it is not needed for matching.** The string match plus stage/path prior resolves the human (≥95%). Use rendering for:
  - **Visibility/instance labels.** Hook `sim.add_object_by_handle` and call `sim.set_object_semantic_id(BASE+oid, oid)` on every (re)insert; add a SEMANTIC_SENSOR. This gives pixel-exact human masks aligned with RGB. The binding exists in habitat-sim 0.1.7 (`src/esp/bindings/SimBindings.cpp` L281, `Simulator.cpp` L607-612; requires physics, which HA-VLN needs anyway for add_object_by_handle). A competitor implements exactly this (`ext/competitor-bingchengzhang/project/scripts/seg_gt_smoke.py`, HUMAN_BASE = 1,000,000). Humans are removed and re-added every 0.1 s during the first ~12 s, so the hook must re-tag on each add.
  - **Detector-recall measurement on SMPL renders.** No public number exists; the competitor notes it has never been measured, and my WebSearch found nothing.
  - **Annotation audits:** the 2 wrong-scan keys; humans clipping furniture; humans on other floors or stairs.
  - **Occlusion-aware "mention visible from pose" labels**, to train the [C] matcher and progress monitor. `sim.cast_ray` is also available (Bullet) for cheap line-of-sight checks.
- **[C] At inference, "rendering" is the agent's own observation stream.** Verification = detector + 3D localization + region/posture consistency checks before accepting a mention match or committing to STOP.
- **[P] Val diagnostics:** compare the [C] agent's predicted mention↔human assignments and STOP positions with M4 labels on val_seen/val_unseen. This is evaluation only, never training.

## 7. Assignment, confidence, and candidate-goal scoring [C]
1. Track human clusters o_j (merge detections within 1 m across frames), each with position x_j, first-seen path progress τ_j, room label ρ_j, posture π_j and activity likelihood q_j(a).
2. Mention–human compatibility:
   S(k, j) = log Σ_a p_k(a)·q_j(a)^γ + λ_r·log P(ρ_j | region_k) + λ_π·log P(π_j | a) + λ_σ·log P(τ_j | stage_k)
   - Use a small γ (≈0.3) because q is weak.
   - Region and stage carry most of the weight.
3. Monotone alignment: DP over mention order vs time-of-first-sighting, with a null option (mentions of unseen or "Around" humans; penalty fit on train). Confidence c_k = posterior of the best j vs null and the alternatives.
4. Goal scoring for a candidate stop point g (from a waypoint predictor or frontier set):
   score(g) = base_nav(g) + Σ_{k: stage=end} c_k·[log N(‖g−x_{j(k)}‖; μ≈1.0 m, σ≈0.7) − ∞·1(‖g−x_{j(k)}‖ < 0.6 m)]
   - The second term excludes collision-prone stops.
   - Start mentions disambiguate the initial heading and room.
   - During mentions act as progress checkpoints: once matched and passed, progress ≥ the mention's ordinal fraction.
   - When c_k < 0.5, fall back to object/room landmarks in the same sentence ("in the laundry room", "near the bed").
5. Expected value, measured oracle bound [P] (stats10). For the 43.5–46.8% of episodes whose goal has a same-floor human within 3 m, stopping at the first reference-path point within R of that human gives:

| R | median dist-to-goal | SR (< 3 m) |
|---|---|---|
| 1.0 m | 0.32–0.83 m | 0.922–0.923 |
| 1.5 m | 0.82–1.21 m | 0.853–0.871 |
| 2.0 m | 1.17–1.71 m | 0.78–0.80 |

   So a correctly grounded end-human gives a near-certain success zone. The real gain is bounded by: (fraction of episodes with an end mention) × (detection + matching accuracy) × (cases where the base policy would otherwise fail).

## 8. Fallback when the Phase 2 bundle withholds test-scan humans
- **Effect [C].** `environments.py` L175 uses `human_motion_data.get(scan, {})`, so local test episodes run human-free (A1). The agent cannot see the humans it is told about, and cannot perceive and avoid the bodies that will be present in the official replay (35–39% of episodes have a human within 0.5 m of the reference path).
- **Legitimate mitigations [C].**
  - (a) Text priors. Parse mentions as in M1. Convert activity → expected region and anchor objects (activity_attributes.json plus PSO placement rules: humans placed in the activity's region, near semantically matched objects, ≥1 m from other objects; Data/README.md L100-108).
  - (b) Learn P(human location | egocentric semantic map, activity) from the 61 train scans ([P] supervision, allowed). At inference, add an "expected-human" soft-cost layer and stop-placement rule: stop ≥1.0–1.5 m from the predicted end-human zone, inside the 3 m success radius.
  - (c) Plan through mentioned-human rooms with extra clearance.
  - This is weaker than perception. All teams would face the same handicap.
- **Not legitimate without explicit permission [P-only].** Reading HA 1.0 test-scan annotations (`human_motion_text.json`, 70 test humans). On public scans: 83.6% of 1.0 anchors persist as 2.0 anchors; 68.1% keep the same activity at the anchor; 65.5% have a same-activity 2.0 human within 3 m. Only 47.3% of 2.0 humans lie within 3 m of any 1.0 human viewpoint (the 2.0/1.0 human ratio is 2.46). So even with permission, this prior misses about half of the test humans.
- **"Rendering with nothing":** without test human placements, rendering can verify only scene and room content (MP3D test scans are available), not humans. Synthesizing humans into the local sim from instruction text would turn a prior into fake observations. Do not do it without organizer approval.
- **Action:** ask the organizers now whether the Phase 2 bundle includes test-scan human_motion.json. FAQ Q11 wording and the populated test-scan demo figure suggest yes.

## 9. Literature (task item 4)
- HA-VLN 2.0 (arXiv 2503.14229): `human_counting` API via GroundingDINO (code above). HA-R2R 16,844 instructions. HAPS 2.0: 486 SMPL motions, "172 activities" per the README. That contradicts the 144-sentence public prompt file, which covers all 115 activities used publicly; 28 activities may be 2.0-only, reserved for test, or a counting difference. Open.
- HA-VLN 1.0 (NeurIPS 2024 D&B, arXiv 2406.19236): HA3D, VLN-CM/VLN-DT. No dedicated human-detection module was found (search summary, low-medium).
- SURREACT (Varol et al., IJCV 2021, arXiv 1912.04070): textured synthetic SMPL humans improve action recognition from unseen viewpoints (NTU 53.6→69.0%). HA-VLN bodies are untextured, so the gap for appearance-based activity recognition is larger.
- BEDLAM (CVPR 2023): realistic synthetic humans; criticises SURREAL-style crude textures.
- TMR (ICCV 2023, arXiv 2305.00976) and the cross-dataset study (CVPRW 2024, arXiv 2405.16909): zero-shot motion→text recognition on BABEL ≈ 30–32% top-1; WaMo (arXiv 2508.03343) ≈ 43%. Fine-grained activity recognition is weak even from 3D motion.
- No public measurement exists of off-the-shelf person detectors on untextured SMPL renders in Habitat (search, Oct 24). Measure it with [P] masks.

## 10. Recommendations
1. [C] Build the text module first: an LLM constrained extractor plus `b11/matcher.py` as fallback, over the closed 144-activity vocabulary. Calibrate the accept threshold at 0.6 on HA-R2R 2.0 **train** labels generated by M4.
2. [P→C] Generate M4 mention↔human labels for all 10,819 train instructions. Use them to train (a) a stage classifier, (b) an end-human→goal offset model, and (c) a progress monitor.
3. [P→C] Instrument the sim with the semantic-ID hook. Measure YOLO-seg / GroundingDINO recall vs distance on train-scan renders, then fine-tune. Target ≥95% recall at ≤6 m, which is needed for both grounding and collision avoidance.
4. [C] Weight region/presence/stage cues over visual activity. Keep the visual activity likelihood as a γ≈0.3 tiebreaker. Do not use the text's group size as a hard constraint.
5. [C] Goal scoring: add the end-human term (μ≈1.0 m, hard exclusion < 0.6 m) only when c_k ≥ 0.5. Otherwise fall back to object/room landmarks.
6. [P] On val, report the mention-grounding accuracy and the "end-human stop" success separately. This attributes gains and is good material for the "innovative solution" write-up.
7. Ask the organizers whether test-scan human_motion.json ships in Phase 2. Prepare the text-prior fallback (§8) in case it does not.

## 11. Corrections and contradictions flagged for other agents
- A9 says "331 of the 486 HAPS-2.0 categories appear in the public 72 scans; the other 155 can only appear in test scans". In fact the 486 HAPS dirs are (category, index) assets: 419 are used publicly, so only **67 assets** are unused. 331 is the count of category strings.
- 2 of 749 human_motion.json keys are viewpoints of other scans. Use translations, not keys.
- "A couple/friends/family" text ≠ multiple bodies. 25/28 such activities are mostly one body, and 70% (89/127) of multi-human anchors combine different category strings.
- The README's "172 activities" vs 144 public prompt sentences (all 115 used activities ⊂ 144).

## Sources
Local:
- `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/Data/Multi-Human-Annotations/human_motion.json`
- `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/HASimulator/HA-DE/connectivity/*_connectivity.json`
- `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/HASimulator/HA-DE/human-viewpoint_annotation/human_motion_text.json`
- `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA3D_simulator/human-viewpoint_annotation/human_motion_model/{HA-VLN_human_motion_prompts.txt,region_motion_text.json,skeleton2smpl.py,README.md}`
- `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA3D_simulator/tasks/HA/data/HA_{train,val_seen,val_unseen}.json`
- `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/Discrete-Continuous-VLN/data/datasets/R2R_VLNCE_v1-2_preprocessed/{train,val_seen,val_unseen,test}/*.json.gz`
- `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/HASimulator/{environments.py,detector.py,measures.py,metric.py,README.md,config/HAVLNCE_task.yaml}`
- `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/Data/README.md` (L77-129)
- `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/Data/HA-R2R-tools/{embeddings_glove_50d.json.gz,collision_num_*.json,README.md}`
- `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/demo/figs/overview_example-1.png`
- `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/habitat-sim-0.1.7/src/esp/{sim/Simulator.cpp,bindings/SimBindings.cpp,physics/bullet/BulletPhysicsManager.cpp}`
- `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/competitor-bingchengzhang/project/{scripts/seg_gt_smoke.py,havln_agent/perception/human_seg.py}`
- `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/jostar-track2` (branch origin/bohan/clarification-Oct14 README L41-42, L175, L309-313)

Web:
- https://arxiv.org/abs/2503.14229
- https://arxiv.org/html/2503.14229v2
- https://github.com/UWMILab/HA-VLN
- https://github.com/UWMILab/HA-VLN/pull/26
- https://github.com/JostarXiong/track2
- https://arxiv.org/abs/2406.19236
- https://arxiv.org/pdf/1912.04070
- https://www.di.ens.fr/willow/research/surreact/
- https://openaccess.thecvf.com/content/CVPR2023/papers/Black_BEDLAM_A_Synthetic_Dataset_of_Bodies_Exhibiting_Detailed_Lifelike_Animated_CVPR_2023_paper.pdf
- https://arxiv.org/pdf/2305.00976
- https://arxiv.org/pdf/2405.16909
- https://arxiv.org/pdf/2508.03343
- https://iclr.cc/virtual/2024/poster/19442
- https://github.com/bingchengzhang/HA-VLN
