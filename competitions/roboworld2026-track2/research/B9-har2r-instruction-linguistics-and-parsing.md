# B9: HA-R2R instruction linguistics and the parsing pipeline

**Scope.** This covers the structure of HA-R2R instructions, the region vocabulary, extracting route steps, matching human mentions to annotated humans, how much human anchors reduce goal ambiguity, a validation protocol, and prompt templates.

**Regime labels.** Each recommendation is tagged with the regime it assumes:
- **[C]** compliant regime: egocentric RGB-D plus GPS/compass, and no human_motion.json at inference.
- **[P]** privileged or offline regime: needs organizer permission. Annotations may also be used this way for training and local evaluation, which is allowed.
- **[both]** applies in either regime.

**Data limits.** The HA-R2R **2.0** episode files (HF `fly1113/HA-VLN`) are **not reachable from this sandbox**. The evidence base is therefore:
- (a) the complete **HA-R2R 1.0** discrete corpus, with per-path human links (`EXT/HA-VLN/HASimulator/HA-DE/tasks/HA/data/HA_{train,val_seen,val_unseen}.json`: 5,798 paths, 17,409 instructions);
- (b) the public **2.0** human annotations (`Data/Multi-Human-Annotations/human_motion.json`: 72 scans, 749 humans);
- (c) **six HA-R2R 2.0 instructions** whose R2R source path I identified (README examples 1–4 and the two demo instructions);
- (d) the 2.0 vocabulary `Data/HA-R2R-tools/instruction_vocab.json`, 5,079 tokens.

WebSearch worked for 3 queries. All analysis scripts are in `SP/b9_scripts/` and their outputs in `SP/b9_out/`, where SP = `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad`.

---

## 0. Executive summary (decision-relevant)

1. **Anatomy (verified on 6 of 6 traced 2.0 examples, plus the 1.0 corpus).** An HA-R2R instruction is an LLM expansion of one short R2R instruction: 18–26 words become about 100–130 words. The expansion follows the HA-VLN 1.0 visibility rule: every human mentioned is one whose annotation viewpoint is in the MP3D-connectivity `visible` set of some path viewpoint. The one traced path with no visible human gets a generic "be careful of any human activity" sentence.
   - The mentions paraphrase the 2.0 category string `<region>:<activity>` and usually keep the region ("on the porch or terrace" for `porch_terrace_deck_driveway`).
   - Only about **56% of visible humans are mentioned** (14 of 25 in the traced examples).
   - The route steps are preserved but **reworded and partly corrupted**. In 1.0, the left/right sequence survives exactly in 84–87% of rewrites, ordinals in 77–86%, and content words at 81%. The 2.0 examples also contain **invented scene details and invented region transitions** (README example 3 adds a "hallway" and ends "back in the living room", while the true path is living room ×4 → hallway).
2. **Human mentions can be matched reliably, but they localize the goal only coarsely.**
   - A plain lexical matcher (IDF-weighted stem overlap) picks an annotated path human as its top-1 for **94–95%** of 1.0 instructions.
   - Against the denser 2.0 candidate sets (10.4 humans per scan, only 57.7% with an activity unique in their scan) it picks the correct key viewpoint for **85–88%**, with 14–19% top ties.
   - Mapping mentions to the 144-activity HAPS catalog with no scan knowledge gives **86% precision@k**.
   - Geometry: the human nearest the goal is within 3 m of it on only **~41%** of val paths (median 3.1–3.4 m) and within 5 m on ~62%. An "End" human (≤1.5 m from the goal) exists on only **8–12%** of paths.
3. **The brief's hypothesis that END sentences almost always mention a human is not supported.**
   - In 1.0, the last sentence mentions a person in 36–45% of instructions.
   - In the traced 2.0 examples, 2 of 5 human-bearing instructions put a specific human in the stop context, and those humans were 3.7 m and 4.8 m from the goal.
   - The text position of a human is a weak cue for where it sits on the path. A Beginning human is in the first sentence only 15–24% of the time, and an End human in the last sentence 30–52%. Text order matches path order for 68–88% of human pairs (chance is 50%). In demo A, the human standing *at the goal viewpoint* is described in the *first* sentence.
4. **Ambiguity reduction (privileged-regime estimate, val, 2.0 humans).**
   - Requiring the candidate shortest path to pass within 3 m of the 1–2 mentioned humans keeps a median 60–67% of candidates (about **0.6–0.75 bits**).
   - Visibility-only pass-by checks are almost useless (95% kept).
   - Requiring the [end] human within 5 m of and visible from the candidate goal keeps a median ~10% (**~3.2–3.5 bits**), but drops the true goal in 27–32% of cases. Use these as **soft features**, not filters.
   - Stopping at the candidate nearest a correctly identified end human lands within 3 m of the goal for 68% of the paths that have one. That is about 40% of all paths.
