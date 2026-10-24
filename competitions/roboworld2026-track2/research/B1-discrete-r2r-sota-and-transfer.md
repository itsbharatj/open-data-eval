# Discrete (nav-graph) R2R SOTA 2021-2026 and transfer to HA-VLN Track 2 via offline connectivity-graph planning

**topic_id:** `B1-discrete-r2r-sota-and-transfer`

## Summary

Discrete (panoramic, Matterport3D connectivity-graph) R2R agents are far stronger than any continuous (VLN-CE) agent: single-run test-unseen SR went from 63 (Rec-VLN-BERT, 2021) to 69 (DUET), 73 (BEVBert/GridMM), 77 (ScaleVLN CLIP-B/16; MAGIC-L), 80 (ScaleVLN CLIP-H/14+EnvEdit) and ~85 SR / 78 SPL (SRDF, ICLR 2025; SPL beats the 76 human SPL), versus the Track-2 CMA baseline at 12.9 SR. Every one of these models is public with code, checkpoints and PRECOMPUTED features for all 90 MP3D scans (incl. the 18 test scans, because R2R test submissions required them), so no Matterport skybox download or feature extraction is needed to run them; features are hdf5 keyed '{scan}_{viewpoint}' -> [36 views, D]. Transfer to our setting is structurally sound: R2R-CE episodes were produced by snapping R2R viewpoint paths onto the Habitat navmesh (77% of R2R paths survived a 'shortest path passes within 0.5 m of each waypoint' test), the 18 test scans have 1,971 included viewpoints (109.5/scan, 3,905 edges, median edge 2.13 m, 73% of edges < 3 m), and success radius is 3 m, so stopping at the correct viewpoint is a success and stopping one node early still succeeds ~73% of the time. Because scoring is offline replay of a submitted action sequence, exploration is free: we can enumerate/beam-search candidate viewpoint paths in the graph and rerank them with several agents plus a speaker model (historically beam search added +15-20 SR over single-run: EnvDrop 51->69, AuxRN ->71, Airbert/Lily ->78), then execute only the chosen path collision-free. The two real risks are (1) instruction style: HA-R2R instructions are LLM-expanded (avg 112 words) R2R-CE instructions with inserted human-activity sentences; DUET-family models accept 200 BERT tokens (OK) but BEVBert and Rec-VLN-BERT truncate at 80 tokens; GSA-R2R shows DUET falling to ~54 SR on LLM-restyled instructions (vs 69-72 on R2R) and HA-VLN 2.0 shows Rec-VLN-BERT 0.63->0.33 and Airbert 0.62->0.36 SR on HA-VLN-DE; mitigations are LLM de-paraphrasing back to R2R style, fine-tuning on the 10.8k HA-R2R train instructions aligned to R2R viewpoint paths via trajectory_id, and recovering the original R2R-CE test instruction if the test bundle keeps trajectory_id/instruction_id; and (2) visual domain if we re-render with Habitat instead of using MatterSim-skybox features (Sim-2-Sim: Rec-VLN-BERT 63 SR in MP3D-sim -> 43/44 SR after full transfer; the graph-teleport ablation isolates the render gap and should be re-measured locally). Recommended goal-proposal engines: (1) ScaleVLN DUET CLIP-H/14+EnvEdit (ready-to-run finetuned ckpt, 80/70 test), (2) SRDF (InternViT-6B features + released pretrained model; needs ~1 A100-day finetune; ~85 SR), (3) NavGPT-2 FlanT5-XXL (71.8/60.3 test; LLM backbone, 200-token input, most likely to tolerate paraphrased long instructions and gives rationales); MAGIC-L/GOAT (77/69, 75/65, CLIP-B/16) as cheap ensemble members; BEVBert/GridMM lower priority (depth grid features, 80-token limit). No published 'ETPNav-DE' exists; ETPNav is CE-only (its discrete sibling is BEVBert).

## Facts (verified) with confidence

1. **R2R test-unseen single-run results (NE m / SR % / SPL %): Rec-VLN-BERT 4.09/63/57; HAMT 3.93/65/60; DUET 3.65/69/59; BEVBert 3.13/73/62; GridMM 3.35/73/62; GOAT ~3.0/74.57/64.94 (rounded 75/65); MAGIC-L 2.75/77/69; MAGIC-S (11M params) 75.17/65.13; ScaleVLN(DUET, CLIP-B/16) 77/68; ScaleVLN(CLIP-H/14+EnvEdit) 80/70 (OSR 86); NavGPT-2 FlanT5-XL 3.39/70.76/59.60; NavGPT-2 FlanT5-XXL 3.33/71.84/60.28 (OSR 80.3); NaviLLM(Vicuna-7B) 68/60; MiniVLN 77.59/68.05; ScaleVLN-NavGRPO 79/70; Human 1.61/86/76.**
   - Evidence: Cross-checked across: 'Do Visual Imaginations Improve VLN Agents' (CVPR25) test table (HAMT/DUET/BEVBert rows); GridMM arXiv 2307.12907 table; 'Trajectory-Diversity-Driven Robust VLN' arXiv 2603.15370 test table (ScaleVLN 77/68, GOAT 75/65, BEVBert 73/62, NavGPT-2 72/60->README says 71.84/60.28, MAGIC-L 77/69, NavGRPO 79/70); MAGIC arXiv 2406.17960 (MAGIC-S 75.17/65.13 vs GOAT 74.57/64.94; ScaleVLN 77/68 test, 79/70 val-unseen); MiniVLN 2409.18800; ScaleVLN appendix leaderboard entry 'EarlyToBed (ours)' 80 SR/70 SPL and SRDF Table-18 ScaleVLN row '86, 80, 70' (OSR/SR/SPL test); NavGPT-2 README table ($EXT/NavGPT-2/README.md); NavGPT-2 Table 1 for NaviLLM 68/60; Rec-VLN-BERT CVPR21 paper (63/57, NE 4.09) and human 86/76.
   - Confidence: high (Rec-VLN-BERT, HAMT, DUET, BEVBert, GridMM, NavGPT-2, MAGIC, ScaleVLN); medium (GOAT NE, NaviLLM, MiniVLN, NavGRPO)

