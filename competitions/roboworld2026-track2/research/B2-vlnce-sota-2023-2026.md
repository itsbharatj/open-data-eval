# VLN-CE (R2R-CE) state of the art 2023-2026 and its transfer to HA-VLN 2.0 / HA-R2R-CE

Topic id: `B2-vlnce-sota-2023-2026`

## Summary

Standard R2R-CE val-unseen SR climbed from ~57-61 (graph/waypoint agents ETPNav 57.2, BEVBert 59, HNR 61, ENP 58, g3D-LF 61; all Habitat 0.1.7, all using the CWP depth-panorama waypoint predictor) to 65-68 for RL-tuned graph agents (ETP-R1 65.3, macro-action closed-loop RL 68.1) and to 70-77 for native-MLLM policies in 2026 (GroundingVLN 69.9, ABot-N1 70.9, Qwen-RobotNav-8B 72.1, Nav-R1 72.5, Efficient-VLN 73.2, SimpleVLN Qwen3.5-9B 76.7/72.6 SPL). Only SimpleVLN (HF weights, Habitat 0.3.3 + vLLM), ETP-R1 (ckpts, Habitat 0.1.7), StreamVLN/JanusVLN/MemoryVLN (Habitat 0.2.4), InternVLA-N1/DualVLN (64.3) and the 0.1.7 graph family have usable public code+weights; Qwen-RobotNav, ABot, OmniNav, Efficient-VLN, GroundingVLN (empty repo) do not. On HA-VLN-CE the picture is radically different because SR there requires success AND zero (baseline-adjusted) collisions: HA-VLN 2.0 reports retrained BEVBert 0.21 / ETPNav 0.17 val-unseen SR (zero-shot 0.15 / 0.08; i.e. -64% to -86% vs their R2R-CE SR), the organizers' CMA baseline scores 0.129 SR / Score 12.9, and the only third-party method (HCSG, May 2026) reaches 0.24 SR / CR 0.36. The dominant loss is the collision-free criterion (38-57% of 'successful' R2R-CE episodes contain contact under sliding), then the human obstacles, then the 112-word LLM-rewritten instructions. ETPNav's R2R-CE sensor rig (12x RGB 224x224 HFOV 90 + 12x depth 256x256) is identical to the HA-VLN task config, so the 0.1.7 graph family ports with minimal change, but its default eval teleports on backtracking (back_algo: teleport) and relies on sliding, both of which must be replaced by replayable MOVE_FORWARD/TURN control for the challenge. Realistic closed-loop (egocentric) ceilings on HA-R2R test by Nov 30: ~0.25-0.40 SR without HA-R2R fine-tuning (modern VLA + collision guard), ~0.45-0.60 with fine-tuning/RL on collision-free HA-R2R experts; a privileged offline-replay planner with perfect goal knowledge gets SR ~0.97-1.0 (Score ~94-97), and with LLM/VLM goal inference on privileged renders ~0.75-0.90, so goal inference accuracy, not control, decides the leaderboard.

## Facts (verified unless marked)

1. **[high]** ETPNav (TPAMI 2024) R2R-CE: val seen TL 11.78 NE 3.95 OSR 72 SR 66 SPL 59; val unseen TL 11.99 NE 4.71 OSR 65 SR 57 (57.21) SPL 49 (49.15); test unseen TL 12.87 NE 5.12 OSR 63 SR 55 SPL 48.  
   _Evidence:_ ENP paper table (arxiv 2410.14250) and peer-observation paper reproduction (arxiv 2603.20804); ETPNav paper 2304.03047.
2. **[high (val) / medium (test)]** BEVBert-CE (ICCV 2023) R2R-CE val unseen NE 4.57 OSR 67 SR 59 SPL 50 (test unseen approx NE 4.70 OSR 67 SR 59 SPL 50).  
   _Evidence:_ SeekVLN table (arxiv 2609.37353) and SOTA2 leaderboard page agree on val unseen; test row from memory/one source only.
3. **[high]** HNR (CVPR 2024 highlight) R2R-CE val unseen NE 4.42 OSR 67 SR 61 SPL 51 (another table: 4.42/67.4/60.7/51.3); test unseen = ETPNav +3 SR +2 SPL => SR 58 SPL 50. Lookahead fine-tuning code was never released (superseded by g3D-LF).  
   _Evidence:_ VIL paper table (arxiv 2507.08831), second 2026 table, HNR paper text; HNR-VLN README TODOs struck through.
4. **[high (val) / medium (test)]** ENP (NeurIPS 2024, energy-based policy on ETPNav) val unseen NE 4.69 OSR 65 SR 58 SPL 50; test unseen +1 OSR +1 SR over ETPNav (SR 56). Code: github.com/DefaultRui/VLN-ENP (clone failed here).  
   _Evidence:_ arxiv 2410.14250 table + text.
5. **[medium-high]** g3D-LF (CVPR 2025): panorama setting val unseen NE 4.53 OSR 68.0 SR 61.0 SPL 52.0; monocular setting val unseen NE 5.70 OSR 59.5 SR 47.2 SPL 34.6, test 6.00/57.5/46.3/32.2. Code + ckpts on HF (MrZihan/g3D-LF), Habitat 0.1.7, needs torch_kdtree + tiny-cuda-nn.  
   _Evidence:_ DyGeoVLN table (2603.21269), Dynam3D table, CVPR paper snippet; README in ext/sota/g3D-LF.