5. **Region prefixes match MP3D region labels 82% of the time.** But the region prefix of the human nearest the goal predicts the goal region only 37–40% of the time (55–57% when that human is within 3 m).
   - Human clauses actively **pollute** naive end-region extraction. On paths with humans, the last-region-word heuristic scores 48.9% on R2R originals and 33.9% on HA rewrites. Removing human clauses recovers 42.9%.
   - **The parser must separate ROUTE, HUMAN, SOCIAL and EMBELLISH clauses before extracting route steps or the goal.**
6. **Compliance.** Matching mentions to `human_motion.json` at inference is forbidden by the Oct-14 clarification. In the primary regime **[C]**, the parse still provides four things: a route program, perception queries (person present, posture, count, region), social constraints, and a soft prior that the goal is "near the last-mentioned person". HAPS humans are bare SMPL bodies with **no props** (no vacuum, no camera), so a VLM can verify posture, count and room but not activity.
   - Annotation-based matching is legitimate for **training labels** (train split) and for **local evaluation**.
   - The R2R original instructions for every test episode are public (R2R_test.json, joined in A1). Using them as an inference input is a **gray area** (see the open questions).

---

## 1. Verified anatomy of an HA-R2R instruction

### 1.1 How the instructions were generated (from the organizers' own documentation)
- The prompt input slots are `[instruction_text]` (the R2R instruction), `[start]`, `[during]` and `[end]`. Each slot holds a HAPS category string such as `"hallway: An individual cleaning or vacuuming."`. The prompt asks for an "objective, step-by-step description... beginning, during, and end... **Expand your description by including character actions, objective descriptions of objects, and details of the movement process**... simulate the robot's movement" (`EXT/HA-VLN/Data/HA-R2R/README.md` L60-80; `Data/README.md` L73-95). **high**
- The generators were ChatGPT-4o and LLaMA-3-8B-Instruct, with a few-shot prompt and iterative refinement (same file L33-56; paper arXiv 2503.14229 appendix via WebSearch). **high**
- The few-shot example in the README uses 1.0-era labels ("other room:", with spaces). The 2.0 categories use underscores (`other_room:An_individual_...`). **high**

### 1.2 Six HA-R2R 2.0 instructions traced to their R2R source path and to the 2.0 humans
Each README or demo instruction was located by co-occurrence of its activities in one scan, then by its R2R source text. Script: `SP/b9_scripts/an2_examples_geom.py <scan>:<path_id>`.

| Example | Split / scan / path / instr idx | R2R original | Humans mentioned → 2.0 category (path idx of nearest vp, distance to goal) | Visible / mentioned |
|---|---|---|---|---|
| README ex1 | train ac26ZMwG7aT 6920 [1] | "Leave the library and take a left. Go straight into the bedroom. Stop outside of the closet." | `bedroom:A_person_searching_for_a_lost_item` (end, 2.32 m); `porch_terrace_deck_driveway:A_family_having_a_casual_conversation` (18–20 m away, visible) | 4 / 2 |
| README ex2 | train VzqfbhrpDEA 2337 [1] | "Walk across the left side of the dining room. Enter through the doorway. Turn left and walk down the hallway. Stop at the entrance of the office." | `hallway:Friends_laughing_and_sharing_stories_over_dinner` (idx 1; **text places it "in the dining room"**); `office:A_person_taking_photographs_of_the_view` (end, 4.82 m) | 2 / 2 |
| README ex3 | train mJXqzFtmKg4 2339 [1] | "Head straight until you pass the couches and wait by the right candle in the wall." (16 words) | dance (idx 2), quiet intimate conversation (idx 4), `hallway:A_couple_having_a_date_night_at_the_bar` (idx 4), `living_room:A_person_checking_themselves_in_a_hallway_mirror` (idx 1, 3.68 m, **described as the END**) | 8 / 4 |
| README ex4 ("no humans") | train ac26ZMwG7aT 2323 [0] | "Exit the room and make a right, make a right through the first doorway and wait near the shelves." | none; text adds "be careful of any human activity or objects" | **0** / 0 |
| demo A | val_unseen 8194nk5LbLH 3785 [0] | "Move forward past the television on the wall, continue forward until you reach the potted plant and a door." | `lounge:Someone_talking_on_the_phone_while_pacing` (**key vp = goal vp, 0.99 m, but described in the FIRST sentence**), TV watchers ×2 (idx 1), toasting cocktails (idx 2, 2.61 m) | 8 / 4 |
| demo B | val_unseen QUCTc6BB5sX 5952 [0] | "Exit the room. Turn left and then turn left again. Go into the room and past the bed. Turn left into the bathroom. Wait near the sink." | `hallway:Someone_ironing_clothes` (idx 1), `bedroom:Someone_reading_a_book_in_bed` (idx 4, 5.09 m) | 3 / 2 |

Sources: `EXT/HA-VLN/Data/HA-R2R/README.md` L17-22, `EXT/havln2/demo/README.md` (Navigation Instruction rows), `EXT/havln-challenge/index.html` L185, `R2R_{train,val_unseen}.json`, `human_motion.json`.

