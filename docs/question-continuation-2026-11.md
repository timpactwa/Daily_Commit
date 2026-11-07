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


## Batch 2

Debugging functions: `count_occurrences`, `minimum_rotated`. Five variants each.

| Primary source | Question IDs |
| --- | --- |
| [Redis EXPIRE](https://redis.io/docs/latest/commands/expire/) | sd-caching-continuation-023, sd-caching-continuation-024 |
| [Kubernetes StatefulSets](https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/) | sd-scaling-continuation-023, sd-scaling-continuation-024 |
| [PostgreSQL partial indexes](https://www.postgresql.org/docs/18/indexes-partial.html) | sd-databases-continuation-023, sd-databases-continuation-024 |
| [RabbitMQ TTL](https://www.rabbitmq.com/docs/ttl) | sd-async-messaging-continuation-023, sd-async-messaging-continuation-024 |
| [Azure health monitoring](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring) | sd-reliability-continuation-023, sd-reliability-continuation-024 |

Checkpoint 2 passed: 244 bank questions (248 with fixtures), 213 Python tests, app build and 12 phone/desktop checks.

