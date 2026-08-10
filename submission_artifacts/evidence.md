# Audit Evidence Summary

Generated: 2026-08-10T16:04:28Z  |  Overall: PASS

| Requirement | Result | Evidence |
|---|---|---|
| Tokenizer integrity | PASS | Manifest record (submission_artifacts/manifests/registry_manifest.jsonl (24 records), submission_artifacts/manifests/shard_manifest.jsonl (178 records)) |
| Evaluation firewall | PASS | Blocked-shard event (deliberately poisoned candidate (a real openai_humaneval example) correctly flagged 'contaminated' by the same check used for real admission) |
| Packing correctness | PASS | Packed-batch report (packed/<lane>/*.npz shape validation + code-never-mixed rule (24 shards checked)) |
| Mixture compliance | PASS | Planned versus actual shares (planned {'Web': 50.0, 'Indic': 25.0, 'Code': 25.0} vs actual {'Indic': 22.1, 'Web': 52.0, 'Code': 25.8} (submission_artifacts/manifests/registry_manifest.jsonl token_count sums)) |
| OPUS audit trail | PASS | Candidate decision records (submission_artifacts/ledgers/opus_decisions.jsonl (24 records, one per registry shard)) |
| Crash recovery | PASS | Expected and resumed batch ids (two independent restores of ckpt-tt-run-audit-7dc60bd5-step000000005's dataloader cursor draw an identical next microbatch) |
| Replay | PASS | Original and replay hashes (original weight hash 72cf71fa9c468405... vs replay weight hash 72cf71fa9c468405... after 3 identical steps from ckpt-tt-run-audit-7dc60bd5-step000000005) |
| Learning trace | PASS | Loss linked to source data (submission_artifacts/ledgers/tt_training_log.jsonl rows resolved to packed/<lane>/doc_manifest.jsonl -> real routed/ source files) |
| Throughput | PASS | Performance report (2.97 steps/sec, 760.8 tokens/sec measured over 5 real training steps) |

Full event sequence: `run.log`. Machine-readable detail: `evidence.json`. Throughput numbers: `performance.json`.