What these examples verify (high confidence unless noted):
- Every mentioned human is visible from the path under the HA-VLN 1.0 rule `getVisiblePoints` (`HA-DE/src/utils/get_info.py` L163-228, L403-416). The no-human example has 0 visible humans. The generator therefore fills the slots from **path-visible humans**.
- Applying that rule to 2.0 humans gives "≥1 visible human" for **88.0% / 90.6% / 88.4%** of train / val_seen / val_unseen paths. The organizers' human-influenced fractions β are 85.1% / 87.7% / 86.6% (`HASimulator/metric.py`). They are close, which suggests β counts roughly this set (**medium**).
- **The region is often kept** ("on the porch or terrace", "into the hallway", "in the bedroom"). It is sometimes **replaced by the route's region** (ex2 puts the hallway dinner party in the dining room).
- **Slot order in the text does not follow path order** (ex3, demo A).
- **Invented content.** Ex2 adds "The dining room features a large table and chairs", "framed pictures along the walls" and "sound of laughter...". Ex3 invents "As you transition into the hallway", "keeping to the right side of the hallway" (a spurious *right*) and "back in the living room", whereas the MP3D labels along the path are living ×4 → hallway. Demo A invents "people... seated comfortably on sofas".
- **Left/right preserved** in 4 of 5 examples that have turns; ex3 adds an extra "right".

### 1.3 Corpus statistics from HA-R2R 1.0 (`SP/b9_out/an1_stats.json`, `an7_fidelity.json`, `an10_order.json`)

| Measure | train | val_seen | val_unseen |
|---|---|---|---|
| words per instruction, mean (R2R source) | 57.1 (26.3) | 58.8 (26.5) | 50.1 (26.1) |
| paths with ≥1 annotated (1.0) human | 75.2% | 78.8% | 65.0% |
| human rel_pos counts (Beginning / Obstacle / Around / End) | 274 / 1004 / 4072 / 283 | 25 / 77 / 311 / 22 | 50 / 141 / 440 / 42 |
| person word present when path has humans / has none | 95.2% / 1.3% | 94.4% / 1.9% | 93.4% / 0.9% |
| no-human paths: HA text identical to R2R | yes (1.0 only; 2.0 rewrites these too, see ex4) | | |
| last sentence mentions a person | 44.2% | 44.6% | 35.8% |
| generation artifacts ("Q2: What is the relative position description?", "Here is") | 2.9% | 3.6% | 3.0% |
| content-word retention vs R2R (mean; p10) | 0.811; 0.636 | 0.806; 0.625 | 0.813; 0.636 |
| L/R sequence identical to R2R | 85.3% | 83.8% | 86.5% |
| R2R L/R order is a subsequence | 89.4% | 87.8% | 90.1% |
| ordinals preserved | 81.3% | 85.6% | 76.6% |
| adds a region word not in R2R (not explained by the human description) | 71.0% (8.6%) | 73.2% (9.4%) | 75.4% (8.8%) |
| text order of 2 humans = path order | 71.6% | 68.3% | 87.8% |
| Beginning human mentioned in first sentence | 23.9% | 19.3% | 15.3% |
| End human mentioned in last sentence | 43.1% | 29.8% | 51.5% |

**Inference (medium).** 2.0 instructions are about twice as long (112 vs 57 words; vocabulary 2,616 → 5,032 per paper, 5,079 tokens in the released vocabulary), and the prompt explicitly asks for added objects and movement detail. So 2.0 route fidelity is probably **no better than 1.0's ~85%** L/R preservation. Expect at least 10–15% of test instructions to carry at least one corrupted or invented route element.

### 1.4 HA-R2R 2.0 lexicon signals (`Data/HA-R2R-tools/instruction_vocab.json`, 5,079 tokens)
- Contains `robot`, `human`, `person`, `individual`, `obstacle`, `beginning`, `during`, `end`, `pause`, `await`, `halt`.
- Contains metric and angle tokens: `2-meter`, `45-degree`, `90-degree`, `180-degree`, `360-degree`, `meters`, `feet`, `clockwise`.
- Contains ordinals up to `tenth`.
- **No** `q1`/`q2`/`input`/`output` tokens, so the 1.0 Q&A artifacts are probably gone (**medium**).
- `familyroom`, `laundryroom`, `toolroom` and `rec` are absent: the LLM turned the underscore and slash labels into ordinary words. **high**
- Website: "Instructions average 112 words, with **20–60% human-related content**" (`EXT/roboworld2026.github.io/track2.html` L116). **high**

---

## 2. Human activity vocabulary and its link to instructions (`SP/b9_out/an3_annotations.json`)

