# V1 — Adversarial review: expected-score and win-probability claims

Reviewer lens: expected Score / SR ranges and win probability in `competitions/roboworld2026-track2/` (01-strategy.md §0, §3, §5,
§6, §10, plus §2/§12 where they restate the same quantities). Method: local files and arithmetic only (no web search).
Rule applied: if the evidence is thin, the verdict is **refuted**.

Paths: `S/` = `/home/user/open-data-eval/competitions/roboworld2026-track2/`; `R/` = `S/research/`;
`X/` = `/tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/`.
Reproduction scripts written for this review (stdlib only, run with `python3 -I`):
`X/v1_review/calc.py` (conversions, derivatives), `X/v1_review/mc.py` (A7 Monte Carlo replica + stress tests),
`X/v1_review/corr.py` (corrected ranges at realistic NE).

Formula used (00-competition-facts.md L53-55; havln_tools/score.py): Score = 100·Nav·(0.70+0.30·Social),
Nav = 0.8·SR + 0.2·3/(3+NE), Social = 0.75(1−CR) + 0.25/(1+TCR). At zero collisions **Score = 80·SR + 60/(3+NE)**.
Official CR normalisation = colliding episodes / 2,859 on test (×1.192 vs an all-episode mean).

---

## 1. Headline findings (most consequential first)

1. **The clean K=1 range "Score 46–55" (L243) is a stretch target, not an expectation. Refuted as stated.**
   - Its lower end (SR 0.50) already equals the **best measured zero-contact K=1 result on the easier benchmark**: human-free R2R-CE with
     short R2R instructions, ETP-R1 + depth guard, clean SR 50.1, proxy Score 42.9–43.5 (R/B2 L27). ETP-R1 also needs 12 simultaneous views,
     i.e. ~22 turns per decision under the rules.
   - The package's own B2 ceiling says "egocentric closed loop reaches 0.25–0.40 SR"; with fine-tuning **and an oracle collision layer**
     it reaches 0.45–0.60 (R/B2 L15).
   - A7 scores the same architecture class for rivals at 39.5–46.7: fine-tuned VLA + shield, and frontier VLM + shield (R/A7 L87-88).
   - No HA-VLN measurement of any proposed component exists yet.
   - The range (±4.5 Score) is narrower than the package's own ±8 pp SR (≈ ±6.5 Score) val→test interval (R/C6 L46, L92).
2. **The K>1 range "60–66" (L243) is mis-sourced and overstated.**
   - The cited source (C9, via digest L195) says **58–62** at SR 0.62–0.68 (R/C9 L262).
   - 60–66 is C6's **dev-set** number (R/C6 L90), and C6 itself says test = dev − 0…3 (R/C6 L92).
   - So §6 sets a test-basis K=1 range (C9) beside a dev-basis K>1 range (C6), which inflates the implied K>1 uplift to about +11–14.
     On the same basis the uplift is +6 to +10.
   - The best measured K>1 analogue (first contact-free tape among 3 depth-guarded agents, human-free) is 62.4 % clean SR, i.e. Score ≈ 58.6
     (R/C8 L28). Reaching 60 needs SR ≥ 0.625 at NE 3 m.
3. **§0.5's "SR 0.50–0.65, NE 2–3 m, CR≈TCR≈0 → Score 50–65" (L46) is refuted.**
   - With zero collisions every failure stops ≥ 3 m from the goal. At SR 0.50, NE 2 m needs every failure at exactly 3 m and a mean
     success distance of 1.0 m.
   - Measured continuous-VLN failures stop a median 7.4–8.7 m away (R/B10 L57), and every published R2R-CE agent at SR 0.54–0.70 has
     NE 3.7–5.2 m (R/B2 L21-31, L126-150). Realistic NE at SR 0.50–0.65 is 3.8–5.1 m, which gives Score ≈ 47–61.
   - Arithmetic check: even at NE 2–3 m the formula gives 50.0–64.0 (65 needs NE 1.6 m).
4. **The "~85 % win at Score ≥ 52" claim (L316-317) reproduces exactly from A7's script (0.867) but is fragile and overstated.**
   - It rests on 10 guessed Bernoulli probabilities and point scores with no calibration data. A7 labels it "low confidence" (R/A7 L7, L93);
     the strategy drops that label.
   - Plausible alternative inputs taken from the package itself give **63–79 %**:
     - the top of A7's own probability ranges;
     - rivals scored as we score ourselves;
     - §8's "Med" likelihood for a privileged-planner rival (which alone gives 67 %).
   - The parenthetical "SR ≥ .55, CR ≤ .1" does not imply Score ≥ 52: A7's own T7 row at SR .55 / CR .1 is 51.8, and at realistic NE it is ≈ 50.
   - Unconditionally, our win probability is ≈ 0.54–0.72, given a realistic distribution of our own score.
