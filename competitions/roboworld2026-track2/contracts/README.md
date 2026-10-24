# Interface contracts (JSON Schema draft 2020-12)

One schema per message type exchanged between workstreams (from `research/C5-multi-agent-organization-and-handoff.md` §4.3), with a valid
fixture per schema in `fixtures/`. File `Name_v1.schema.json` ↔ contract id `Name/1`. Every producer validates on write, every consumer on
read; a contract change is a new version (`Name/2`), never an edit. `tests/test_contracts_fixtures.py` validates all fixtures.

| Contract | Producer → Consumer |
|---|---|
| EpisodeInput/1, Observation/1 | W1 runner → agent (W3/W4/W5/W2) |
| InstructionProgram/1, Percept/1 | W3 → W4/W5/W2 |
| SubgoalProposal/1 | W4/W5 → W2 (the executor alone emits MOVE_FORWARD/STOP and owns the 500-action budget) |
| ExecutorReport/1 | W2 → W4/W5 |
| RolloutRecord/1, SelectionRecord/1 | runner/W5 → W6 (signed tape, no GT metrics) |
| ScoreRequest/1 → ScoreResult/1 | W6/W7 → W1 scorer (idempotent task id = sha256(request); cr_mode human_influenced) |
| PlanRequest/1 → PlanResult/1, GoalCandidates/1 | privileged, token-gated: teachers, Track B, oracle evaluation only |
| ExperimentRecord/1, SubmissionManifest/1, TaskBrief/1 | registry, submission ledger, agent briefs |