- **2.0 public:** 749 humans, 331 unique category strings, **115 unique activity sentences, all from the 145-line HAPS 1.0 prompt list** (`EXT/HA3D_simulator/human-viewpoint_annotation/human_motion_model/HA-VLN_human_motion_prompts.txt`, which equals `region_motion_text.json` with 29 regions × 5). HAPS 2.0 claims 172 activities and 486 motions, so test scans *may* contain up to ~57 activities outside this list. **high** for the public data.
- **Activity is decoupled from region in 2.0.** For 516 of 749 humans (69%), the region prefix differs from the activity's native HAPS-1.0 region. Examples: `hallway:A_couple_having_a_date_night_at_the_bar`, `living_room:A_person_checking_themselves_in_a_hallway_mirror`. The prefix is the **placement region**: it agrees with the MP3D region label of the nearest labelled panorama for **82%** (428 of 522) of humans (`an6_region.py`, using A9's decoded niessner 12-class labels). **high**
- **Frequent activities:** phone while pacing 78; quiet intimate couple 53; friends sharing stories over dinner 53; taking photographs 32; cleaning or vacuuming 29; napping on couch 25; toasting cocktails 20; dance 19.
- **Distinctiveness within a scan:**
  - 2.0 has 10.4 humans per scan (median 10, range 6–19).
  - Only **57.7%** have a scan-unique activity and **66.6%** a scan-unique (region + activity) category. HA-VLN 1.0 had 93.3% unique.
  - Key viewpoints with 1 / 2 / 3 / 4 humans: 420 / 66 / 47 / 14.
  - **Group words do not track instance counts.** "couple" categories appear as a single instance in 35 of 54 cases, and "friends/family/group" in 107 of 138. A "couple" in the text is often one rendered body.
- **1.0 → 2.0 carry-over:** in the 72 public scans, 254 of 304 (84%) of 1.0 human viewpoints are reused in 2.0, and 207 (68%) keep the same activity. The 18 test scans have 70 public 1.0 humans (`human_motion_text.json`), so about 48 of the ~161 2.0 test humans are probably predictable. Using this at inference is privileged and **non-compliant**. 1.0 test-scan prefixes include `dining booth`, `classroom`, `bar` and `utilityroom/toolroom`, which never appear in the public 2.0 set, so the parser's region vocabulary must cover all 30 MP3D codes.
- **No props.** HAPS motions are pure SMPL bodies (README: 486×120×(10+72+6890×3); MDM text-to-motion). "Vacuuming" or "taking photographs" is only a body pose: **an activity cannot be confirmed visually, only posture, count and location** (inference from the data format, **high**).

---

## 3. Region ontology and mapping

| MP3D .house code | MP3D doc name | habitat-sim 0.1.7 name (`Mp3dSemanticScene.cpp` L18-52) | HAPS 1.0 prefix | HAPS 2.0 prefix | niessner 12-class id (A9 decode) | Instruction surface forms (parser synonyms) |
|---|---|---|---|---|---|---|
| a | bathroom | bathroom | bathroom | bathroom | 10 | bathroom, restroom, washroom, powder room, bath |
| b | bedroom | bedroom | bedroom | bedroom | 11 | bedroom, master/guest bedroom, kids' room, nursery |
| c | closet | closet | closet | closet | (→11/10) | closet, walk-in closet, wardrobe |
| d | dining room | dining room | dining room | dining_room | 5 | dining room/area, breakfast room/nook |
| e | entryway/foyer/lobby | entryway/foyer/lobby | entryway/foyer/lobby | entryway_foyer_lobby | 4 | entryway, entry, foyer, lobby, front door, vestibule, entrance hall ("entryway, foyer, or lobby" verbatim in 1.0) |
| f | familyroom | familyroom/lounge | familyroom | family_room | 3 | family room, den |
| g | garage | garage | garage | garage | – | garage |
| h | hallway | hallway | hallway | hallway | 12 | hallway, hall, corridor, passage, landing (ambiguous with stairs) |
| i | library | library | library | library | – | library (not "study") |
| j | laundryroom/mudroom | laundryroom/mudroom | laundryroom/mudroom | laundry_room_mudroom | – | laundry room, mudroom, utility (ambiguous with u) |
| k | kitchen | kitchen | kitchen | kitchen | 8 | kitchen, kitchenette, pantry (approx.) |
| l | living room | living room | living room | living_room | 6 | living room, sitting room, great room, parlor |
| m | meetingroom/conferenceroom | same | meetingroom/conferenceroom | meeting_room_conference_room | – | meeting room, conference room, boardroom |
| n | lounge | lounge | lounge | lounge | 2 | lounge, lounge area, sitting/seating area |
| o | office | office | office | office | 1 | office, study, workspace |
| p | porch/terrace/deck/driveway | porch/terrace/deck | porch/terrace/deck/driveway | porch_terrace_deck_driveway | 9 | porch, patio, deck, terrace, driveway, veranda ("porch or terrace") |
| r | rec/game | rec/game | rec/game | rec_game | – | game room, recreation room, billiards room |
| s | stairs | stairs | stairs | stairs | 7 | stairs, staircase, stairway, steps, landing |
| t | toilet | toilet | toilet | toilet | (→10) | toilet, WC, half bath |
| u | utilityroom/toolroom | same | utilityroom/toolroom | (not public) | – | utility room, tool room, workshop |
| v | tv | tv | tv | tv | – | TV room, theater, media room |
| w | workout/gym/exercise | same | workout/gym/exercise | workout_gym_exercise | – | gym, exercise/workout room |
| x | outdoor areas | outdoor | outdoor areas containing grass... | outdoor_area | (→9) | outside, yard, garden, lawn, courtyard, pool area |
| y | balcony | balcony | balcony | balcony | – | balcony |
| z | other room | other room | other room | other_room | – | "the room", "a room" (generic) |
| B | bar | bar | bar | (not public) | – | bar, wet bar |
| C | classroom | classroom | classroom | (not public) | – | classroom |
| D | dining booth | dining booth | dining booth | (not public) | – | booth |
| S | spa/sauna | spa/sauna | spa/sauna | spa_sauna | – | spa, sauna, hot tub, jacuzzi |
| Z / - | junk / no label | junk | – | – | – | – |

