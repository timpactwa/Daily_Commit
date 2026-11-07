# Research-backed question expansion

Researched November 7, 2026. Adds 50 original system-design scenarios and 50 mutation-verified debugging questions. The factual explanations below cite primary documentation; scenario workloads and numbers are teaching examples, not claims about real incidents. No interview question bank was copied.

## Editorial rules

- Every new system-design explanation contains a direct source link, displayed after grading. PostgreSQL links pin the reviewed major version (18). Other vendor pages are living documentation.
- Existing question IDs are retained. New question IDs use the research suffix. Difficulty values are editorial seed estimates, not measured vendor ratings; live Elo updates calibrate them.
- The new system-design questions span seed ratings 850–1550. New debugging functions use explicit difficulty offsets to represent algorithm complexity; these are also provisional estimates.
- Debugging code is original. Fifteen new functions have independent oracle-generated case tables, including empty/boundary/duplicate/negative inputs where allowed. Each retained mutation changes one line and fails a case. Timeouts, subprocess crashes and answer leakage are rejected; a function exception can be a valid failing case and is shown by name. These checks establish correctness against the stated test domain, not a formal proof for every possible input.

## Source register and question mapping

| Source | Primary documentation | New question IDs |
| --- | --- | --- |
| RFC 9111 | [RFC 9111](https://www.rfc-editor.org/rfc/rfc9111.html) | sd-caching-research-011, sd-caching-research-012 |
| RFC 9110 §13.1.2 | [RFC 9110 §13.1.2](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.2) | sd-caching-research-013 |
| RFC 5861 §4 | [RFC 5861 §4](https://www.rfc-editor.org/rfc/rfc5861.html#section-4) | sd-caching-research-014 |
| Redis eviction | [Redis eviction](https://redis.io/docs/latest/develop/reference/eviction/) | sd-caching-research-015, sd-caching-research-016 |
| Redis client caching | [Redis client caching](https://redis.io/docs/latest/develop/reference/client-side-caching/) | sd-caching-research-017 |
| CloudFront cache keys | [CloudFront cache keys](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/QueryStringParameters.html) | sd-caching-research-018 |
| Azure Cache-Aside | [Azure Cache-Aside](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside) | sd-caching-research-019 |
| Memcached protocol | [Memcached protocol](https://docs.memcached.org/protocols/basic/) | sd-caching-research-020 |
| Kubernetes HPA | [Kubernetes HPA](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/) | sd-scaling-research-012, sd-scaling-research-013 |
| Kubernetes probes | [Kubernetes probes](https://kubernetes.io/docs/concepts/workloads/pods/probes/) | sd-scaling-research-011, sd-reliability-research-018 |
| Kubernetes PDBs | [Kubernetes PDBs](https://kubernetes.io/docs/tasks/run-application/configure-pdb/) | sd-scaling-research-014 |
| gRPC load balancing | [gRPC load balancing](https://grpc.io/docs/guides/custom-load-balancing/) | sd-scaling-research-015 |
| NGINX balancing | [NGINX balancing](https://docs.nginx.com/nginx/admin-guide/load-balancer/http-load-balancer/) | sd-scaling-research-016 |
| DynamoDB key design | [DynamoDB key design](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-partition-key-design.html) | sd-scaling-research-017 |
| AWS scheduled scaling | [AWS scheduled scaling](https://docs.aws.amazon.com/autoscaling/ec2/userguide/ec2-auto-scaling-scheduled-scaling.html) | sd-scaling-research-018 |
| Kubernetes resources | [Kubernetes resources](https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/) | sd-scaling-research-019 |
| ALB slow start | [ALB slow start](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html#slow-start-mode) | sd-scaling-research-020 |
| PostgreSQL indexes | [PostgreSQL indexes](https://www.postgresql.org/docs/18/indexes-multicolumn.html) | sd-databases-research-012, sd-databases-research-013 |
| PostgreSQL EXPLAIN | [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/18/using-explain.html) | sd-databases-research-014 |
| PostgreSQL constraints | [PostgreSQL constraints](https://www.postgresql.org/docs/18/ddl-constraints.html) | sd-databases-research-011 |
| PostgreSQL isolation | [PostgreSQL isolation](https://www.postgresql.org/docs/18/transaction-iso.html) | sd-databases-research-015, sd-databases-research-016 |
| PostgreSQL SELECT | [PostgreSQL SELECT](https://www.postgresql.org/docs/18/sql-select.html#SQL-FOR-UPDATE-SHARE) | sd-databases-research-017 |
| PostgreSQL hot standby | [PostgreSQL hot standby](https://www.postgresql.org/docs/18/hot-standby.html) | sd-databases-research-018 |
| PostgreSQL pruning | [PostgreSQL pruning](https://www.postgresql.org/docs/18/ddl-partitioning.html#DDL-PARTITION-PRUNING) | sd-databases-research-019 |
| PostgreSQL CREATE INDEX | [PostgreSQL CREATE INDEX](https://www.postgresql.org/docs/18/sql-createindex.html#SQL-CREATEINDEX-CONCURRENTLY) | sd-databases-research-020 |
| SQS visibility | [SQS visibility](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html) | sd-async-messaging-research-012, sd-async-messaging-research-013 |
| SQS dead-letter queues | [SQS dead-letter queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-dead-letter-queues.html) | sd-async-messaging-research-014 |
| SQS FIFO ordering | [SQS FIFO ordering](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-understanding-logic.html) | sd-async-messaging-research-015 |
| SQS deduplication | [SQS deduplication](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html) | sd-async-messaging-research-016 |
| Apache Kafka design | [Apache Kafka design](https://kafka.apache.org/41/design/design/) | sd-async-messaging-research-017, sd-async-messaging-research-018 |
| RabbitMQ acknowledgements | [RabbitMQ acknowledgements](https://www.rabbitmq.com/docs/confirms) | sd-async-messaging-research-019 |
| AWS transactional outbox | [AWS transactional outbox](https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html) | sd-async-messaging-research-020 |
| Azure async request-reply | [Azure async request-reply](https://learn.microsoft.com/en-us/azure/architecture/patterns/asynchronous-request-reply) | sd-async-messaging-research-011 |
| Google SRE objectives | [Google SRE objectives](https://sre.google/sre-book/service-level-objectives/) | sd-reliability-research-011, sd-reliability-research-012 |
| Google SRE monitoring | [Google SRE monitoring](https://sre.google/sre-book/monitoring-distributed-systems/) | sd-reliability-research-013 |
| AWS Builders Library | [AWS Builders Library](https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/) | sd-reliability-research-014, sd-reliability-research-015 |
| Google SRE overload | [Google SRE overload](https://sre.google/sre-book/handling-overload/) | sd-reliability-research-016 |
| Azure Bulkhead | [Azure Bulkhead](https://learn.microsoft.com/en-us/azure/architecture/patterns/bulkhead) | sd-reliability-research-017 |
| AWS recovery objectives | [AWS recovery objectives](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_planning_for_recovery_objective_defined_recovery.html) | sd-reliability-research-019 |
| Google SRE canaries | [Google SRE canaries](https://sre.google/workbook/canarying-releases/) | sd-reliability-research-020 |

## Reproducing the debugging bank

`python -m pipeline check` verifies original function cases. `python -m pipeline build` regenerates the committed debugging JSON. Each new case module sets its prompt, a per-function question cap, and a provisional difficulty offset. The additions contribute ten questions to each debugging topic.

Run `python contracts/validate.py` and `pytest api engine pipeline` before merging. The research validation script also checks the 100-question delta, source coverage, topic balance, ID preservation and every added mutant’s failing/fixed behavior.

## Expansion audit

The bank grows from 104 to 204 questions: 50 new system-design questions and 50 generated debugging questions. Every one of the ten topics receives ten additions. All 104 previous IDs remain, and their prompts, answers, explanations, code and seed ratings are unchanged. The pipeline recalculates its three placement candidates per debugging topic against the larger bank, so some placement flags move.

Using the provisional seed bands below 1150 / 1150–1299 / 1300 and above, the additions contain 38 beginner, 32 intermediate and 30 advanced questions. These bands describe editorial question seeds, not a validated prediction of a candidate's job level.

New formats: 31 multiple-choice, 9 reorder, 10 tap-node, and 50 tap-line. Citation rendering accepts HTTPS links and leaves unsupported markup as escaped text. Source links appear after grading, while explanations remain private before submission.

The debugging checks rerun every new mutant and its exact one-line repair; all added mutants fail a case and every repair restores the original passing function. Separate stdlib/brute-force oracles verify all new case tables. Exhaustive short-input checks additionally cover the three sorting functions, sliding-window uniqueness and prefix-sum subarray counting.