6. **[high]** Sim2Real-VLN-3DFF (CoRL 2024, monocular ETPNav + 3D feature fields): val unseen NE 5.95 OSR 55.8 SR 44.9 SPL 30.4; test 6.24/54.4/43.7/28.9. Known multi-GPU eval bug: a user got SR 33.5/SPL 22.9; authors say evaluate with GPU_NUMBERS=1, NUM_ENVIRONMENTS=1.  
   _Evidence:_ arxiv 2406.09798 ablation + Dynam3D table; GitHub issue #3 (fetched).
7. **[high]** Dynam3D (NeurIPS 2025 oral, monocular 3D-VLM on llava-phi-3-mini): val unseen NE 5.34 OSR 62.1 SR 52.9 SPL 45.7; test NE 5.53 OSR 60.4 SR 51.4 SPL 44.8. Pretraining code/ckpts released, VLN checkpoints NOT released (README TODO unchecked). Habitat 0.1.7, py3.8.  
   _Evidence:_ DyGeoVLN table + Dynam3D paper table; ext/sota/Dynam3D/README.md.
8. **[medium]** NavMorph (ICCV 2025 world model): monocular variant (on VLN-3DFF) R2R-CE val unseen ~47.9 SR / 33.2 SPL; panoramic (ETPNav base) ~58-59 SR / 49-50 SPL ('58.02/48.98' in paper text; CompactNav table 66 OSR/59 SR/50 SPL). Code+ckpt on Google Drive; README says Habitat v0.2.1 (but still uses CWP hfov90 predictor).  
   _Evidence:_ NaVIDA table (2601.18188), CompactNav (2607.23181), NavMorph arXiv HTML; ext/sota/NavMorph/README.md.
9. **[high]** NaVid (RSS 2024): paper val unseen NE 5.47 OSR 49.1 SR 37.4 SPL 35.9; released ckpt (trained with Uni-NaVid recipe) 5.65/49.2/41.9/36.5; eval.ai test 5.39/52/45/39. Uni-NaVid (RSS 2025): paper 5.58/53.3/47.0/42.7; released ckpt 4.96/57.4/51.8/47.7. Both Habitat 0.1.7 py3.8; NaVid eval 1839 eps in 2.5 h on 8xA100; Uni-NaVid ~5 Hz on one A100; NaVid per-step 0.87-2.72 s depending on tokens/frame.  
   _Evidence:_ ext/sota/NaVid-VLN-CE/README.md, ext/sota/Uni-NaVid/README.md, NaVid paper.
10. **[high]** NaVILA (RSS 2025, VILA/LLaMA3-8B): val unseen NE 5.22 OSR 62.5 SR 54.0 SPL 49.0; eval needs Habitat 0.1.7 built from source under py3.10; ~0.6 s VLA inference per step (FP16 594.58 ms), ~1 s/action on Go2; 56.84 s/episode measured on RTX 4090 by GroundingVLN.  
   _Evidence:_ SimpleVLN/VLN-Cache tables; NaVILA README; NaVILA appendix; GroundingVLN paper.
11. **[high]** StreamVLN (ICRA 2026, LLaVA-Video 7B): paper val unseen NE 4.98 OSR 64.2 SR 56.9 SPL 51.9; v1-3-trained ckpt 4.90/63.6/56.4/50.2; 0.27 s latency per 4-action chunk on Go2; Habitat 0.2.4; code, DAgger collection, ScaleVLN-150k VLN-CE conversion and ckpts released.  
   _Evidence:_ ext/sota/StreamVLN/README.md; streamvln.github.io.
12. **[high]** VLN-R1 (Qwen2-VL-7B, GRPO): R2R-CE val unseen SR 30.2 SPL 21.8; 2B-RFT beats 7B-SFT; data (VLN-Ego) released, SFT/RFT/test engine still 'in progress' in Qi-Zhangyang/GPT4Scene repo.  
   _Evidence:_ arxiv 2506.17221; ext/sota/GPT4Scene/README.md status table.
13. **[medium]** MapNav (annotated semantic map memory for VLM): R2R-CE val unseen 5.92/50.3/36.5/34.3 (current RGB+ASM) or 5.43/53.0/39.7/37.2 (+2 history frames); per-step 1.22 s -> 0.25 s; code 'to be released' (not found).  
   _Evidence:_ arxiv 2502.13451 table; HSGM citation.
14. **[medium]** OVER-NAV (CVPR 2024) targets Iterative VLN (IR2R / IR2R-CE), reporting +4/+3 t-nDTW over MAP-CMA; it is not a standard R2R-CE agent and no code was found.  
   _Evidence:_ CVPR 2024 paper text via search.
15. **[high]** UniWM (ECCV 2026, 'Unified World Models') is by the HA-VLN organizers' group (Yifei Dong, Fengyi Wu, Zhi-Qi Cheng, Hauptmann; repo F1y1113/UniWM, same account as the HA-VLN HF dataset); evaluated on Go Stanford/ReCon/SCAND/HuRoN, not R2R-CE.  
   _Evidence:_ ext/sota/UniWM/README.md author list and HA-VLN cross-link; arxiv 2510.08713.