Notes:
- The `.house` `R` lines carry the label char plus a bounding box per region (`EXT/Matterport-niessner/data_organization.md` L192-277).
- At inference, the region of a viewpoint or navmesh point comes from the `.house` file **[P]**, or from a region-classifier VLM on egocentric frames **[C]**.
- The 12-class panorama labels for the 18 test scans are public (A9). Using them at inference is privileged.

---

## 4. Route-step extraction

### 4.1 What the route text contains
R2R test originals are the text that the test instructions were expanded from (`R2R_test.json`, 4,173 instructions, `an11_lexicon.py`, `an7_fidelity.py`):
- left/right in 78.5% (1.49 per instruction); ordinals in 25%; stop or wait phrase in 87%; stairs in 43%; door, doorway or exit in 56%; turn around or 180 in 6.3%; any region word in 85%; up stairs 15%, down stairs 11%.
- Verb frequency per 1,000 instructions: walk 614, stop 543, turn 530, go 415, wait 316, exit 194, enter 170, take 114, step 111, pass 107.
- Landmarks by share of instructions: stairs 35%, door 32%, hallway 22%, table 19%, bedroom 19%, doorway 18%, bathroom 14%, chair 14%, kitchen 10%, bed 8%, couch 4%, sink 4%, painting 4%.
- Stop-clause relations: "at the" 13%, "on the" 11%, "near" 8%, "in front of" 7.7%, "by the" 7%, "next to" 5.5%, "in the doorway" 4.3%, "inside" 3.3%, "top/bottom of stairs" 5.3%.

### 4.2 Output schema (JSON) **[both]**
```json
{
 "episode_id": "1",
 "route": [
  {"id": 1, "verb": "exit|enter|go|go_through|pass|turn|ascend|descend|continue|cross|follow|stop|wait",
   "direction": "left|right|straight|around|slight_left|slight_right|up|down|null",
   "landmark": {"text": "first doorway on the right", "category": "region|door|stairs|object|human",
                "region_code": "h|null", "ordinal": 1, "side": "right|left|null"},
   "until": "you reach the closet", "span": "<verbatim>", "provenance": "ROUTE", "confidence": 0.9}
 ],
 "humans": [
  {"hid": "H1", "span": "<verbatim>", "activity_ids": [[87, 0.8], [12, 0.1]], "activity_text": "searching for a lost item",
   "region_said": "b", "region_source": "explicit|from_route_context|none", "stage_said": "start|during|end",
   "attached_step": 3, "posture_prior": "standing|sitting|lying|walking", "count_word": "person|couple|group|family|children|people",
   "social": ["do_not_disturb", "keep_distance", "quiet"]}
 ],
 "stop": {"relation": "in_front_of|next_to|near|at|inside|outside|in_doorway|top_of_stairs|bottom_of_stairs|between|before|after",
          "anchor": {"text": "closet", "category": "object|door|region|stairs|human"}, "region_code": "b|null",
          "human_ref": "H2|null", "span": "<verbatim>"},
 "start_context": {"region_code": "i", "facing_text": null, "humans": []},
 "floor_change": "up|down|none|unknown",
 "embellishments": [{"span": "The dining room features a large table and chairs.", "reason": "scene description not needed to follow the route"}],
 "generic_safety_only": false,
 "self_check": {"lr_sequence": ["left"], "n_route_steps": 4, "conflicts": []}
}
```

### 4.3 Prompt templates