2. **SRDF (ICLR 2025, Wang et al.) is the current discrete SOTA: SPL on R2R TEST raised from 70 to 78, surpassing human SPL 76; val-unseen ~85-86 SR / 78-79 SPL (released intermediate data reproduces ~85/78, ~1 pt below paper); a 2026 survey quotes 85% SR on R2R Test-Unseen for the SRDF-trained DUET; SkillNav (SRDF-based) reports 83/77.**
   - Evidence: SRDF abstract (arXiv 2412.08467) '70% to 78% SPL on the classic R2R test set, surpassing human performance (76%)'; $EXT/VLN-SRDF/README.md ('~85% SR and ~78% SPL on R2R val unseen ... ScaleVLN (81% SR and 70% SPL)'); survey arXiv 2607.09792 ('DUET baseline ... R2R Test-Unseen set (85% SR)'); SkillNav arXiv 2508.07642.
   - Confidence: high for SPL 78 test; medium for SR ~85 test

3. **All top discrete models are public with code AND checkpoints AND precomputed per-viewpoint features covering all 90 MP3D scans including the 18 test scans (required for their own R2R test submissions). Feature stores: ScaleVLN HF OpenGVLab/ScaleVLN features.zip (clip_vit-b16_mp3d_original.hdf5, clip_vit-h14_mp3d_original.hdf5 + EnvEdit variants, plus HM3D/Gibson); SRDF HF ZunWang/SRDF (internvit_6b_fov60_mp3d.hdf5, 3200-d; model_step_170000.pt pretrained); DUET/HAMT Dropbox (pth_vit_base_patch16_224_imagenet.hdf5, 768-d); GOAT/MAGIC HF crystal61 ('clip768' CLIP ViT-B/16 METER features + EnvEdit); NavGPT-2 HF ZGZzz (MP3D_eva_clip_g_can.lmdb; FlanT5-XL/XXL weights); NaviLLM OneDrive/HF (mp3d_EVA02-CLIP-L-14-336.hdf5; Vicuna-7B base); BEVBert ModelScope admagic/BEVBert grid features + GDrive weights; GridMM Baidu Netdisk; Rec-VLN-BERT zenodo (ResNet-152-Places365 tsv).**
   - Evidence: READMEs under $EXT/ScaleVLN, $EXT/VLN-SRDF, $EXT/VLN-DUET, $EXT/VLN-HAMT, $EXT/VLN-GOAT, $EXT/VLN-MAGIC, $EXT/NavGPT-2, $EXT/NaviLLM, $EXT/VLN-BEVBert, $EXT/GridMM, $EXT/Recurrent-VLN-BERT; ScaleVLN parser uses val_ft_file=clip_vit-h14_mp3d_original.hdf5 for --test --submit ($EXT/ScaleVLN/VLN-DUET/map_nav_src/r2r/parser.py lines 118-131; scripts/r2r_h14_envedit_mix.sh test block).
   - Confidence: high (feature files exist for test scans); medium (hosts are Dropbox/Baidu/OneDrive/GDrive/HF - some blocked from this sandbox but reachable from a normal machine)

4. **Feature file format is uniform across the DUET family: hdf5 dataset per key '%s_%s' % (scan, viewpoint) with shape [36, D] (36 discretized views: 12 headings x 3 elevations -30/0/+30 deg, rendered by MatterSim at 640x480, VFOV 60), optionally truncated to image_feat_size. BEVBert additionally uses 12-view 224x224 VFOV-90 CLIP grid features and depth grids (MatterSim depth after depth_to_skybox, or Habitat).**
   - Evidence: $EXT/ScaleVLN/VLN-DUET/map_nav_src/utils/data.py lines 10-30 (ImageFeaturesDB); $EXT/VLN-HAMT/preprocess/precompute_img_features_vit.py lines 31-37, 85-100; $EXT/VLN-BEVBert/precompute_features/grid_mp3d_clip.py (VIEWPOINT_SIZE=12, 224x224, VFOV 90) and grid_depth.py (builds both MatterSim and Habitat sims).
   - Confidence: high

5. **Pretraining data: Rec-VLN-BERT/HAMT/DUET/BEVBert/GridMM/GOAT/MAGIC/NaviLLM/NavGPT-2 use MP3D only (R2R + PREVALENT/EnvDrop speaker augmentation, RxR-Marky, EnvEdit for GOAT/MAGIC). ScaleVLN adds 800 HM3D + 491 Gibson scenes (4.9M instruction-trajectory pairs; graphs built by linking viewpoints within 5 m, <=5 edges, mean edge 1.41 m, degree 4.55; panoramas 512x1024 rendered from the mesh in Habitat and repaired with Co-Mod GAN). SRDF adds SRDF-20M (19.5M pairs on HM3D paths) on top of ScaleVLN with InternViT-6B features. NavGPT-2 adds 10K GPT-4V reasoning samples; NaviLLM is multi-task (CVDN/SOON/R2R/REVERIE/ScanQA/LLaVA).**
   - Evidence: $EXT/ScaleVLN/VLN-DUET/pretrain_src/config/r2r_pretrain_hm3d+mp3d+gibson_clip-h14.json (train files R2R_hm3d_aug_envdrop_generated_enc.jsonl, R2R_gibson_aug_envdrop_generated_enc.jsonl, R2R_prevalent_aug_train_enc.jsonl); ScaleVLN paper/appendix (arXiv 2307.15644); SRDF README; NavGPT-2 README; NaviLLM README; GOAT README (PREVALENT, RxR-Marky, EnvEdit).
   - Confidence: high