16. **[high]** NavDP (ICRA 2026) is a point/image-goal diffusion policy (no language). Used as System-1 of InternVLA-N1: R2R-CE val unseen dual-system w/ NavDP* 4.22/70.4/64.1/58.1; DualVLN (ICLR 2026, RGB only) 4.05/70.7/64.3/58.5; System-2 + ShortestPathFollower 4.25/68.3/60.9/55.2; weights on HF (InternRobotics/*).  
   _Evidence:_ ext/sota/InternNav/README.md results tables; ext/sota/NavDP/README.md.
17. **[high]** ETP-R1 (Dec 2025, graph-based + Gemini-annotated pretraining + GRPO): R2R-CE val unseen SFT SR 63.24 SPL 54.30; RFT SR 65.31 SPL 55.77 OSR 71.45; claims SOTA on all splits; full code + all ckpts (HF cepillarskeira/ETP-R1-extra-files); trained on 4xA6000; Habitat 0.1.7 py3.6 torch 1.9.1.  
   _Evidence:_ LCGNav table (2605.09053); ext/sota/ETP-R1/README.md.
18. **[medium]** Same group's 'Revisiting Topological Graphs for Macro Action based Closed-loop RL' (Sep 2026, 2609.03906): val unseen SR 65.1 -> 68.1, SPL 53.5 -> 57.3 via graph-PPO over frontier nodes with a training-free low-level controller; still depends on the waypoint predictor; code not found.  
   _Evidence:_ arxiv 2609.03906 abstract/intro.
19. **[high for README-sourced; medium for others]** 2026 native-MLLM frontier on R2R-CE val unseen: SimpleVLN Qwen3.5-9B RL 76.7 SR / 72.6 SPL (Qwen3.5-4B 76.3/72.3; Qwen3-VL-8B 74.4/69.5 with NE 2.93 OSR 79.2; pre-RL 9B 69.2/61.2; RL adds +7.5-10.2 SR); Efficient-VLN v2 (Qwen3-VL-8B) 73.2 SR, 159 ms/step on H200; Nav-R1 72.5/68.8; Qwen-RobotNav-8B 72.1/66.6 (panoramic, 15.6M samples); ABot-N1 70.89/67.5 (tri-view); GroundingVLN 69.9/64.1 (Qwen3.5-4B, 188K samples); OmniNav 69.5/66.1; ABot-N0 66.4/63.9; NavFoM 56.2/51.2 (single-view) / 61.7 (4-view); DualVLN 64.3/58.5; D3D-VLP 61.3/56.1; JanusVLN 52.8/49.2 (60.5/56.8 with 10.7M samples); AdaGeoVLN 55.7/51.4; MemoryVLN 54.76/50.26; FutureNav-8B 55.5/51.4; Goal2Pixel 54.1/52.5.  
   _Evidence:_ ext/sota/SimpleVLN/README.md, ext/sota/Qwen-RobotNav/README.md, ext/sota/MemVLN/README.md, arxiv 2512.10310v2, 2509.10884, 2607.10383, 2609.18581, 2512.12622, 2509.22548.
20. **[high]** Code/weights availability of the 2026 frontier: SimpleVLN = full weights on HF (honglyhly/SimpleVLN_*), eval via Habitat 0.3.3 + vLLM 0.18.0, annotations bundled; Nav-R1 = code + models on HF (eval script defaults to 50/100-episode subsets; a third-party review flagged real-world SR>1.0 anomalies); JanusVLN = code + ModelScope weights (Habitat 0.2.4); MemoryVLN = eval code only (Habitat 0.2.4); GroundingVLN repo contains only a LICENSE (as of 2026-10-24); Qwen-RobotNav: 'no plan to release model weights'; Efficient-VLN, ABot-N0/N1, OmniNav: no code found.  
   _Evidence:_ Local clones under ext/sota/*; README text.
21. **[medium]** Zero-shot/training-free R2R-CE val unseen SR (self-reported, protocols differ): HAM-VLN 61.0 (Jul 2026 preprint), SpaceVLN 53.3 (full 1,839 eps), HSGM 47.9/32.8 SPL (CVPR 2026, GPT-5), SparseNav 42.8/35.2, VLN-Zero 42.4/26.3, InstructNav 31.0, Open-Nav 19.0.  
   _Evidence:_ arxiv 2607.29600, 2606.08992, CVPR 2026 HSGM, 2609.26408, 2509.18592.
22. **[medium]** World-model VLN-CE line: NavMorph (ICCV25), SC2-WM (ICML 2026; +7.1% SR/+7.8% SPL relative on VLN-3DFF; reproduced ckpt SR ~49.4-51.0, SPL ~36.5-36.7; code+ckpt sunrise-yuze/SC2_WM), NavForesee, NavWM, FutureNav, WNM-3D, UniNav, MonoDream, VISTA; none exceeds the native-MLLM policies on R2R-CE.  
   _Evidence:_ arxiv 2608.07548 + GitHub issue #7; search results.
23. **[high]** Habitat versions: 0.1.7 = VLN-CE, ETPNav, BEVBert-CE, HNR, 3DFF, g3D-LF, Dynam3D, ETP-R1, V2-VLNCE/VIL, NaVid/Uni-NaVid eval, NaVILA eval (source build), HA-VLN 2.0 itself; 0.2.1 = NavMorph; 0.2.4 = StreamVLN, JanusVLN, MemoryVLN; 0.3.3 = SimpleVLN eval; Habitat 3.0 = DPed-VLN; Isaac Sim = NavDP/InternNav System-1 bench, AdaVLN, NaVILA-Bench.  
   _Evidence:_ READMEs in ext/sota/* and ext/HA-VLN/README.md.
24. **[high]** ETPNav's R2R-CE task config (ext/sota/ETPNav/habitat_extensions/config/r2r_vlnce.yaml) = RGB 224x224 HFOV 90, DEPTH 256x256 HFOV 90, FORWARD 0.25, TURN 15, ALLOW_SLIDING True, MAX_EPISODE_STEPS 20 (waypoint-level), actions [STOP, MOVE_FORWARD, TURN_LEFT, TURN_RIGHT, HIGHTOLOW]; at runtime it adds 12 cameras (30 deg apart) each 224x224 HFOV 90 for RGB and depth (ss_trainer_ETP.py L97-144). This is identical to HA-VLN's HAVLNCE_R2R_task.yaml sensor spec (RGB 224 HFOV 90, depth 256, 0.25 m / 15 deg, sliding on) except HA-VLN uses MAX_EPISODE_STEPS 500 at the primitive-action level.  
   _Evidence:_ Files read locally; ext/HA-VLN/HASimulator/config/HAVLNCE_R2R_task.yaml.
25. **[high]** The CWP waypoint predictor used by ETPNav/BEVBert/HNR/3DFF/g3D-LF/ETP-R1/NavMorph is depth-only (TRM_net.py: vis_x = depth_x), consumes 12 depth views, outputs a 120-angle x 12-distance heatmap (HEATMAP_OFFSET 5), weights 'check_cwp_bestdist_hfov90' for R2R (hfov63 for RxR); training code wz0919/waypoint-predictor.  
   _Evidence:_ ext/sota/ETPNav/vlnce_baselines/waypoint_pred/TRM_net.py; ss_trainer_ETP.py L199.
26. **[high]** ETPNav's low-level controller (vlnce_baselines/common/environments.py L363-470): single_step_control turns to the ghost node then issues int(dist//0.25) MOVE_FORWARDs; the 'tryout' obstacle-escape heuristic (random +-90 deg then a sweep of 6 headings) is only active when ALLOW_SLIDING is False; default R2R-CE eval uses back_algo: teleport, i.e. it TELEPORTS the agent to the front node when backtracking and to stop_pos at STOP (set_agent_state), which cannot be expressed as a replayable action sequence.  
   _Evidence:_ ext/sota/ETPNav/run_r2r/iter_train.yaml (back_algo: teleport, tryout: True); environments.py teleport().
27. **[high]** The HA-VLN repo contains no ETPNav/BEVBert integration code (only an install pointer to ETPNav in README); HA-VLN 2.0 paper results for those agents cannot be reproduced from the released repo.  
   _Evidence:_ grep of ext/HA-VLN, ext/havln2, ext/track2 for 'etpnav|bevbert' -> only README.md:253.
28. **[high]** HA-VLN 2.0 (arxiv 2503.14229, accepted IROS 2026) HA-VLN-CE SR (success AND collision-free): retrained BEVBert val seen 0.27 / val unseen 0.21; retrained ETPNav 0.24 / 0.17 (0.25 m step). Zero-shot (trained on VLN-CE only): BEVBert 0.19 / 0.15 (val unseen NE 6.10 TCR 5.72 CR 0.56); ETPNav val unseen NE 7.40 TCR 7.94 CR 0.71 SR 0.08. v1 'gap' table: ETPNav SR -70.2% (retrained) / -86.0% (zero-shot) vs VLN-CE; BEVBert -64.4% / -74.6% (arithmetically consistent with 0.57->0.17/0.08 and 0.59->0.21/0.15).  
   _Evidence:_ Three independent search extractions of 2503.14229 v1/v2/v3 text and tables; HCSG paper quoting 0.21/0.17.
29. **[medium-high]** HA-VLN 2.0 ablations: replacing humans with cylinders lowers TCR ~36% and raises SR ~10% relative (BEVBert 0.15->0.17, CR 0.56->0.46, TCR 5.72->5.11); removing human-interaction instruction enrichment lowers TCR up to 22% and raises SR up to 25%. HA-VLN-CMA-Base: val seen NE 7.63 TCR 63.09 CR 0.77 SR 0.05; val unseen NE 7.88 TCR 63.84 CR 0.75 SR 0.04. Full HA-VLN-CMA* (challenge baseline): val unseen SR 0.129 NE 6.387 CR 0.684 TCR 17.536 Score 12.945 (toolkit README) vs repo table SR 0.114 NE 6.502 CR 0.689 TCR 22.352 Score 11.94.  
   _Evidence:_ 2503.14229 Table 4 snippets; UWMILab/HA-VLN README (fetched); CONTEXT.md.
30. **[high]** HA-VLN 1.0 (NeurIPS 2024 D&B spotlight, discrete HA3D sim): even the best retrained agent reached at most 40% SR in unseen environments and human occupancy caused SR reductions of up to 65%.  
   _Evidence:_ arxiv 2406.19236 text via search.
31. **[high]** HCSG (arxiv 2605.13321, May 2026) is the only third-party method found on HA-VLN-CE: val unseen SR 0.24 vs BEVBert 0.21 / ETPNav 0.17; CR 0.36 (-34.5% vs BEVBert ~0.55, -37.9% vs ETPNav ~0.58); adds human pose/trajectory forecasting + VLM intent descriptions into a topological-map agent plus a social-distance loss; project page haoxuanxu1024.github.io/HCSG; code not confirmed.  
   _Evidence:_ arxiv 2605.13321 abstract/results via search.
32. **[high]** 'Successful but Unsafe' (arxiv 2610.14682, Oct 2026, code dinhieufam/vln-safe): across six published R2R-CE agents 38.5-56.8% of successful episodes contain contact under sliding; switching to blocking lowers SR by 11.7-36.1 pp; a training-free collision guard cuts collision steps 62-98% and raises SR 6.9-29.3 pp under blocking.  
   _Evidence:_ arxiv 2610.14682 abstract.
33. **[medium]** DPed-VLN (Sep 2026, Habitat 3.0, ORCA pedestrians, 33,093 episodes) LoRA-adapted NaVILA and StreamVLN; LoRA notably reduced StreamVLN's collision rate; code pending, dataset on Zenodo. AdaVLN (Isaac Sim, moving humans) exists but no baseline numbers retrieved.  
   _Evidence:_ ext/sota/DPedVLN/README.md; arxiv 2609.21504; 2411.18539.
34. **[high]** Graph-family compute: ETPNav-without-depth pretrain (100k steps) + finetune (15k iters) in <1 day on 2-4 RTX 3090; ETPNav-3DFF +4 days (25k iters); 3DFF eval of val unseen ~3 h (original ETPNav faster), <1 s per waypoint step on a 3090 (<2 s on GTX 1060), ~15 waypoint steps/episode. ETPNav official training uses 2 GPUs, batch 1 env; ckpts on ModelScope (admagic/ETPNav).  
   _Evidence:_ GitHub issue MrZihan/Sim2Real-VLN-3DFF#2 (fetched); ext/sota/ETPNav/README.md.
35. **[medium-high]** VLA latencies (different GPUs, not comparable): NaVid 0.87-2.72 s/step; Uni-NaVid 0.2 s (A100); NaVILA ~0.6 s; StreamVLN 0.27 s per 4-action chunk; VLN-Cache 637->419 ms; Efficient-VLN 898->159 ms/step (H200); NavJev 0.65 s; Qwen-RobotNav 196 ms (Jetson Thor); SimpleVLN latency table measured on A100 (vLLM-served). Efficient-VLN v1 trained in 282 H800 GPU-hours.  
   _Evidence:_ Papers/READMEs cited above.
36. **[medium-high]** HA-R2R uses all 16,844 VLN-CE episodes (10,819/778/1,839/3,408). VLN-CE's 4,475 trajectories were produced by converting R2R nav-graph paths to Habitat navmesh paths and keeping only navigable ones, so every episode has a navigable geodesic path in the human-free scene by construction (oracle SR ~1.0 without humans).  
   _Evidence:_ VLN-CE paper (ECCV 2020) text via search; CONTEXT.md split sizes.
37. **[high]** Challenge SR definition from HASimulator/metric.py: TCR = max(0, collisions.count - collision_num[ep]); CR = min(TCR,1); SR = success * (TCR==0). Hence any agent that collides more than the released per-episode CMA baseline count fails the episode even if it reaches the goal.  
   _Evidence:_ ext/HA-VLN/HASimulator/metric.py L15-17.

## Key numbers

| What | Value | Source |
|---|---|---|
| ETPNav R2R-CE val unseen NE/OSR/SR/SPL | 4.71 / 65 / 57.2 / 49.2 | arxiv 2410.14250 table; 2603.20804 |
| ETPNav R2R-CE test unseen NE/OSR/SR/SPL | 5.12 / 63 / 55 / 48 | arxiv 2410.14250 table |
| BEVBert-CE val unseen NE/OSR/SR/SPL | 4.57 / 67 / 59 / 50 | arxiv 2609.37353 table; sota2.com |
| HNR val unseen NE/OSR/SR/SPL | 4.42 / 67 / 61 / 51 | arxiv 2507.08831 table |
| ENP-ETPNav val unseen NE/OSR/SR/SPL | 4.69 / 65 / 58 / 50 | arxiv 2410.14250 |
| g3D-LF panorama val unseen NE/OSR/SR/SPL | 4.53 / 68.0 / 61.0 / 52.0 | arxiv 2603.21269 table |
| g3D-LF monocular val unseen / test NE/OSR/SR/SPL | 5.70/59.5/47.2/34.6 ; 6.00/57.5/46.3/32.2 | Dynam3D table; CVPR25 paper |
| VLN-3DFF monocular val unseen / test | 5.95/55.8/44.9/30.4 ; 6.24/54.4/43.7/28.9 | arxiv 2406.09798; Dynam3D table |
| Dynam3D monocular val unseen / test | 5.34/62.1/52.9/45.7 ; 5.53/60.4/51.4/44.8 | arxiv 2505.11383 table |
| NaVid val unseen (paper / released ckpt) and test | 5.47/49.1/37.4/35.9 ; 5.65/49.2/41.9/36.5 ; test 5.39/52/45/39 | ext/sota/NaVid-VLN-CE/README.md |
| Uni-NaVid val unseen (paper / released ckpt) | 5.58/53.3/47.0/42.7 ; 4.96/57.4/51.8/47.7 | ext/sota/Uni-NaVid/README.md |
| NaVILA val unseen NE/OSR/SR/SPL | 5.22 / 62.5 / 54.0 / 49.0 | arxiv 2610.23203 table; 2603.07080 |
| StreamVLN val unseen (paper / v1-3 ckpt) | 4.98/64.2/56.9/51.9 ; 4.90/63.6/56.4/50.2 | ext/sota/StreamVLN/README.md |
| VLN-R1 (Qwen2-VL-7B) val unseen SR/SPL | 30.2 / 21.8 | arxiv 2506.17221 |
| MapNav val unseen (1 frame / +2 history) | 5.92/50.3/36.5/34.3 ; 5.43/53.0/39.7/37.2 | arxiv 2502.13451 |
| NavMorph monocular / panoramic val unseen SR/SPL | ~47.9/33.2 ; ~58-59/49-50 | arxiv 2601.18188 table; 2607.23181; 2506.23468 |
| ETP-R1 val unseen SFT and RFT (OSR/SR/SPL) | SFT 63.24/54.30 ; RFT 71.45/65.31/55.77 | arxiv 2605.09053 table |
| Macro-action closed-loop RL (2609.03906) val unseen SR/SPL | 68.1 / 57.3 (from 65.1/53.5) | arxiv 2609.03906 |
| InternVLA-N1 DualVLN / w NavDP* / S2+SPF val unseen NE/OSR/SR/SPL | 4.05/70.7/64.3/58.5 ; 4.22/70.4/64.1/58.1 ; 4.25/68.3/60.9/55.2 | ext/sota/InternNav/README.md |
| JanusVLN base / +extra data val unseen SR/SPL | 52.8/49.2 ; 60.5/56.8 | arxiv 2509.22548; chengwei920412/JanusVLN-vln README |
| MemoryVLN val unseen NE/OSR/SR/SPL | 3.52 / 59.98 / 54.76 / 50.26 | ext/sota/MemVLN/README.md |
| GroundingVLN (Qwen3.5-4B) val unseen NE/OSR/SR/SPL | 3.66 / 74.8 / 69.9 / 64.1 | arxiv 2609.18581 |
| Nav-R1 dual-system val unseen NE/OSR/SR/SPL | 3.86 / 74.1 / 72.5 / 68.8 | arxiv 2509.10884 |
| Qwen-RobotNav 8B / 4B val unseen SR/SPL (panoramic) | 72.1/66.6 ; 69.5/63.6 | ext/sota/Qwen-RobotNav/README.md |
| ABot-N1 val unseen NE/SR/SPL (tri-view RGB) | 3.32 / 70.89 / 67.5 | arxiv 2607.10383 |
| OmniNav / ABot-N0 / NavFoM(4-view) / NavFoM(1-view) val unseen SR/SPL | 69.5/66.1 ; 66.4/63.9 ; 61.7/55.3 ; 56.2/51.2 | Qwen-RobotNav README table; SimpleVLN table |
| Efficient-VLN v2 (Qwen3-VL-8B) val unseen SR; per-step latency | 73.2 SR ; 159 ms/step (H200) | arxiv 2512.10310v2 |
| SimpleVLN after-RL val unseen SR/SPL: Qwen3.5-9B / 3.5-4B / 3-VL-8B / 3-VL-4B | 76.7/72.6 ; 76.3/72.3 ; 74.4/69.5 ; 73.8/66.7 | ext/sota/SimpleVLN/README.md |
| SimpleVLN pre-RL val unseen SR/SPL (Qwen3.5-9B / Qwen2.5-VL-7B) | 69.2/61.2 ; 59.1/52.0 | ext/sota/SimpleVLN/README.md |
| Zero-shot R2R-CE val unseen SR: HAM-VLN / SpaceVLN / HSGM / SparseNav / VLN-Zero / InstructNav / Open-Nav | 61.0 / 53.3 / 47.9 / 42.8 / 42.4 / 31.0 / 19.0 | arxiv 2607.29600, 2606.08992, CVPR26 HSGM, 2609.26408, 2509.18592 |
| HA-VLN-CE retrained SR val seen/unseen: BEVBert ; ETPNav | 0.27/0.21 ; 0.24/0.17 | arxiv 2503.14229 (v2 step-size table, v3 text) |
| HA-VLN-CE zero-shot val unseen: BEVBert NE/TCR/CR/SR ; ETPNav NE/TCR/CR/SR | 6.10/5.72/0.56/0.15 ; 7.40/7.94/0.71/0.08 | arxiv 2503.14229 Table 4 |
| HA-VLN-CE SR gap vs R2R-CE (v1 gap table): ETPNav retrained/zero-shot ; BEVBert | -70.2% / -86.0% ; -64.4% / -74.6% | arxiv 2503.14229v1 |
| Cylinder-for-human ablation (BEVBert, CE): NE/TCR/CR/SR | 6.32 / 5.11 / 0.46 / 0.17 (TCR -36%, SR +10% rel.) | arxiv 2503.14229 Table 4 |
| HA-VLN-CMA-Base val seen / val unseen NE/TCR/CR/SR | 7.63/63.09/0.77/0.05 ; 7.88/63.84/0.75/0.04 | arxiv 2503.14229 Table 1 fragment |
| Challenge CMA baseline val unseen SR/NE/CR/TCR/Score | 0.129 / 6.387 / 0.684 / 17.536 / 12.945 | track2 README (CONTEXT.md) |
| HCSG HA-VLN-CE val unseen SR / CR | 0.24 / 0.36 (BEVBert 0.21/~0.55, ETPNav 0.17/~0.58) | arxiv 2605.13321 |
| Successful-but-Unsafe: share of successful episodes with contact (sliding); SR drop under blocking; guard effect | 38.5-56.8% ; -11.7 to -36.1 pp ; collision steps -62..98%, SR +6.9..29.3 pp | arxiv 2610.14682 |
| HA-VLN 1.0 (discrete): best retrained unseen SR ; max SR reduction from humans | <=40% ; up to 65% | arxiv 2406.19236 |
| ETPNav-family compute: pretrain+finetune time ; 3DFF val-unseen eval time ; per-step | <1 day on 2-4x3090 ; ~3 h ; <1 s (3090) | GitHub MrZihan/Sim2Real-VLN-3DFF issue #2 |
| NaVid full val-unseen eval ; Uni-NaVid speed | 1839 eps in 2.5 h on 8xA100 ; ~5 Hz on 1 A100 | ext/sota/NaVid-VLN-CE/README.md |
| ETPNav-R2R sensor rig vs HA-VLN config | 12x RGB 224x224 HFOV90 + 12x depth 256x256; 0.25 m / 15 deg; sliding on == HA-VLN HAVLNCE_R2R_task.yaml | ETPNav r2r_vlnce.yaml + ss_trainer_ETP.py; HA-VLN config |
| Perfect-goal privileged planner on HA-R2R (inference) | SR ~0.97-1.0, NE ~0.3-1.0 m, zero collisions => Score ~94-97 | Score formula in CONTEXT.md; metric.py |
| Realistic closed-loop egocentric SR ceiling on HA-R2R test by Nov 30 (inference) | no HA fine-tune: 0.25-0.40 (Score ~30-45); with HA-R2R fine-tune+RL+collision guard: 0.45-0.60 (Score ~50-65); privileged offline-replay with inferred goal: 0.75-0.90 (Score ~78-92) | Derived from facts above |

## Implications (inferences)

- The HA-R2R-CE leaderboard is NOT a standard VLN-CE leaderboard: SR requires success AND no more collisions than the released per-episode CMA baseline. Published R2R-CE SOTA (57-77 SR) collapses to 0.08-0.24 SR on HA-VLN-CE in the literature, primarily because (a) 38-57% of 'successful' R2R-CE episodes involve wall contact under sliding, (b) static human obstacles add collisions, (c) 112-word rewritten instructions shift the language distribution. Any strategy must treat collision-free control as the first-order problem and goal grounding as the second.
- Every strong public agent either (i) relies on sliding + a waypoint predictor + teleport-style backtracking (ETPNav family: back_algo teleport, tryout only without sliding), or (ii) emits discrete actions from a VLA (StreamVLN, SimpleVLN, NaVILA) in Habitat 0.2.4/0.3.3. Neither produces a collision-free replayable action tape out of the box; a local-replay verification loop (plan -> replay in the 0.1.7 docker -> repair) is mandatory regardless of which policy is used.
- Minimal-porting candidates into Habitat 0.1.7 + HA-VLN config: ETPNav, BEVBert-CE, HNR/g3D-LF (panorama), ETP-R1, V2-VLNCE/VIL, NavMorph (hfov90 predictor), NaVid/Uni-NaVid (eval code already 0.1.7), NaVILA (0.1.7 eval). They share the exact 224x224/HFOV90 RGB and 256x256 depth rig. Required changes: register HA simulator type & human loading, swap ETPNav's teleport/back_algo to 'control', add a collision-aware local controller (inflated navmesh / stop-before-contact), and emit the primitive action log. StreamVLN/JanusVLN/MemoryVLN/SimpleVLN need either a Habitat 0.2.4/0.3.3 side-environment that mirrors the HA scenes+humans (feasible: humans are static GLBs placed from human_motion.json) or an observation-server bridge; SimpleVLN is served via vLLM so the simulator side is thin.
- Best off-the-shelf closed-loop policy to start from, by expected HA-R2R SR after collision-guarding: SimpleVLN Qwen3.5-9B RL (76.7 R2R-CE SR, weights public, single-turn input so instruction length 112 words is fine) > ETP-R1 (65.3, 0.1.7-native, cheapest to port, strong with depth) > InternVLA-N1 DualVLN (64.3, RGB) > StreamVLN (56.9). Fine-tuning SimpleVLN-style (IL -> DAgger -> RL with reward = success AND zero-collision) on HA-R2R train with experts re-planned on the human-inserted inflated navmesh is the most promising closed-loop path; RL alone gave +7.5-10 SR on R2R-CE.
- Because scoring is offline replay, the competition reduces to goal inference: a privileged planner with the true goal would score ~94-97 while the best published closed-loop agent scores ~0.24 SR. Even a modest goal-inference accuracy (e.g., 75-85% of episodes placed within 3 m) with guaranteed zero collisions yields Score ~78-92, far above anything an egocentric agent can reach by Nov 30. Ensembles of VLN policies run locally (ETP-R1 + SimpleVLN + StreamVLN) can be used as goal proposers whose stop positions are then verified/re-ranked by an LLM/VLM over privileged renders, and the final tape is produced by a collision-free planner.
- HCSG (May 2026, SR 0.24 on val unseen) and the organizers' own group (UniWM, world models) define the visible competitive landscape; a closed-loop entry in the 0.3-0.5 SR range would already be far beyond the published state of the art, while a privileged-planning entry can plausibly reach 0.8+. Expect at least one other team to discover the replay exploit; speed of execution matters.
- Nondeterministic human animation during replay is a second-order risk: human translation extents are tiny (median 0.03 m, p90 0.8 m), so planning on a navmesh inflated by the human's swept extent (+0.3-0.5 m) plus the agent radius makes the tape robust to frame timing.

## Recommendations

- Port ETP-R1 (not vanilla ETPNav) into the HA-VLN 0.1.7 stack first: same sensor rig, best public graph agent (65.3 SR), ckpts on HF; set back_algo: control, disable teleport, wrap movement in a collision-checking controller, and dump the primitive action tape for local replay.
- Stand up SimpleVLN (Qwen3.5-9B RL) behind vLLM with a Habitat side-environment that loads HA scenes + static humans (HAPS2.0 GLBs at human_motion.json poses) and fine-tune it on HA-R2R train with collision-free experts re-planned on an inflated human-inserted navmesh (IL -> DAgger -> RL, reward = success * [collisions <= baseline]).
- Use all closed-loop agents only as goal proposers inside the privileged offline pipeline; let a navmesh planner (agent radius + human swept-extent inflation) produce the final action sequence and verify zero TCR by local replay before every submission.
- Add the training-free collision guard idea from 'Successful but Unsafe' (stop/turn before predicted contact using depth) to any closed-loop agent; it recovers 7-29 pp SR under blocking.
- Benchmark locally on HA-R2R val_unseen with the challenge metric.py (baseline-adjusted TCR) rather than paper SR; target >0.5 SR closed-loop and >0.9 SR privileged before Phase 2 opens on Oct 30.

## Open questions

- Exact HA-VLN 2.0 Table 1 rows for NaVid/NaVILA (zero-shot) and HA-VLN-CMA*/HA-VLN-VL on the TEST split were not retrievable (arxiv blocked; snippets garbled). Only BEVBert/ETPNav val numbers are confirmed.
- Whether the 18 test-scan human placements will be released in the Phase 2 bundle (needed for local simulation/planning with humans). If withheld, collision-free planning must rely on conservative inflation plus human_motion_text.json (HA-VLN 1.0 era, 90 scans) priors.
- Fraction of HA-R2R test episodes where static humans make the goal unreachable without collision (would cap even the perfect-goal planner). Unknown; needs local navmesh analysis once placements are available.
- How HA-VLN 2.0 computed its own TCR/SR for ETPNav/BEVBert (strict zero-collision vs baseline-adjusted as in the challenge metric.py) - affects comparability of 0.17/0.21 to the challenge Score.
- Per-agent sliding->blocking SR drops from 'Successful but Unsafe' (which agents lose 36 pp) were not retrieved; relevant to choosing which backbone is least collision-prone.
- Efficient-VLN v2 and GroundingVLN code/weights (none found); Nav-R1's evaluation protocol (script defaults to 50/100-episode subsets) casts doubt on its 72.5 SR.
- NavMorph panoramic numbers (58.02/48.98) may be RxR-CE rather than R2R-CE in one source; needs the ICCV table.
- Whether HCSG released code; whether its authors are RoboWorld Track 2 participants.

## Sources

- arxiv 2304.03047 (ETPNav), 2212.04385 (BEVBert), 2404.01943 (HNR), 2410.14250 (ENP), 2411.17030 (g3D-LF), 2406.09798 (VLN-3DFF), 2505.11383 (Dynam3D), 2506.23468 (NavMorph), 2402.15852 (NaVid), 2412.06224 (Uni-NaVid), 2412.04453 (NaVILA), 2507.05240 (StreamVLN), 2506.17221 (VLN-R1), 2502.13451 (MapNav), 2403.17334 (OVER-NAV), 2510.08713 (UniWM), 2505.08712 (NavDP), 2512.08186 (DualVLN), 2512.20940 (ETP-R1), 2609.03906 (macro-action RL), 2605.09053 (LCGNav), 2509.22548 (JanusVLN), 2610.18478 (MemoryVLN), 2609.18581 (GroundingVLN), 2509.10884 (Nav-R1), 2606.18112 (Qwen-RobotNav), 2607.10383 (ABot-N1), 2602.11598 (ABot-N0), 2509.12129 (NavFoM), 2512.10310 (Efficient-VLN), 2610.23203 (SimpleVLN), 2607.29600 (HAM-VLN), 2606.08992 (SpaceVLN), 2606.00095 (HSGM), 2609.26408 (SparseNav), 2509.18592 (VLN-Zero), 2608.07548 (SC2-WM), 2503.14229 (HA-VLN 2.0), 2406.19236 (HA-VLN 1.0), 2605.13321 (HCSG), 2610.14682 (Successful but Unsafe), 2609.21504 (DPed-VLN), 2411.18539 (AdaVLN), 2203.02764 (CWP waypoint predictor), 2004.02857 (VLN-CE)
- Local clones (depth 1) under /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/sota/: ETPNav, VLN-BEVBert, HNR-VLN, Sim2Real-VLN-3DFF, g3D-LF, Dynam3D, NaVid-VLN-CE, Uni-NaVid, StreamVLN, NaVILA, NavDP, GPT4Scene (VLN-R1), ETP-R1, NavMorph, V2-VLNCE-realjoshqsun, Qwen-RobotNav, SimpleVLN, MemVLN, Nav-R1, InternNav, JanusVLN-vln, DPedVLN, UniWM, GroundingVLN (LICENSE only)
- Local files: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/HASimulator/config/HAVLNCE_R2R_task.yaml; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/HASimulator/metric.py L15-17; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/sota/ETPNav/habitat_extensions/config/r2r_vlnce.yaml; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/sota/ETPNav/run_r2r/iter_train.yaml; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/sota/ETPNav/vlnce_baselines/common/environments.py L360-470; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/sota/ETPNav/vlnce_baselines/ss_trainer_ETP.py L97-144,L199; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/sota/ETPNav/vlnce_baselines/waypoint_pred/TRM_net.py
- GitHub pages fetched: github.com/MrZihan/Sim2Real-VLN-3DFF/issues/2 and /issues/3; github.com/UWMILab/HA-VLN
- Secondary tables used for cross-checking: arxiv 2603.20804, 2609.37353, 2507.08831, 2603.21269, 2601.18188, 2607.23181, 2603.07080, 2609.18789, 2605.09053, sota2.com R2R-CE val-unseen page