**P1: clause classification and parse** (any frontier LLM; distil to Qwen-7B for the open-weight story) **[both]**
```
SYSTEM: You parse navigation instructions from the HA-R2R dataset. Each instruction was produced by an LLM that took a SHORT
human-written route instruction (~26 words, e.g. "Leave the library and take a left. Go straight into the bedroom. Stop outside
of the closet.") and expanded it to ~110 words by (1) inserting descriptions of simulated people taken from a fixed catalog of
activities, each tagged with the room where that person stands, for the beginning/during/end of the route, (2) adding social
advice ("do not disturb them"), and (3) adding invented scene details and sometimes invented room transitions.
Tag every clause with exactly one provenance: ROUTE (a movement, turn, landmark or stop condition that a short human route
instruction would contain), HUMAN (describes a person or their activity/location), SOCIAL (behavioral advice), EMBELLISH
(scene description, sounds, objects or room transitions that are not needed to follow the route or that only restate a
HUMAN clause's room). Rules: never invent steps; copy left/right/ordinals exactly as written; if a room is mentioned ONLY
inside a HUMAN clause, do not create a route step for it; if the stop sentence mentions a person, record it as stop.human_ref
but take the stop anchor from objects/doors/rooms when present; output JSON matching the schema; then list your left/right
sequence and any internal conflicts in self_check.
FEW-SHOT: README examples 1-4 (all TRAIN split: ac26ZMwG7aT/6920, VzqfbhrpDEA/2337, mJXqzFtmKg4/2339, ac26ZMwG7aT/2323)
with gold parses written from their R2R originals (shown in section 1.2). Do NOT use the val_unseen demo instructions as shots.
USER: Instruction: "<HA-R2R text>"
```

**P2: closed-set activity canonicalization** (scan-agnostic, compliant) **[C/both]**
```
SYSTEM: Map each HUMAN mention to the activity catalog below (145 numbered HAPS activity sentences; region prefixes removed).
Return top-3 ids with probabilities, or "OTHER" if none fits (the test set may use activities outside this list).
Also return posture_prior in {standing, sitting, lying, walking/pacing, dynamic} and the room said in the text (MP3D code).
CATALOG: 1 "A person brushing their teeth in front of the mirror." ... 145 "...".
USER: mentions: [{"hid":"H1","span":"..."}, ...]
```

**P3: matching confirmation** (privileged or offline only, or train-label generation) **[P]**
```
SYSTEM: A navigation instruction mentions a person. Candidate annotated humans in this building are listed with their
category "<region>:<activity>", whether several humans share the spot, and (if a candidate route is given) how far the route
passes from each and at which step. Choose the candidate the mention refers to, or NONE. Remember: instruction writers
sometimes moved a person into the room the route was in; region is a soft cue, activity wording is the strong cue.
USER: mention: "...", stage_said: "end", route_step: 4; candidates: [{"id":"A","category":"office:A_person_taking_photographs_of_the_view","group":1,"min_dist_to_route_m":4.8,"nearest_step":5}, ...]
```

**P4: VLM verification on egocentric frames** (compliant) **[C]**
```
SYSTEM: HAPS humans are untextured-prop SMPL bodies: there is NO vacuum, camera, phone, glass or book. Judge only: is at
least one person visible; how many; posture (standing/sitting/lying/moving); which room type this looks like; roughly how far
(use the depth summary). Answer JSON {person_visible, count, posture, room_type, distance_m, confidence}.
USER: [RGB frame(s)] [depth summary] Expected from instruction: "<activity_text>" (posture_prior=sitting, room=d)
```

---

## 5. Matching algorithm (mention → annotated human)

**Use [P] / training labels. Not allowed at inference in [C].**
1. **Canonicalize** each mention with P2: activity distribution `p(a|m)`, region said `r_m`, stage said `s_m`.
2. **Group entities.** Merge humans that share a key viewpoint (the 32-hex prefix of the 33-character keys) and the same category into one entity. Groups are co-located, so error tolerance is not affected.
3. **Score** each mention–entity pair:
   `S = 0.55·max(p(a_h|m), cos(emb(span_m), emb(activity_h))) + 0.25·R(r_m, region_h) + 0.10·G(stage) + 0.10·D(route)`
   - R is 1 for the same MP3D code, 0.5 for a synonym group (f/n/l; a/t; b/c; p/x/y), and 0 otherwise.
   - G is the soft consistency between the stage said and the entity's position along a candidate route.
   - D = exp(−d_route/3 m), available offline only.
   - Embeddings: any sentence encoder (e5, bge, gte) or a cross-encoder.
4. **Assign** with Hungarian matching across mentions (one mention per entity), with a NONE option below a threshold τ. τ is calibrated on the **train** split (val and test must not be used for training).
5. **LLM confirmation (P3)** when the top-2 margin is below 0.1, or for ties caused by duplicate activities (expected in about 15–20% of mentions).

**Expected accuracy.** The lexical lower bound is 94–95% top-1 against 1.0 candidates and 85–88% against 2.0 candidates. A frontier LLM with region evidence should reach **≥95% entity accuracy** (inference, **medium**). NavAgent (arXiv 2411.08579) reports GPT-4 landmark-phrase extraction at **98.4 P / 98.2 R** (Touchdown) and 99.6 / 99.7 (Map2seq). So **extraction is not the bottleneck: the noisy source text is.**

---

## 6. How much do human anchors reduce goal ambiguity?

Scripts: `an5_geometry.py`, `an12_ambiguity.py`, `an12b_ambiguity_passby3m.py`, `an8_endhuman_region.py`. The setting is 2.0 humans on R2R val paths in public scans; R2R paths are graph shortest paths.