5. **At least six different K=1 clean expectations coexist.** They range from Score 40–50 (L45) and SR 0.25–0.40 (B2 ceiling) up to
   Score 52–63 (C8), and the same SR range 0.50–0.62 maps to Scores about 7 points apart (C6 vs C9). The cause is unstated NE and collision
   assumptions. §0.5 assumes CR≈TCR≈0 and W6 requires TCR 0, while the 46–55 range itself assumes **7–11 % colliding episodes** (`X/work/c9/score.py`).

---

## 2. Claims table

Verdicts: **holds** · **overstated** (direction right, magnitude/certainty too high, or misapplied) · **refuted** (contradicted by
arithmetic or by the package's own evidence, or unsupported).

| # | Claim | Location | Verdict | Evidence | Proposed corrected wording |
|---|---|---|---|---|---|
| 1 | Final K=1 target SR 0.50–0.60 → Score 46–55 | 01 L243; R/C9 L53, L256-257, L327; digest L195 | **refuted** (as an expectation; OK as a stretch target) | (i) No HA-VLN measurement exists. (ii) The lower end = best measured zero-contact K=1 SR on human-free, short-instruction R2R-CE (ETP-R1 + depth guard 50.1; proxy Score 42.9 with official CR, R/B2 L27). (iii) R/B2 L15: egocentric closed loop 0.25–0.40 SR; 0.45–0.60 only with an oracle collision layer. (iv) HA penalties: 41 % of shortest paths pass within 0.5 m of a person (digest L107); 112-word LLM text with ≥10–15 % corrupted route elements (digest L154-155); organizers' gap table shows −64 % to −86 % relative SR, R2R-CE → HA-VLN-CE (R/B2 L114, L193). (v) A7 scores the same class for rivals at 39.5/46.7 (R/A7 L87-88). (vi) The 46–55 conversion needs NE 3.6–4.3 m and 7–11 % colliding episodes (C9 `score.py`); at zero collisions SR .50→46 needs NE 7.0 and SR .60→55 needs NE 5.6. (vii) The range is narrower than the ±8 pp val→test band (R/C6 L46). (viii) SimpleVLN's 76.7 may be pass@4 (launcher default PASS_K=4, `X/ext/sota/SimpleVLN/eval/scripts/eval.sh` L2, L23; eval.py L631-653 reports both pass@4 and avg4; the README does not say which). | "Clean K=1 **planning target**: SR 0.50–0.60 (Score ≈ 46–55 at NE 3.6–4.3 m with 7–11 % colliding episodes). **Evidence-based expectation** before any HA-VLN measurement: SR ≈ 0.35–0.52 → Score ≈ 33–48 (central ≈ 42), plus a further ±6.5-Score val→test interval. Re-baseline after the M1 zero-shot measurement (Oct 27–30)." |
| 2 | Score 60–66 if K>1 is allowed | 01 L243; digest L195 | **refuted** (mis-sourced and overstated) | C9, the cited source, says **58–62** at SR 0.62–0.68 (R/C9 L262). 60–66 is C6's **dev** "gated K" figure (R/C6 L90); C6 says test = dev − 0…3 (L92). At realistic NE 3.8–4.0 m, Score 60 needs SR ≈ 0.645 and Score 66 needs SR ≈ 0.72. L7's own range 0.58–0.70 (01 L353) maps to ≈ 54–65. The best measured K>1 analogue (human-free, 3 depth-guarded agents, first contact-free tape) is 62.4 % → Score ≈ 58.6 (R/C8 L28). B10 puts all gray levers at +3–8 SR (R/B10 L9). | "If multi-rollout selection is permitted: +5 to +10 Score over K=1 (C9 test basis: SR 0.62–0.68 → 58–62 **if** K=1 reaches its target; ≈ 45–58 from the evidence-based K=1 expectation)." |
| 3 | "Clean configuration ≈ Score 40–50" | 01 L45 | **holds** (most defensible number in the package) but **contradicts** L243, L351 | Consistent with the human-free measured anchor (42.9–43.5) plus unmeasured gains. At zero collisions, Score 40 ↔ SR ≈ 0.40–0.43; the L351 SR 0.50–0.62 band cannot give < 46.7 at CR=0 even at NE 6 m. | Keep "≈ 33–48 (central ≈ 42)" or "40–50", and make §6/§12 match. |
| 4 | "Gray levers approved ≈ 50–65" | 01 L45 | **overstated** | The K>1-only gain on a consistent basis is +6–10 (see #2). Adding sibling and pre-exploration levers relies on discrete-era magnitudes (see #20). With the evidence-based K=1 of 33–48, the result is ≈ 40–58. | "≈ 45–60 if all gray levers are approved (non-additive)". |
| 5 | "A compliant agent … targets SR 0.50–0.65, NE 2–3 m, CR≈TCR≈0 → Score 50–65" | 01 L46 | **refuted** | NE 2–3 m is infeasible at SR 0.50–0.65 with zero collisions: NE ≥ 3(1−SR) + SR·d_s; SR .50 at NE 2 needs all failures at exactly 3 m and d_s = 1.0 m. Measured CE failures: median 7.4–8.7 m (R/B10 L57). Published R2R-CE agents at SR .54–.70: NE 3.74–5.22 (R/B2 L21-31; facts 17-29). Formula at NE 2–3 gives 50.0–64.0, not 65. With NE = SR·1.5 + (1−SR)·(7.5–8.7) the result is **47.4–61.1**. "CR≈TCR≈0" contradicts the 7–11 % colliding episodes behind L243 and C6's "TCR = 0 likely unattainable" (R/C6 L549). | "SR 0.50–0.65 at NE ≈ 3.8–4.8 m and ≈ 0–5 % colliding episodes → Score ≈ 46–61. This is the gray-lever (K>1) band, not the clean configuration." |
| 6 | "…would be first by a wide margin unless another team fields an offline privileged planner" | 01 L47 | **refuted** | A7's own compliant threats T6 (frontier-API + shield, 46.7, P 15–30 %) and T7 (51.8) overlap 46–55. In A7's MC, P(best rival ≥ 46) = 0.22 (`X/v1_review/mc.py`). | "…would likely finish top-3 and probably first; the expected margin over a well-built frontier-VLM + shield entry is 0–8 points." |
| 7 | "A compliant entry at Score ≥ 52 (SR ≥ .55, CR ≤ .1) wins about 85 % of the time" | 01 L316-317; digest L53; R/A7 L7 | **overstated** | Reproduced 0.867 from `X/A7_build.py` L197-211 (independent Bernoulli per class, Score × lognormal(0, 0.2)). Stress tests using only package numbers (`mc.py`): top-of-range probabilities and T8 not halved → **0.79**; rivals who build our architecture scored at our own projections (T5/T6 = 50.5, T7 = 60) → **0.77**; T8 at §8's "Med" (0.25) scoring 80 → **0.67**; σ = 0.3 → 0.83; combined → **0.63–0.68**. The parenthetical SR .55 / CR .1 does not give ≥ 52 unless NE ≤ ≈ 3.0–3.2 (A7's own T7 = 51.8; NE 4.4 → 50.0–50.5). One draw per class ignores several teams per class, and the team count is unknown (R/A7 §7). | "Under A7's **low-confidence** threat model, a test Score ≥ 52 beats the best rival ≈ 85 % of the time. Alternative inputs from this package give 63–79 % (≈ 67 % if a privileged-planner rival is as likely as §8 says). Because 52 lies in the upper half of our own K=1 target, our unconditional win probability is ≈ 55–70 %." |
| 8 | "Best rival's median Score ≈ 30, P(best rival ≥ 50) ≈ 0.16" | 01 L316; R/A7 L93 | **holds** (arithmetic) / **overstated** (certainty) | Reproduced: median 30.1, P(≥50) 0.159. Across the variants above: median 30–44, P(≥50) 0.16–0.40. | Add "(inference, low confidence; 0.16–0.40 under alternative inputs)". |
| 9 | "Each +0.01 SR adds ≈ 0.74 Score" | 01 L317; R/A7 L95 | **overstated / inconsistent** | 0.744 is the partial derivative at SR .40 / NE 4.5 / CR .2 / TCR .5, not at the Score-52 point. There the partial is 0.77–0.80; adding the accompanying NE drop gives ≈ 0.87 (`calc.py`). §0.1 L14 says 0.8; C9 says 0.77 (R/C9 L328). | "+0.01 SR ≈ +0.8 Score (≈ +0.87 including the NE improvement of the converted episode)." |
| 10 | Rival table: 13 / 18 / 23 / 32 / 40 / 47 / 52 / 66–90 | 01 L308-314 | **holds** (reproduces R/A7 L82-91: 13.0/18.0/22.6/31.7/39.5/46.7/51.8/66.5) except the last row | "66–90" for a privileged planner conflicts with 75–90 (L47, L74, L277), 75–95 (L106) and 80–87 (L206). | Use one range everywhere (see #21). |
| 11 | Published HA-VLN-CE SOTA SR 0.17–0.24; HCSG ≈ 23, BEVBert ≈ 19, ETPNav ≈ 17, CMA 12.95 | 01 L45, L302 | **holds** (comparable protocol; HCSG NE assumed 5.3, ±3 Score per R/A7 §3) | It omits DyGeoVLN's SR 0.40 (Score 33.7) and its VLA rows (StreamVLN .33, NaVILA .32, NaVid .34, Uni-NaVid .32), all with doubtful comparability (R/B2 L51, L118). This matters for how weak the field really is. | "…0.17–0.24 under the organizers' protocol; a 2026 paper reports 0.32–0.40 for VLA agents under a non-comparable collision count." |
| 12 | One SR point = 0.8 Score | 01 L14 | **holds** (partial derivative at zero collisions; 0.75–0.80 elsewhere) | `calc.py`; landscape L151-154. | — |
| 13 | 0.1 m of NE ≈ 0.2–0.3 Score | 01 L14 | **overstated** | 60/(3+NE)² per m: 0.235 at NE 2, 0.167 at NE 3, **0.10–0.13 at NE 3.6–4.5** (our K=1 regime); the landscape says "≈0.2 at NE ~1–2 m" (S/benchmarks/score_landscape.md L156). 0.3 needs NE ≈ 1.5 m (Track B or oracle only). | "0.1 m of NE ≈ 0.1–0.15 Score at NE 3.5–4.5 m (≈ 0.24 at NE 2 m)." |
| 14 | Every 0.01 of collision rate costs ≈ 0.2 | 01 L15 | **holds approximately** (incomplete) | Social-term cost per +0.01 CR & TCR = 0.14–0.16 at Nav ≈ 0.5 and 0.23 at Nav 0.8; ×1.19 under official CR normalisation. It omits the larger loss: a colliding episode cannot succeed (up to −0.8 per 0.01 if it would have succeeded). | "…≈ 0.15–0.25 through the Social term, plus up to 0.8 per 0.01 if those episodes would otherwise have succeeded." |
| 15 | Collision-free execution is a 30 % multiplier | 01 L15 | **holds** | Social factor 0.70–1.00 (≤ 30 % of Score at stake; ≤ 1.43× gain). | — |
| 16 | "Social = 1 exactly when the tape has zero navmesh contacts"; CMA loses ~15 steps/episode; Score 12.9 | 01 L12-13 | **holds** (minor imprecision) | Social = 1 iff contacts ≤ collision_num (non-zero for 7 % of test episodes). TCR 13.7/17.5; Score 12.945. | "…zero contacts beyond the per-episode allowance." |
| 17 | "38–57 % of successful R2R-CE episodes contain wall contact" | 01 L37 | **holds** | vln-safe README L10-12: 38.5–56.8 % (`X/ext/sota/vln-safe/README.md`); R/B2 L21-25. | — |
| 18 | "a training-free collision guard recovers 7–29 SR points under blocking" | 01 L38 | **overstated** (wrong regime) | HA-VLN scores with sliding (ALLOW_SLIDING True). vln-safe: under blocking +6.9–29.3 SR, but **under sliding SR unchanged and collision-free success +4.1–12.4** (vln-safe README L19-21). B2 Table A: +8.1 to +12.4 (R/B2 L27-29). | "…raises collision-free success by 4–12 points under the sliding physics the challenge uses." |
| 19 | Sibling instructions: "expected gain several SR points"; "≈ +5" Score | 01 L43, L90; R/C3 L355, L778 | **overstated** | +6–7 SR is from 2021 discrete rankers (B4). On modern CE agents B10 measured **+2.0–2.3 SR** (≈ +1.6–2.0 Score) because sibling failures are correlated (R/B10 L9, L57; digest L147-148). | "≈ +2 SR (+1.5–2 Score) measured on CE agents; up to +5 SR only with a learned selector." |
| 20 | Gray levers: multi-rollout ≈ +9–15 Score; pre-exploration ≈ +8–14 | 01 L89-90; R/C3 L778 | **overstated** | Derived from 2018–2020 discrete beam search (+11–19 SR, "gains shrink as base strengthens", R/B10 fact 21). Package K>1 estimates on CE: L5→L7 +8 SR (≈ +7 Score, 01 L351-353); C9 +8–12 SR (L53 vs L262); C8 +7–10 SR; B10 all gray levers +3–8 SR. | "multi-rollout selection ≈ +5–10 Score; pre-exploration unmeasured (historically +8–14 on discrete R2R)." |
| 21 | Privileged offline planner Score 75–90 (rival and our Track B) | 01 L47, L74, L106 (75–95), L206 (80–87), L277, L314 (66–90) | **overstated / inconsistent** | Goal top-1 78–92 % at zero collisions → 73–87 (`calc.py`); B1 76.5/81.6/86.8 at 80/85/90 % (digest L81); C8 77.6–84.8 with "~77" for own-instruction (digest L190-191). ≥ 88 % needs the original R2R text (a red line). 95 = oracle goal, not a planner. A7's rival T8 = 66.5. | "≈ 75–85 (goal top-1 80–90 %); a rival's weaker privileged planner ≈ 65–80." |
| 22 | Oracle-goal, zero-collision tape ≈ 95 | 01 L49 | **holds** | SR .97/NE .5 → 94.7; SR .98/NE .3 → 96.6; C6 93–96; C8 97.0. | — |
| 23 | vln-safe numbers: ETP-R1 37.7 (raw 64.6), StreamVLN 34.4, ETPNav 34.0, OmniNav 29.1, CMA 17.8; depth guard 50.1; oracle guard 61.3 | 01 L165-168 | **holds** | R/B2 L21-30; R/C9 fact 8. All are **human-free, short-instruction** numbers and must not be read as HA-VLN SRs. | Add "(human-free R2R-CE; no HA-VLN equivalent measured)". |
| 24 | First contact-free run among three guarded agents → 62.4 %; union 87 % vs best single 67.5 % | 01 L169-170 | **holds** | R/C8 L28 (depth guards, human-free, K=3 = gray); R/B10 L61 (0.872 / 0.675). | Label 62.4 % as a K>1 (gray) human-free number. |
| 25 | SimpleVLN 76.3/76.7/74.4 SR on R2R-CE | 01 L156-158 | **holds** (README) / **unverified semantics** | eval.sh defaults to PASS_K=4 and the summary reports both `pass@4` and `avg4`; the README does not state which. C8 L132 says "mean over 4"; C9 L292 says "pass@4 in the launcher"; B10 L174 says pass@k is unmeasured. Evaluated at 640×480 on Habitat 0.3.3, without collision accounting. | "…(pass@4 vs mean unverified; 640×480; collisions not counted)." |
| 26 | Instruction voting +6–7 SR; 51 % agree → 89.7 % vs 34.8 % | 01 L175-177 | **holds** (historical, discrete) | R/B4; the CE analogue is +2–2.3 (see #19). | Add "(discrete 2021 rankers; CE ≈ +2)". |
| 27 | Most-covered candidate stop succeeds 41.6 % (CMA: 12.9) | 01 L178-179 | **overstated** (misleading comparison) | It is an offline, nav-graph (privileged at inference) geometric baseline compared with a closed-loop CMA SR. B12's equivalent is SR 0.437 / Score ≈ 42 "offline-only" (digest L132). It is not evidence for Track A. | Move it to Track B or mark it "privileged, offline". |
| 28 | One success = 0.0235 Score; extra collision in a failed episode 0.004–0.007; attempt if P(contact) < ~0.8 | 01 L183-184 | **holds / holds / overstated** | 80/3408 = 0.02347. First collision in a failed episode at Nav 0.45–0.75 costs 0.0045–0.0076. Break-even p* = 4.7q/(1+4.7q), with q = P(success \| contact-free pass): 0.82 at q=1, 0.70 at q=0.5. | "…attempt it if P(contact) < 0.7–0.8 (depending on P(success) once past)." |
| 29 | RL gives +7–10 SR (SimpleVLN) | 01 L188 | **holds** | SimpleVLN README: +7.5–10.2 on R2R-CE. | — |
| 30 | W2 DoD: compliant executor + GT goal SR ≥ 0.90 → 0.94, contact episodes ≤ 1 % | 01 L219; briefs/W2 L28 | **overstated** (as a DoD) | No precedent: the vln-safe navmesh-**oracle** guard still leaves 5.9–7.8 % contact episodes (R/B2 L30-31), and the GT-goal ShortestPathFollower collides in 18–26 % (digest L41-42). C6 sets ≤ 3 % → ≤ 1 % (R/C6 L171). | "Contact episodes ≤ 3 % (gate), ≤ 1 % (stretch)." |
| 31 | W4: val clean SR ≥ 0.40 by Nov 9, ≥ 0.46 by Nov 16, ≥ 0.50 at freeze | 01 L221 | **refuted as consistent plan** (three versions) | briefs/W4 L22-23: SR ≥ 0.30 / TCR ≤ 0.05 on Nov 3; SR ≥ 0.45 / TCR ≤ 0.02 on Nov 13. R/C8 L437: A-ST ≥ 0.50 by Nov 8. §6 G5–G7 give *test* numbers with TCR 0.15–1.2 (C9). | One milestone table with basis (val/test), SR, colliding-episode share and TCR. |
| 32 | W5: +3–5 SR from allowed levers | 01 L222 | **holds** (vs C8 A3 +2–5) / **inconsistent** with B10 (test-time compliant components +2–4, +1–3, +1–3, +1–4, digest L149-150) | — | State which levers are counted. |
| 33 | W6: every ZIP PASS + TCR 0 on all regimes | 01 L223; briefs/W6 | **refuted** (contradicts the plan's own projections) | C6 flags TCR 0 as "likely unattainable" (R/C6 L549); the 46–55 range assumes 7–11 % colliding episodes. | "TCR ≤ 0.02 and colliding episodes ≤ 3 % on all regimes; zero = stretch." |
| 34 | STOP-only predicted Score 8.473053 (Euclidean); CR 0.684 vs 0.593 | 01 L239 | **holds** | 80·63/1839 + 60/(3+7.46676) = 8.4731; 0.684·1593/1839 = 0.5925. | — |
| 35 | G5 SR .28–.36 → 25–32; G6 .40–.47 → 36–43; G7 .46–.54 → 42–50 | 01 L241-243 | **holds** (arithmetic, given C9's unstated assumptions) | Reproduced 25.1–32.0 / 36.4–43.0 / 42.2–49.9 with NE 6.0→4.0 and colliding share 35 %→9 % (`X/work/c9/score.py`). At zero collisions G5's SRs would give 29.9–40.8. These assumptions conflict with briefs/W4 (TCR ≤ 0.05 on Nov 3, ≤ 0.02 on Nov 13). The SR levels inherit #1's evidence problem. | Print the NE / colliding-share / TCR assumptions next to each gate. |
| 36 | L5 clean SR 0.50–0.62; L6 0.72–0.85 at K=8; L7 0.58–0.70 | 01 L351-353; R/C6 L85-87, L171-173 | **refuted / overstated / overstated** | L5: see #1 (C6 rates its own evidence "medium-low", L171). L6: human-free 3-agent contact-free union = 73.4 % (R/C8 L28), so 0.85 on HA-VLN exceeds the human-free measurement. L7: ≥ human-free measured 62.4 %. | L5 "0.35–0.52 expected, 0.50–0.62 target"; L6 "0.60–0.75"; L7 "0.45–0.62". |

---

## 3. Internal inconsistencies (exact references)

**A. The same quantity with different values**

1. **K=1 clean Score.** Six values for one quantity:
   - 40–50 (01-strategy.md L45);
   - "50–65" for "a compliant agent built as below" (L46);
   - 46–55 test (L243, from R/C9 L53);
   - 53–60 dev (R/C6 L89; implied by 01 L351's SR 0.50–0.62);
   - 52–63 (R/C8 L30; digest L188);
   - 53 for the best single backbone after RL (R/A6 L300).

   B2's ceiling, 0.25–0.40 SR for egocentric closed loop (R/B2 L15), implies ≈ 22–37.
2. **K>1 Score.** 50–65 (L45); 60–66 (L243 and digest L195, attributed to C9); **58–62 in C9 itself** (R/C9 L262); 60–66 dev
   (R/C6 L90); 62–71 (R/C8 L30; digest L189); L7 SR 0.58–0.70 → ≈ 54–65 at realistic NE (01 L353).
3. **K>1 uplift.** +9–15 Score (L89; R/C3 L778) vs +6.4–7.5 (L351→L353) vs +7–12 (C9 L53→L262) vs +3–8 SR for all gray levers (R/B10 L9)
   vs +11–14 implied by L243, which mixes a test basis with a dev basis.
4. **Sibling-instruction gain.** "several SR points" (L43) and "≈ +5" Score (L90; R/C3 L355) vs measured +2.0–2.3 SR on CE agents
   (R/B10 L9, L57; digest L147-148).
5. **Privileged-planner Score.** 75–90 (L47, L74, L277); 75–95 (L106); ~80–87 (L206); 66–90 (L314); 66.5 (rival T8, R/A7 L91);
   76.5–86.8 (digest L81); 77.6–84.8 (R/C8 L98-109; digest L190-191 "~77" with own instruction).
6. **Track B goal accuracy.** 85 % (78–90) from HA-R2R text (L205) vs 78–86 % (digest L190, C8).
7. **Value of one SR point.** 0.8 (L14) vs 0.74 (L317; R/A7 L95) vs 0.77 (R/C9 L328) vs 0.75–0.85 (R/B10 L13). The total derivative
   including the NE coupling is ≈ 0.87.
8. **Value of 0.1 m of NE.** 0.2–0.3 (L14) vs 0.10 (R/A7 L95) vs 0.125 (R/C9 L328, 1.25 per m). It is 0.10–0.13 at the NE our own plan implies.
9. **Collision level of the final K=1 tape.** ≈ 0 (L46) / TCR 0 on all regimes (L223, briefs/W6) / ≤ 1 % contact episodes (L219, GT-goal
   executor) / ≤ 3 % contact (R/C6 L171) / 7–11 % colliding episodes (the basis of L243, `X/work/c9/score.py`) / TCR ≤ 0.02
   (briefs/W4 L23).
10. **Same SR, different Score.** SR 0.50–0.62 ↔ dev Score 53.5–59.9 in C6 (NE 2.6–3.0, 2–3 % contact; R/C6 L180-186). SR 0.50–0.60 ↔ test
    Score 46.1–55.5 in C9 (NE 3.6–4.3, 7–11 %). 01 L351 quotes C6's SR and L243 quotes C9's Score.
11. **Likelihood that a rival fields a privileged planner.** "Med" (L277) vs 3–8 % (R/A7 L104) vs 2.75 % in the MC (`X/A7_build.py` L199).
    It drives the 85 % (see claim #7).
12. **The same architecture class scored for us and for rivals.** Rivals: fine-tuned VLA + guard 40, frontier-API + guard 47 (L311-312;
    R/A7 L87-88). Us, with the same classes plus a frontier System 2: 46–55 (L243).
13. **Milestones.** L221 (val ≥ 0.40 Nov 9, ≥ 0.46 Nov 16, ≥ 0.50 at freeze) vs briefs/W4 L22-23 (≥ 0.30 Nov 3, ≥ 0.45 Nov 13; TCR ≤ 0.05 /
    0.02) vs R/C8 L437 (≥ 0.50 by Nov 8) vs §6 L241-243 (test SR 0.28–0.36 Nov 2–6 with TCR 0.8–1.2 per C9).
14. **Penalty if test-scan human placements are missing.** −0.05–0.12 SR (R/C9 L58) vs −10 to −30 points (R/C8 L275). No headline range is
    conditioned on it, although §8 rates the risk "Med" (L276) and A6 assumes the placements are available (R/A6 L296).
15. **Single-system SR precision.** ±2.8 pp at 95 % (L356; R/C6 L44) vs SE 1.6 pp, i.e. ±3.1 pp (digest L151).
16. **Test count.** "13 passing" (01 L5; briefs/W6 L14) vs "15 tests" (01 L332) vs 20 (README L12; digest L198). The actual count is 20
    `test_` functions.

**B. SR→Score conversions that do not match 80·SR + 60/(3+NE) at the stated or implied collision level**

17. L46: SR 0.50–0.65 at NE 2–3 m and CR≈0 gives **50.0–64.0**, not 50–65 (65 needs NE 1.62 m). The NE itself is infeasible (claim #5).
18. L45: "Clean ≈ 40–50" is incompatible with L351's clean SR 0.50–0.62 at CR≈0. The minimum is 46.7, even at NE 6 m.
19. L243: SR 0.50 → 46 needs NE 7.0 m and SR 0.60 → 55 needs NE 5.57 m at zero collisions. The range is reachable only with C9's unstated
    7–11 % colliding episodes, which contradicts L46 and L223.
20. L243: "60–66 if K>1" needs SR 0.625–0.70 at NE 3 m (0.645–0.72 at realistic NE 3.8–4.0 m). L353's L7 lower end, 0.58, gives at most
    56.4 even at NE 3 m.
21. L241 (G5): at zero collisions SR 0.28–0.36 gives 29.9–40.8 (NE 2–6). The 25–32 range implies 28–35 % colliding episodes and TCR
    0.8–1.2, which contradicts briefs/W4 L22 (TCR ≤ 0.05 on Nov 3).
22. L316: "Score ≥ 52 (SR ≥ .55, CR ≤ .1)". SR .55 with CR .10 reaches 52 only at NE ≤ 3.0–3.2 m. A7's own row with these values (T7, NE 3.2,
    TCR .2) gives 51.8 (R/A7 L90). With official CR normalisation and NE 4.4 m it gives ≈ 50.0.
23. A7 recommendation (R/A7 L109): "Score ≥ 50 on val_unseen (SR ≥ .55, NE ≤ 3.3, CR ≤ .10, TCR ≤ .2)" gives 51.7. That is fine, but it
    sets a **val** bar while the threat matrix is **test**.
24. Digest L149-150 (B10): the components "+2–4, +1–3, +1–3, +1–4" sum to +5–14 but are labelled "≈ +8–18 SR total". The +8–18 in
    R/B10 L9, L13 includes the training levers (DAgger, RL, augmentation).
25. Digest L195 attributes "60–66 if K>1 allowed" to C9, which says 58–62 (R/C9 L262).

**C. Evidence misapplied to the scored regime**

26. L38: the vln-safe guard gain "7–29 SR under blocking" applies to the blocking regime. The challenge uses sliding, where the gain is
    +4.1–12.4 collision-free success (vln-safe README L19-21).
27. L165-171 and L351: human-free, short-instruction R2R-CE measurements anchor HA-VLN expectations without any HA-specific discount being
    shown. The only numbers on record for the HA-specific penalties are: −64 % to −86 % relative SR drop (organizers, R/B2 L114, L193);
    "up to 25 %" SR from removing human text (R/B2 L114); 38 % of routes within 0.3 m of a human (R/C8 L80).
28. L156-158: SimpleVLN's headline SR may be pass@4 (see claim #25); every downstream K=1 chain (R/C8 L132 "0.60–0.72 raw after HA
    fine-tune"; R/A6 L300 "0.40 zero-shot") starts from it.

---

## 4. Reproduction notes

- Win-probability replica (`X/v1_review/mc.py`, 200k draws, seed 0). The script reports P(win | 52), P(win | 46), the median and
  P(≥50) for each variant:
  - V0 (A7 as published): P(win | 52) 0.867; P(win | 46) 0.780; median 30.1; P(≥50) 0.159.
  - V1 (top-of-range probabilities, T8 not halved): 0.789.
  - V2 (rivals symmetric with our projections): 0.774.
  - V3 (T8 "Med" = 0.25 at Score 80): 0.671.
  - V4 (σ 0.3): 0.834.
  - V5 (V1 + V2): 0.677.
  - V6 (V5 with T8 0.15): 0.632.

  Unconditional P(win):
  - our Score ~ U(46, 55) (the package's own K=1 band): 0.845 (V0) / 0.650 (V5);
  - our Score ~ N(43, 7) (this review's band): 0.724 (V0) / 0.537 (V5).

  V0 contributions to P(best rival ≥ 52): T6 0.065, T7 0.037, T8 0.025, T5 0.013, others ≈ 0.
- Corrected K=1 band (`X/v1_review/corr.py`). Assumptions: NE = SR·1.5 + (1−SR)·8.0, colliding share 12 % → 6 %, official CR
  normalisation. Results: SR .35 → 33.2; .43 → 40.0; .45 → 41.8; .50 → 46.1; .52 → 47.8; .55 → 50.7; .62 → 57.0; .65 → 59.8.
- Human-free measured anchors converted to challenge Score: ETP-R1 + depth guard (K=1) 42.9 (official CR) / 43.5 (raw CR); 3-agent
  first-contact-free (K=3, gray) ≈ 58.6 at zero contacts.
- Confidence: the arithmetic findings (§3B, claims #5, #9, #13, #22) are high. That the ranges are optimistic is medium-high: every anchor
  is from human-free R2R-CE, and no HA-VLN measurement exists for any option. The corrected central value (≈ 42) is itself an
  inference (low–medium) and should be replaced by the first measurement on val_unseen.