6. **ScaleVLN/SRDF agents were trained on Habitat-rendered (GAN-repaired) HM3D/Gibson panoramas mixed with MatterSim MP3D panoramas, so they have already seen render-style imagery; models trained only on MP3D skybox photos (DUET, HAMT, BEVBert, GOAT, MAGIC, NavGPT-2, NaviLLM) have not.**
   - Evidence: ScaleVLN appendix (render 512x1024 from mesh, Co-Mod GAN repair, 36 views cut from repaired crops); ScaleVLN parser mixes clip_vit-h14_mp3d_original.hdf5 with clip_vit-h14_mp3d_hm3d_gibson.hdf5.
   - Confidence: high (fact) / medium (the inference that this reduces Habitat-render domain gap)

7. **R2R-CE episodes are derived from R2R nav-graph paths: each viewpoint's 3D location is projected onto the nearest navigable navmesh point and a trajectory is kept only if an agent following the shortest path passes within 0.5 m of each next waypoint; 77% of R2R trajectories survived (5,611 trajectories pre-filter; 4,475 in the ECCV release across train/val). The R2R-CE/HA-R2R test split has 3,408 episodes in 18 scenes and 'does not have ground truth paths or goal locations'. Success radius = 3.0 m.**
   - Evidence: Krantz et al. ECCV 2020 'Beyond the Nav-Graph' (ecva.net PDF, via WebSearch); VLN-CE data page jacobkrantz.github.io/vlnce/data (3408 episodes, 18 scenes; no GT for test); ACE-Brain-0.5 description of the VLN-CE projection protocol; HA-DE eval error_margin=3.0 ($EXT/HA-VLN/HASimulator/HA-DE/tasks/HA/eval.py line 25).
   - Confidence: high

8. **Connectivity graphs for the 18 test scans (same files MatterSim uses) are in $EXT/HA-VLN/HASimulator/HA-DE/connectivity: 1,971 included viewpoints total (mean 109.5/scan, min 37 [2t7WUuJeko7, gYvKGZ5eRqb=38], max 229 [pa4otMbVnkk]); 3,905 undirected 'unobstructed' edges; edge length mean 2.40 m, median 2.13 m, p10 1.06 m, p90 4.01 m, max 16.8 m; 73.0% of edges < 3.0 m, 45% < 2.0 m, 2% > 5 m; mean degree 3.96; nearest-neighbour node spacing median 1.39 m (p90 2.26 m).**
   - Evidence: Computed with python over the 18 *_connectivity.json files (pose[3],pose[7],pose[11] = x,y,z; 'included' and 'unobstructed' flags) - see this agent's tool log; file format documented in $EXT/Matterport3DSimulator/connectivity/README.md.
   - Confidence: high

9. **CWP (Hong et al. CVPR 2022, Discrete-Continuous-VLN) released 'adapted MP3D connectivity graphs in continuous environments' in which all nodes are placed in open space and all edges are fully traversable by a VLN-CE-configured agent; the waypoint-predictor repo loads them via RAW_GRAPH_PATH. This is the safest graph to plan on if nodes of the raw graph fall inside geometry.**
   - Evidence: $EXT/Discrete-Continuous-VLN/README.md section 'Adapted MP3D Connectivity Graphs in Continuous Environments' (GDrive link); $EXT/waypoint-predictor/README.md lines 5-8.
   - Confidence: high

10. **Sim-2-Sim (Krantz & Lee, ECCV 2022 oral) transferred Rec-VLN-BERT (63 SR in MP3D-sim val unseen) into Habitat: with predicted subgoals + local policy it scores 43 SR / 36 SPL / 52 OSR val-unseen and 44 SR test (+12 over prior VLN-CE SOTA); the paper states transfer 'does not fully retain' discrete performance. Its code has a 'graph-teleport' config (known subgoals from the MP3D nav graph, teleport between nodes) that is exactly our setting (a), plus 'graph-oracle_policy' (A*) and 'graph-local_policy'.**
   - Evidence: $EXT/Sim2Sim-VLNCE/README.md ('Known Subgoals ... Teleportation: the discrete VLN task in Habitat', configs sim2sim_vlnce/config/graph-teleport.yaml); Sim-to-Real-3DFF arXiv 2406.09798 table (Sim-2-Sim 43 val-unseen / 44 test); ECCV PDF abstract.
   - Confidence: high; exact teleport-ablation numbers NOT retrieved (open question)

11. **HA-R2R instructions were generated by ChatGPT-4o / LLaMA-3-8B-Instruct from the ORIGINAL R2R-CE instruction plus start/during/end human-activity descriptions (few-shot prompt), i.e. every HA-R2R instruction contains the original route text as a sub-structure; HA-VLN 2.0 reports avg 112 words. The older HA-VLN 1.0 discrete files (HA_val_unseen.json: 783 paths, 2,349 instructions, 11 scans) average 50 words and include 'human' (viewpoint, relative position, description) and 'crux_points' fields alongside the viewpoint 'path'.**
   - Evidence: $EXT/HA-VLN/Data/HA-R2R/README.md (prompt and examples); $EXT/HA-VLN/HASimulator/HA-DE/tasks/HA/data/HA_val_unseen.json (parsed: mean 50.1 words, median 52); CONTEXT.md fact 5 (avg 112 words).
   - Confidence: high