| Quantity | val_seen | val_unseen | train |
|---|---|---|---|
| paths with ≥1 visible 2.0 human | 90.6% | 88.4% | 88.0% |
| visible humans per path (mean) | 3.75 | 3.51 | 3.43 |
| paths with an End human (≤1.5 m of goal vp) | 11.2% | 8.4% | 11.8% |
| goal → nearest visible human, median (p25–p75) | 3.23 m (2.0–5.4) | 3.11 m (2.0–5.6) | 3.43 m (2.0–5.6) |
| nearest visible human within 3 m / 5 m of goal | 40.6% / 64.1% | 41.3% / 61.4% | 38.4% / 61.7% |
| candidates kept if the path must pass ≤3 m from the 1–2 path-nearest humans (median) | 59.6% (0.75 bits) | 66.7% (0.59 bits) | – |
| same, using visibility instead of 3 m | 94.4% | 94.9% | – |
| candidates kept if the end human is ≤5 m from and visible from the candidate (median) | 9.0% (3.5 bits), GT kept 73% | 10.3% (3.3 bits), GT kept 68% | – |
| stopping at the candidate nearest the end human is within 3 m of the goal (paths that have one) | 66.7% | 67.9% | – |
| region prefix of goal-nearest human = goal region label | 40.1% (56.6% if ≤3 m) | n/a (no labels) | 37.3% (55.1%) |

**Interpretation (inference, medium):**
- Human anchors are a **3-bit end-of-route cue** for the roughly 60% of episodes whose stop clause or final stage names a person near the goal.
- Otherwise they are a **sub-1-bit pass-by cue**. As a hard rule they would discard the true goal about 30% of the time.
- Combined with the parsed route-end clause (object or door relation), they mainly resolve which-room and which-side ambiguities.
- They are worth roughly +3 to +8 SR points in a candidate-ranking pipeline **[P]**. As a closed-loop stop-region prior **[C]** they are worth less, perhaps +1 to +3, because the agent must perceive the person and HAPS bodies lack props.

---

## 7. Validation protocol (run on day 1 once HA-R2R 2.0 val_unseen.json.gz is downloaded by someone with HF access)

- **Inputs.**
  - The 1,839 val_unseen episodes, joined to R2R val_unseen by `trajectory_id` (= R2R path_id; A1 index).
  - GT: reference path viewpoints and goal.
  - The 2.0 humans for the 11 val_unseen scans (public).
  - `.house` regions (from MP3D, once approved) and the A9 labels for train scans.
- **Prompt development on TRAIN only** (10,819 episodes). Report val_unseen once per prompt version. Val and test must not be used for training.
- **Metrics and targets:**
  1. **Route fidelity:** parse(HA) vs parse(R2R original), measuring the exact L/R sequence, ordinal set and stop-anchor noun. Target ≥ the generator ceiling (about 85–90%, based on the 1.0 rewrite fidelity). Report the disagreement cases. They estimate how often the HA text itself is wrong.
  2. **Human mention extraction P/R:** silver labels are humans visible from the path with lexical score ≥ 0.5, plus a 100-episode manual audit. The lexical recall baseline is 84–88%.
  3. **Closed-set activity accuracy** (P2 vs category): lexical baseline P@k 86%. Target ≥ 95%.
  4. **Mention → entity accuracy** (P3 pipeline, privileged): lexical baseline 85–88%. Target ≥ 95%.
  5. **End-region accuracy vs the goal's `.house` region:** naive baselines are 34% (HA raw) / 43% (human clauses removed) / 49% (R2R original). Target ≥ 55%. Also report the ceiling given label noise (goals at doorways).
  6. **Stop-stage human:** the fraction of episodes whose stop clause names a human, the distance from that human to the goal, and whether it is the nearest visible human. This replaces the brief's untested hypothesis with numbers.
  7. **Downstream:** the C8 ranker's top-1 within 3 m with and without human features, and the closed-loop [C] agent's SR with and without the parse-derived stop prior.
- **Bundle-day test checks:** run P1 on all 3,408 test instructions. Flag instructions with `generic_safety_only=true` (expected about 15%, i.e. 1 − β(test) = 549/3408 = 16.1%) and with low-confidence route steps. Comparing with the R2R originals is permitted only for QA if organizers allow it (gray area).
- **Cost:** about 4k tokens per instruction (catalog included), so about 14M tokens per pass over test, or 70M with 5× self-consistency. A local 7B model can also do it.

---

