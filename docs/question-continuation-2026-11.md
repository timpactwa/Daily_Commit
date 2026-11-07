# Continued question research

Researched November 7, 2026. This edition adds questions in independently checked batches of 20 (ten per track). Scenarios are original teaching examples, not real incident reports. System-design facts cite primary documentation; debugging functions are original code verified through mutation and independent case-table oracles. Difficulty seeds are provisional editorial estimates. Existing IDs and question payloads are retained, except recalculated debugging placement flags.

Each checkpoint runs schema validation, the full Python suite (including regeneration), app build, and phone/desktop flows before the next batch is applied. The final PR also requires all five CI jobs before publication.

## Batch 1

Debugging functions: `running_max`, `rotate_right`. Five variants each.

| Primary source | Question IDs |
| --- | --- |
| [Redis SET](https://redis.io/docs/latest/commands/set/) | sd-caching-continuation-021, sd-caching-continuation-022 |
| [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) | sd-scaling-continuation-021, sd-scaling-continuation-022 |
| [PostgreSQL vacuuming](https://www.postgresql.org/docs/18/routine-vacuuming.html) | sd-databases-continuation-021, sd-databases-continuation-022 |
| [Redis Streams](https://redis.io/docs/latest/develop/data-types/streams/) | sd-async-messaging-continuation-021, sd-async-messaging-continuation-022 |
| [Azure circuit breakers](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker) | sd-reliability-continuation-021, sd-reliability-continuation-022 |

Checkpoint 1 passed: 224 bank questions (228 including contract fixtures), 208 Python tests, app build and 12 phone/desktop checks. All 204 previous payloads retained apart from placement flags.