12. **Instruction-length limits: DUET, ScaleVLN, GridMM, GOAT, MAGIC, NavGPT-2 fine-tune with --max_instr_len 200 (BERT wordpieces); BEVBert uses 80; Rec-VLN-BERT maxInput=80. A 112-word HA-R2R instruction is roughly 140-170 wordpieces, so it fits the 200-token models (tail may be clipped on the longest ones) but loses ~half its text (including the final stop description) in BEVBert/Rec-VLN-BERT.**
   - Evidence: grep max_instr_len over $EXT/*/map_nav_src/scripts/*.sh and $EXT/VLN-BEVBert/scripts/ft_r2r.bash line 38; $EXT/Recurrent-VLN-BERT/r2r_src/param.py line 19.
   - Confidence: high (limits); medium (token-count estimate)

13. **Instruction-style robustness evidence: (i) GSA-R2R (ICLR 2025) finds all models best on Basic > User > Scene LLM-restyled instructions; a third-party leaderboard lists DUET at 54.0 SR / 44.4 SPL on 'Sheldon'-style instructions vs GR-DUET 63.9/58.9 (paper: GR-DUET +8 SR over DUET via environment/style-specific training). (ii) HA-VLN 2.0 Table 2 (val unseen, discrete HA-VLN-DE with humans and collision-aware SR): Speaker-Follower 0.35->0.21, Rec(PREVALENT) 0.63->0.33 (NE 6.12, TCR 0.29, CR 0.81), Airbert 0.62->0.36 (NE 5.54, TCR 0.30, CR 0.83); HA-VLN 1.0 reports the best retrained agent at <=40% SR unseen (drops up to 65%). (iii) 'Does VLN pretraining work with nonsensical instructions' (HAMT/VLN-BERT): transformer agents are insensitive to word order and largely key on content tokens, so extra human/landmark sentences act as distractor landmarks rather than breaking parsing.**
   - Evidence: GSA-R2R arXiv 2501.17403 + sota2 GSA-R2R leaderboard; HA-VLN 2.0 arXiv 2503.14229 (v1/v2 tables consistent); HA-VLN 1.0 arXiv 2406.19236; arXiv 2311.17280.
   - Confidence: medium (numbers are from third-party tables/snippets; the HA-VLN-DE drop confounds instruction style with human obstacles and a stricter success definition)

14. **HA-DE discrete evaluation (HA-VLN 1.0/2.0 code) defines success as NE < 3.0 m AND zero human 'hits' (hits computed from the path's proximity to human locations from human_motion_text.json); teacher paths are shortest paths on the graph with nodes near humans removed (strategies local/global/sLLA).**
   - Evidence: $EXT/HA-VLN/HASimulator/HA-DE/tasks/HA/eval.py lines 17-25, 55-97, 141-144, 173; env.py lines 223-308, 359-363.
   - Confidence: high

15. **Beam-search / pre-exploration upper bounds on R2R test (leaderboard snapshot 28 Jul 2023 in ScaleVLN appendix Table 17 and EnvDrop/AuxRN papers): EnvDrop beam 69 SR (single-run 51), AuxRN beam 71, Airbert and Lily beam 78 SR (SPL ~1 because of trajectory length), Active Exploration pre-explore 70; i.e. +15-20 SR over the same model's single run in 2019-2023 era models. Oracle success (OSR) of modern single-run agents: DUET 80.5, BEVBert 84, ScaleVLN 87.5 (val unseen) / 86 (test), NavGPT-2-XXL 83.9 (val unseen).**
   - Evidence: ScaleVLN arXiv 2307.15644 appendix Table 17; 'Rethinking the Spatial Route Prior' arXiv 2110.05728 beam-search block; third-party OSR tables (arXiv 2603.15370, 2602.15724); NavGPT-2 README.
   - Confidence: high (beam numbers), medium (OSR split labels)

16. **No published 'ETPNav-DE' exists. ETPNav (An et al.) is a continuous-environment (R2R-CE/RxR-CE) topological planner; its discrete-environment sibling by the same first author is BEVBert. ETP-R1 (Dec 2025, RL fine-tuning of ETPNav) is also CE-only (+6 SR / +3 SPL over G3D-LF on R2R-CE test). The HA-VLN repo only references ETPNav for habitat installation instructions.**
   - Evidence: WebSearch on 'ETPNav-DE' returned nothing; ETP-R1 arXiv 2512.20940; $EXT/HA-VLN/README.md line 253.
   - Confidence: high

17. **Other 2025-2026 discrete R2R entrants (self-reported, mostly incremental over GridMM/ScaleVLN): DART-VLN (training-free test-time memory decay on GridMM: 73/62 -> 74/63 test), FIGR (76/67 val unseen, 66 SPL test), VER (CVPR24, +3 SR/+4 SPL over BEVBert on test), SR-VLN (Sensors 2026, 76.02 SR / 73.80 SPL test, GRPO), UNeMo (world model, +2.1 SR over SOTA on R2R unseen), DV-VLN (LLaMA-2 generate-then-verify, 'competitive'), LookStep, 'Learning to Retrieve Navigable Candidates'. None beats SRDF/ScaleVLN-H14 on test; NavGRPO (CVPR26 Findings) adds +3 SPL on ScaleVLN (79/70 test).**
   - Evidence: arXiv 2607.01043 (DART-VLN), 2503.11006 (FIGR), 2403.14158 (VER), Sensors s26123809 (SR-VLN), 2511.18845 (UNeMo), 2601.18492 (DV-VLN), 2603.15370 (NavGRPO).
   - Confidence: medium

18. **Zero-shot LLM navigators on discrete R2R val unseen are far weaker than trained specialists: MapGPT (GPT-4V) 43.7 SR, DiscussNav (GPT-4) 43 SR / 40 SPL, NavCoT 40/37. They are therefore not goal-proposal engines but can serve as instruction de-paraphrasers / rerankers.**
   - Evidence: MapGPT ACL 2024 (arXiv 2401.07314); NavGPT-2 Table comparison; MSNav arXiv 2508.16654.
   - Confidence: high

19. **R2R test split (discrete) is public: R2R_test.json (Dropbox links in $EXT/Matterport3DSimulator/tasks/R2R/data/download.sh) holds the 18 test scans' instructions with only the START viewpoint ('For the test set, only the first path_id (starting location) is included'). VLN-CE episodes carry trajectory_id (= R2R path_id) and instruction.instruction_id; HA-VLN's task.py keeps both fields.**
   - Evidence: $EXT/HA-VLN/HASimulator/HA-DE/tasks/HA/README.md ('For the test set, only the first path_id ...'); $EXT/HA-VLN/agent/VLN-CE/habitat_extensions/task.py lines 24, 42, 91; VLN-CE data docs.
   - Confidence: high (R2R_test.json content); medium (whether the Phase-2 HA-R2R test bundle retains trajectory_id/instruction_id - UNCONFIRMED)

20. **collision_num_test.json has 3,408 keys ('1'..'3408'); the first five entries are 0, consistent with per-episode baseline collision counts indexed by episode_id (string).**
   - Evidence: $EXT/HA-VLN/Data/HA-R2R-tools/collision_num_test.json parsed in this session.
   - Confidence: high


## Numbers

| What | Value | Source |
|---|---|---|
| Best discrete single-run R2R test-unseen SR / SPL (SRDF, ICLR25) | ~85 SR / 78 SPL (SPL > human 76) | arXiv 2412.08467 abstract; survey arXiv 2607.09792; SRDF README (val unseen ~85/78) |
| ScaleVLN CLIP-H/14+EnvEdit test-unseen OSR/SR/SPL | 86 / 80 / 70 (val unseen 88/81/70) | ScaleVLN appendix leaderboard 'EarlyToBed'; SRDF Table 18 row |
| ScaleVLN CLIP-B/16 test-unseen SR/SPL | 77 / 68 (val unseen 79.4/70.0, OSR 87.5) | MAGIC arXiv 2406.17960; MiniVLN 2409.18800; arXiv 2603.15370 |
| MAGIC-L test-unseen NE/SR/SPL | 2.75 / 77 / 69 (val unseen 79/70) | arXiv 2603.15370 table; SRDF ICLR25 table |
| GOAT test-unseen SR/SPL | 74.57 / 64.94 | MAGIC arXiv 2406.17960 |
| BEVBert test-unseen NE/SR/SPL | 3.13 / 73 / 62 (val unseen 75/64, OSR 84) | BEVBert arXiv 2212.04385; CVPR25 'Visual Imaginations' table |
| GridMM test-unseen NE/SR/SPL | 3.35 / 73 / 62 (val unseen 75/64) | arXiv 2307.12907 |
| DUET test-unseen NE/SR/SPL | 3.65 / 69 / 59 (val unseen 72/60, OSR 80.5) | CVPR25 'Visual Imaginations' table; arXiv 2602.15724 |
| HAMT test-unseen NE/SR/SPL | 3.93 / 65 / 60 (val unseen 66/61, OSR 73) | CVPR25 'Visual Imaginations' table; HAMT supplemental |
| Rec-VLN-BERT (PREVALENT) test-unseen NE/SR/SPL | 4.09 / 63 / 57 | Hong et al. CVPR 2021 |
| NavGPT-2 FlanT5-XXL test TL/NE/OSR/SR/SPL | 14.74 / 3.33 / 80.30 / 71.84 / 60.28 (val unseen 73.82/61.06) | $EXT/NavGPT-2/README.md |
| NavGPT-2 FlanT5-XL test NE/SR/SPL | 3.39 / 70.76 / 59.60 | $EXT/NavGPT-2/README.md |
| NaviLLM (Vicuna-7B) R2R SR/SPL | test 68/60; val unseen 67/59 | NavGPT-2 Table 1; $EXT/NaviLLM/README.md checkpoint table |
| Human R2R test NE/SR/SPL | 1.61 / 86 / 76 | Rec-VLN-BERT paper table; SRDF abstract (human SPL 76) |
| Beam-search test SR (older models) | EnvDrop 69 (single 51), AuxRN 71, Airbert 78, Lily 78 (SPL ~1); pre-explore Active Exploration 70 | ScaleVLN appendix Table 17 (leaderboard 28 Jul 2023); arXiv 2110.05728 |
| Zero-shot LLM navigators val unseen SR | MapGPT(GPT-4V) 43.7; DiscussNav 43; NavCoT 40 | arXiv 2401.07314; NavGPT-2 paper |
| Track-2 CMA baseline val_unseen SR | 0.129 (Score 12.945) | CONTEXT.md fact 3 |
| Test-scan connectivity graph size | 1,971 included viewpoints (109.5/scan); 3,905 edges; mean degree 3.96 | computed from $EXT/HA-VLN/HASimulator/HA-DE/connectivity/*_connectivity.json |
| Edge length distribution (test scans) | mean 2.40 m, median 2.13 m, p10 1.06, p90 4.01, max 16.8; 73% < 3 m, 45% < 2 m | computed as above |
| R2R->R2R-CE conversion yield | 77% of R2R trajectories navigable (0.5 m waypoint criterion); 5,611 trajectories | Krantz et al. ECCV 2020 |
| HA-R2R test split | 3,408 episodes, 18 scans, GT paths/goals withheld | VLN-CE data page; CONTEXT.md |
| Instruction length | R2R 29 words; R2R-CE 32; HA-R2R 1.0 DE val_unseen mean 50; HA-R2R 2.0 avg 112; RxR-CE ~110-120 | RxR/R2R papers; HA_val_unseen.json parsed; CONTEXT.md |
| Model instruction token limits | 200 wordpieces (DUET/ScaleVLN/GridMM/GOAT/MAGIC/NavGPT-2); 80 (BEVBert, Rec-VLN-BERT) | repo scripts (see facts) |
| GSA-R2R style shift (DUET) | 54.0 SR / 44.4 SPL on LLM-restyled instructions vs 69-72 on R2R; GR-DUET 63.9/58.9 (+8 SR) | arXiv 2501.17403; sota2 GSA-R2R page (third-party) |
| HA-VLN-DE val unseen SR drop (VLN -> HA-VLN-DE) | Rec(PREVALENT) 0.63->0.33; Airbert 0.62->0.36; Speaker-Follower 0.35->0.21 | HA-VLN 2.0 arXiv 2503.14229 Table 2 |
| Sim-2-Sim transfer of Rec-VLN-BERT | 63 SR (MP3D-sim val unseen) -> 43 SR/36 SPL/52 OSR val unseen, 44 SR test with predicted subgoals | ECCV 2022; arXiv 2406.09798 table |
| ScaleVLN synthetic graphs | link within 5 m, <=5 edges/node, mean edge 1.41 m, degree 4.55; 800 HM3D + 491 Gibson scenes; 4.9M pairs | ScaleVLN paper |
| Feature extraction cost if re-rendering 18 test scans | 1,971 viewpoints x 36 views = 70,956 images; ~10 GPU-min for ViT-B/16 CLIP, ~1 GPU-h for InternViT-6B (estimate) | this agent's estimate from HAMT/ScaleVLN scripts |
| Fine-tuning cost | ScaleVLN fine-tune: 1 A100, 200k iters bs 8 (script); pretraining 2 A100; SRDF: pretrain 1-2 epochs sufficient; NaviLLM: ~20 h on 8 A100 | repo READMEs/scripts |

## Model table (R2R test unseen, single run; NE m / SR % / SPL %)

| Model | Venue | Test NE/SR/SPL | Val-unseen SR/SPL (OSR) | Pretraining data | Visual features | Code/ckpt + feature host | Instr. token limit |
|---|---|---|---|---|---|---|---|
| Rec-VLN-BERT (PREVALENT) | CVPR21 | 4.09/63/57 | 63/57 | MP3D + PREVALENT aug | ResNet-152 Places365 (tsv) | zenodo (weights, feats) | 80 |
| HAMT | NeurIPS21 | 3.93/65/60 | 66/61 (73) | MP3D + PREVALENT aug; e2e ViT | ViT-B/16 768-d, 36 views | Dropbox | 200 (BERT) |
| DUET | CVPR22 | 3.65/69/59 | 72/60 (80.5) | MP3D + PREVALENT aug | ViT-B/16 ImageNet 768-d | Dropbox | 200 |
| Lily (DUET generative) | ICCV23 | ~72/? (+3 SR over DUET; beam 78) | 74 | YouTube-VLN + MP3D | - | JeremyLinky/YouTube-VLN | - |
| BEVBert | ICCV23 | 3.13/73/62 | 75/64 (84) | MP3D + Prevalent aug | CLIP ViT-B/16 512-d grid (12 views) + depth grid | GDrive + ModelScope | 80 |
| GridMM | ICCV23 | 3.35/73/62 | 75/64 | MP3D + aug | ViT-B/16 + grid/depth | Baidu Netdisk | 200 |
| ScaleVLN (DUET, CLIP-B/16) | ICCV23 | -/77/68 | 79.4/70.0 (87.5) | MP3D + 800 HM3D + 491 Gibson (4.9M) | CLIP ViT-B/16 512-d | HF OpenGVLab/ScaleVLN | 200 |
| ScaleVLN (CLIP-H/14 + EnvEdit) | ICCV23 | -/80/70 (OSR 86) | 81/70 (88) | same | CLIP ViT-H/14 1024-d | HF OpenGVLab/ScaleVLN (duet_vit-h14_ft_best_val_unseen) | 200 |
| NaviLLM (Vicuna-7B) | CVPR24 | -/68/60 | 67/59 | multi-task MP3D (CVDN/SOON/R2R/REVERIE/ScanQA/LLaVA) | EVA02-CLIP-L-14-336 | HF zd11024/NaviLLM + OneDrive feats | LLM prompt |
| NavGPT-2 FlanT5-XL | ECCV24 | 3.39/70.76/59.60 | 69.89/58.86 (78.5) | MP3D R2R + 10K GPT-4V reasoning | EVA-CLIP-g (lmdb) | HF ZGZzz | 200 |
| NavGPT-2 FlanT5-XXL | ECCV24 | 3.33/71.84/60.28 (OSR 80.3) | 73.82/61.06 (83.9) | same | same | HF ZGZzz | 200 |
| GOAT | CVPR24 | ~3.0/74.57/64.94 | ~78/68 | MP3D + PREVALENT + RxR-Marky + EnvEdit (METER init) | CLIP ViT-B/16 768-d ('clip768') | HF crystal61/VLN-GOAT | 200 |
| MAGIC-L / MAGIC-S | arXiv24 / TPAMI26 | 2.75/77/69 ; 75.17/65.13 | 79/70 | as GOAT | clip768 | HF crystal61/VLN-MAGIC | 200 |
| VER | CVPR24 | +3 SR/+4 SPL over BEVBert (~76/66) | - | MP3D | volumetric | DefaultRui/VLN-VER | - |
| MiniVLN | arXiv24 | -/77.59/68.05 | - | ScaleVLN data (distilled) | - | - | - |
| SRDF (DUET + InternViT-6B) | ICLR25 | -/~85/78 (SPL > human 76) | 85-86/78-79 | ScaleVLN envs + SRDF-20M (19.5M HM3D) | InternViT-6B fov60 3200-d | HF ZunWang/SRDF (pretrained model_step_170000.pt; partial data) | 200 |
| SkillNav (SRDF-based) | 2025 | -/83/77 (reported 'unseen') | - | SRDF | - | - | - |
| ScaleVLN-NavGRPO | CVPR26F | -/79/70 | - | ScaleVLN + GRPO | CLIP-B/16 | cocoastar/NavGRPO (unverified) | 200 |
| DART-VLN (GridMM + TTA) | 2026 | -/74/63 | 76/65 | - | - | Japluto/DART-VLN | - |
| SR-VLN | Sensors 2026 | -/76.02/73.80 (self-reported) | - | GRPO | - | - | - |
| Human | - | 1.61/86/76 | - | - | - | - | - |

## Implications

- Discrete goal proposal dominates CE policies by ~6x in SR (80-85 vs 12.9 baseline / ~55-70 for best CE agents); since Score = 100*Nav*(0.7+0.3*Social) with Nav = 0.8 SR + 0.2*3/(3+NE), reaching ~80 SR with zero collisions would give Score ~ 80-85 vs 12.9 baseline.
- Trajectory length is irrelevant to Score (no SPL term), so offline beam/exhaustive search over the connectivity graph with multi-model + speaker reranking is free; historically beam search gave +15-20 SR, so 85-92 SR is a plausible ceiling for an ensemble of ScaleVLN-H14, SRDF and MAGIC-L/NavGPT-2 (inference).
- Because the R2R-CE goal is the snapped last R2R viewpoint and 73% of graph edges are < 3 m, SR is tolerant to off-by-one-node stopping; NE penalty is mild (3/(3+NE)).
- The 112-word LLM-expanded instructions are the main transfer risk: DUET-family tokenizers fit them (200 wordpieces) but published evidence (GSA-R2R, HA-VLN 2.0) suggests 10-30 SR points lost without adaptation; three mitigations exist and can be A/B tested on val_unseen in a day: LLM de-paraphrase to R2R style, fine-tune on HA-R2R train (10,819 eps) aligned to R2R viewpoint paths via trajectory_id, and/or ensemble both instruction forms.
- If the Phase-2 bundle keeps trajectory_id/instruction_id, the original 29-word R2R test instruction can be looked up in public R2R_test.json / R2R_VLNCE test.json.gz and fed to the discrete agents, removing the paraphrase problem entirely (rules risk: external public data - no rule forbids it, but flag for the strategy lead).
- No feature extraction or MP3D skybox download is required: released hdf5/lmdb features already cover the 18 test scans. Re-rendering (MatterSim or Habitat with HAPS humans inserted) is optional and introduces a render-domain gap that cost Sim-2-Sim ~20 SR points for a 2021 model; ScaleVLN/SRDF should be less sensitive because they were pretrained on Habitat renders.
- Node positions must be converted MP3D(z-up) -> Habitat(y-up) and snapped to the navmesh; the CWP adapted graphs already do this, and VLN-CE's own conversion defines the goals, so viewpoint->goal offsets should be a few decimetres (verify on val splits).
- Discrete agents never see humans (features are of empty scans); that is acceptable for goal proposal, and the human-activity sentences are mostly redundant with route text, but the executor must handle humans (static obstacles) separately.

## Recommendations

1. Top-3 goal-proposal engines: (1) ScaleVLN DUET CLIP-H/14+EnvEdit - download HF OpenGVLab/ScaleVLN r2r_preprocess_data.zip + features.zip + r2r_trained_models.zip, run map_nav_src with --resume_file duet_vit-h14_ft_best_val_unseen --test on the 18 test scans (zero training; 80/70 test). (2) SRDF - download HF ZunWang/SRDF model_step_170000.pt + internvit_6b_fov60_mp3d.hdf5 (+panogen) and fine-tune per README (feat dim 3200, 1 A100-day) -> ~85 SR; also fine-tune a second copy on HA-R2R-train instructions. (3) NavGPT-2 FlanT5-XXL (HF ZGZzz, EVA-CLIP-g lmdb; 71.8/60.3) for instruction-style robustness, rationales and ensemble diversity. Add MAGIC-L and GOAT (HF crystal61; CLIP-B/16 'clip768') as cheap extra voters; skip BEVBert/GridMM unless depth grid features are downloaded (80-token limit, extra pipeline).
2. Build an offline 'graph beam search' harness: from the start viewpoint (nearest connectivity node to the episode start, after z-up->y-up conversion), run each agent (a) greedily, (b) with beam width 8-16 and state-factored search over the graph, (c) exhaustively scoring all simple paths of 3-8 nodes (~10^3-10^4 per episode) with teacher-forced log-likelihood + a speaker/instruction-generator likelihood (ScaleVLN/SRDF generators) + an optional VLM judge; fuse by rank voting on the goal node. Evaluate on val_unseen (1,839 eps) against GT goals to pick the recipe.
3. Instruction handling experiment (day 1): on val_unseen compare SR of each agent with (i) raw HA-R2R text, (ii) LLM de-paraphrased R2R-style text (prompt: 'strip human-activity sentences, keep route and stop condition, <=40 words'), (iii) the original R2R-CE instruction retrieved via trajectory_id/instruction_id. Then fine-tune ScaleVLN/SRDF on HA-R2R train+val_seen instructions mapped to R2R viewpoint paths (trajectory_id -> R2R path_id) with mixed original+HA text (GSA-R2R's GR-DUET recovered +8 SR this way).
4. Quantify the viewpoint->goal mapping on val splits: for each episode, distance between the R2R path end viewpoint (converted) and the episode goal; and the fraction of episodes whose start is within 0.5 m of a graph node. Use the CWP adapted graphs if any raw node is off-navmesh.
5. Measure the render-domain gap once: extract CLIP-H/14 features for val_unseen scans from Habitat renders at node poses (36 views, VFOV 60, 640x480) and compare ScaleVLN SR against the released MatterSim features; only if the gap is small consider human-inserted renders to exploit HA sentences as landmarks.
6. Do NOT spend effort on 'ETPNav-DE' (does not exist) or on zero-shot GPT navigators as proposers (<=44 SR); use LLMs only for de-paraphrasing, reranking and tie-breaking.
7. Keep the discrete proposer and the continuous executor decoupled: the proposer outputs a goal node (plus 2-3 ranked alternatives); the executor plans collision-free low-level actions on an inflated navmesh with humans as obstacles and verifies by local replay (other agents' topics C1/C2).

## Open questions

- Does the Phase-2 test bundle (and the val json) keep VLN-CE trajectory_id and instruction.instruction_id? If yes, original R2R instructions are recoverable; verify on val_unseen.json.gz immediately.
- Exact Sim-2-Sim 'graph-teleport' numbers (render gap in isolation) were not retrieved; re-measure locally with ScaleVLN on val_unseen (MatterSim features vs Habitat-render features).
- SRDF's exact test-unseen SR (paper table not retrievable here; ~85 per a 2026 survey) and whether a fine-tuned navigator checkpoint (not just model_step_170000.pt) is released.
- How much SR do ScaleVLN/SRDF lose on raw 112-word HA-R2R instructions vs original R2R-CE instructions (no published measurement; must be run on val_unseen).
- Whether competition rules permit offline use of connectivity graphs / public R2R test instructions / scene meshes (CONTEXT says no explicit prohibition; organisers list 'topological planners' as welcome).
- Lily's exact test row (single-run) and VER's absolute test numbers were not confirmed; both are superseded by ScaleVLN/SRDF anyway.
- Whether the raw MP3D graph nodes used by R2R-CE conversion coincide with CWP's adapted nodes for the 18 test scans (download the adapted graphs from the Discrete-Continuous-VLN GDrive link and diff).

## Sources

- https://arxiv.org/abs/2307.15644 (ScaleVLN, ICCV 2023) and https://openaccess.thecvf.com/content/ICCV2023/supplemental/Wang_Scaling_Data_Generation_ICCV_2023_supplemental.pdf
- https://arxiv.org/abs/2412.08467 (SRDF, ICLR 2025); https://github.com/wz0919/VLN-SRDF
- https://arxiv.org/abs/2212.04385 (BEVBert); https://github.com/MarSaKi/VLN-BEVBert
- https://arxiv.org/abs/2307.12907 (GridMM); https://github.com/MrZihan/GridMM
- https://arxiv.org/abs/2202.11742 (DUET); https://github.com/cshizhe/VLN-DUET
- https://arxiv.org/abs/2110.13309 (HAMT); https://github.com/cshizhe/VLN-HAMT
- https://arxiv.org/abs/2011.13922 (Recurrent VLN-BERT); https://github.com/YicongHong/Recurrent-VLN-BERT
- https://arxiv.org/abs/2407.12366 (NavGPT-2); https://github.com/GengzeZhou/NavGPT-2
- https://arxiv.org/abs/2312.02010 (NaviLLM); https://github.com/zd11024/NaviLLM
- https://arxiv.org/abs/2404.10241 (GOAT); https://github.com/CrystalSixone/VLN-GOAT
- https://arxiv.org/abs/2406.17960 (MAGIC); https://github.com/CrystalSixone/VLN-MAGIC
- https://arxiv.org/abs/2307.11984 (Lily / YouTube-VLN)
- https://arxiv.org/abs/2409.18800 (MiniVLN); https://arxiv.org/abs/2603.15370 (NavGRPO, CVPR 2026 Findings); https://arxiv.org/abs/2607.01043 (DART-VLN); https://arxiv.org/abs/2503.11006 (FIGR); https://arxiv.org/abs/2403.14158 (VER); https://arxiv.org/abs/2511.18845 (UNeMo); https://arxiv.org/abs/2601.18492 (DV-VLN); https://arxiv.org/abs/2512.20940 (ETP-R1)
- https://arxiv.org/abs/2503.16394 (Do Visual Imaginations Improve VLN Agents, CVPR 2025 - test-unseen comparison table)
- https://arxiv.org/abs/2501.17403 (GSA-R2R, ICLR 2025); https://github.com/honghd16/GSA-VLN
- https://arxiv.org/abs/2311.17280 (Does VLN pretraining work with nonsensical instructions)
- https://arxiv.org/abs/2401.07314 (MapGPT); https://arxiv.org/abs/2309.11382 (DiscussNav)
- https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123730103.pdf (VLN-CE / R2R-CE conversion); https://jacobkrantz.github.io/vlnce/data
- https://arxiv.org/abs/2204.09667 (Sim-2-Sim); https://github.com/jacobkrantz/Sim2Sim-VLNCE
- https://arxiv.org/abs/2203.02764 (CWP / Discrete-Continuous-VLN); https://github.com/YicongHong/Discrete-Continuous-VLN; https://github.com/wz0919/waypoint-predictor
- https://arxiv.org/abs/2503.14229 (HA-VLN 2.0); https://arxiv.org/abs/2406.19236 (HA-VLN 1.0, NeurIPS 2024 D&B)
- https://arxiv.org/abs/2406.09798 (Sim-to-Real 3D Feature Fields; table with Sim-2-Sim 43/44)
- https://arxiv.org/abs/2110.05728 (beam-search block: EnvDrop 69, AuxRN 71)
- Local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/HA-VLN/HASimulator/HA-DE/connectivity/*.json; /HA-DE/tasks/HA/{eval.py,env.py,data/HA_val_unseen.json,README.md}; /Data/HA-R2R/README.md; /Data/HA-R2R-tools/collision_num_test.json
- Local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/ScaleVLN/VLN-DUET/{map_nav_src/r2r/parser.py,map_nav_src/utils/data.py,map_nav_src/scripts/r2r_h14_envedit_mix.sh,pretrain_src/config/r2r_pretrain_hm3d+mp3d+gibson_clip-h14.json}
- Local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/VLN-HAMT/preprocess/precompute_img_features_vit.py; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/VLN-BEVBert/precompute_features/{grid_mp3d_clip.py,grid_depth.py}; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/VLN-BEVBert/scripts/ft_r2r.bash; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/Recurrent-VLN-BERT/r2r_src/param.py
- Local: /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/{NavGPT-2,NaviLLM,VLN-GOAT,VLN-MAGIC,VLN-DUET,GridMM,Sim2Sim-VLNCE,Discrete-Continuous-VLN,waypoint-predictor,GSA-VLN}/README.md; /tmp/claude-0/-home-user-open-data-eval/4c7c4db8-da0f-59f9-9f52-b232ac0aa3b2/scratchpad/ext/Matterport3DSimulator/{connectivity/README.md,tasks/R2R/data/download.sh}