## 8. Recommendations
1. **[both]** Build the P1 parser with the six-way schema now. Make **clause provenance tagging** the first step and keep HUMAN, SOCIAL and EMBELLISH clauses out of the route program. Use README examples 1–4 (train) as few-shot shots with gold parses from their R2R originals.
2. **[both]** Canonicalize human mentions to the 145-entry HAPS catalog (P2) plus an OTHER class. Carry posture, count and room priors, but treat count words as weak ("couple" is one body in 65% of cases).
3. **[C]** Use humans in the closed-loop agent only as: (a) a social-cost trigger (keep distance and avoid collisions, which cost TCR and CR); (b) progress cues ("the room with seated people" leads to the next step); (c) a soft stop prior, "goal within ~3–5 m of the last-mentioned person", **only when the stop sentence itself names the person**. Verify with P4 on posture, count and room, not activity.
4. **[P/training]** Auto-label HA-R2R **train** human mentions to annotated humans (lexical first pass, then LLM confirmation) to supervise grounding or progress heads and DAgger teachers. Offline, add the end-human distance (about 3.3 bits) and the pass-by-3 m feature (about 0.6–0.75 bits) to candidate scoring **as soft features**.
5. **[both]** Never let a room that appears only in a human clause become the goal region. The human prefix gives the goal region only 37–40% of the time.
6. **[both]** Expect at least 10–15% corrupted or invented route elements in the test text. Use 3-way self-consistency across the sibling instructions of a trajectory (IDs 3k+1..3k+3 share the goal; A1) to vote on route programs and stop anchors. This cross-episode use is a gray area under [C], so ask the organizers.
7. **[both]** Ask the organizers (one email, together with other rule questions) whether the public R2R original instruction (R2R_test.json, and FG-R2R sub-instructions) may be used as an auxiliary input. It would remove most invented-content noise.
8. **[both]** Region vocabulary: support all 30 MP3D codes (test scans include dining booth, classroom, bar and utility room in 1.0) through the synonym table in section 3.

## 9. Open questions
- How exactly does 2.0 fill the [start]/[during]/[end] slots (path-index thresholds, number of humans per slot, random sampling)? Settle it on day 1 from HA-R2R 2.0 train/val.
- Fraction of 2.0 instructions whose stop sentence names a person (estimate 35–55%; based on 2 of 5 traced examples and the 1.0 rate of 36–45%).
- Do test scans use activities outside the 145-entry list (HAPS 2.0 has 172)?
- Are LLaMA-3-8B-generated instructions (vs GPT-4o) noisier, and can they be identified? A style classifier could weight trust.
- Are the R2R originals, FG-R2R sub-instructions or sibling instructions allowed as inference inputs under the Oct-14 clarification?
- Will the Phase-2 bundle include test-scan human placements? This is irrelevant for [C], but it matters for local replay and verification.

## 10. Sources
- `EXT/HA-VLN/Data/HA-R2R/README.md` L17-22, L33-80; `EXT/HA-VLN/Data/README.md` L73-95 (generation prompt, examples).
- `EXT/havln2/demo/README.md` (demo instructions); `EXT/havln-challenge/index.html` L185; `EXT/a10/F1y1113_HA-VLN-webpage/src/pages/index.astro` L252.
- `EXT/HA-VLN/HASimulator/HA-DE/src/utils/get_info.py` L163-262 (visibility rule, Beginning/Obstacle/Around/End with 1.5 m threshold).
- `EXT/HA-VLN/HASimulator/HA-DE/tasks/HA/data/HA_*.json` (HA-R2R 1.0); `.../tasks/R2R/data/R2R_*.json`; `.../con/{pos_info,con_info}`; `.../connectivity`.
- `EXT/HA-VLN/Data/Multi-Human-Annotations/human_motion.json`; `EXT/HA-VLN/HASimulator/HA-DE/human-viewpoint_annotation/human_motion_text.json`.
- `EXT/HA3D_simulator/human-viewpoint_annotation/human_motion_model/{HA-VLN_human_motion_prompts.txt,region_motion_text.json,README.md}`.
- `EXT/HA-VLN/Data/HA-R2R-tools/{instruction_vocab.json,README.md}`; `EXT/HA-VLN/Data/HAPS2_0/README.md`; `EXT/track2/README.md` L174; `EXT/roboworld2026.github.io/track2.html` L116.
- `EXT/habitat-sim-0.1.7/src/esp/scene/Mp3dSemanticScene.cpp` L18-52; `EXT/Matterport-niessner/data_organization.md` L192-277; A9 labels `SP/a9_out/mp3d_regcls_pano_labels.json`.
- A1 findings (test index, R2R-original join): `SP/findings/A1-episode-format-and-test-split.md`; A10 (paper stats).
- Web sources:
  - [HA-VLN 2.0 arXiv HTML](https://arxiv.org/html/2503.14229): 27→112 words, vocabulary 2,616→5,032, 16,844 instructions
  - [arXiv abs 2503.14229](https://arxiv.org/abs/2503.14229)
  - [UWMILab/HA-VLN](https://github.com/UWMILab/HA-VLN)
  - [NavAgent 2411.08579](https://arxiv.org/pdf/2411.08579): GPT-4 landmark extraction P/R about 98–99.7
  - [CONSOLE 2405.18721](https://arxiv.org/html/2405.18721)
  - [Open-Nav 2409.18794](https://arxiv.org/pdf/2409.18794)
  - [NavCoT 2403.07376](https://arxiv.org/pdf/2403.07376)
- Scripts and outputs: `SP/b9_scripts/an1_stats.py … an12b_ambiguity_passby3m.py`, `SP/b9_out/*.json`.
