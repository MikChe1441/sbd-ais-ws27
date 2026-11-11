# Stage B — Decision record: Line Guardian

## Options

1. **Keep PostgreSQL, poll it better.** Several pollers, each for a subset of
   machines, each running `SELECT ... WHERE id > last_id`.
2. **Kafka for the readings.** Gateways produce every reading to a Kafka
   topic; detector instances consume it in a consumer group. PostgreSQL stays
   the system of record for the machine registry.

## Decision

**Option 2: Kafka.**

## Reasons (R1–R4)

- **R1 scale.** A single PostgreSQL has to absorb 100,000 INSERT/s *and* the
  pollers' reads; writes and reads compete. Kafka is an append-only log built
  for high throughput and scales by partitions.
- **R2 complete & ordered.** The `id > last_id` poller skips rows that commit
  out of id order (Stage A). Kafka's per-partition offset is monotonic and
  commit-ordered; key = `machine_id` puts all readings of a machine in one
  partition, in order, and a consumer group gives each partition to exactly
  one detector instance.
- **R3 fresh.** Polling adds latency and falls behind under load (Stage A).
  Consumers read as fast as they can; `linger.ms=5` keeps latency low.
- **R4 independent consumers.** Every new poller adds read load to the same
  DB. Kafka consumer groups are independent: an archive or dashboard can read
  the same topic without affecting the detector or PostgreSQL.

## Numbers

- Model cost: 3 ms per reading.
- Lab: 60 × 10 Hz = **600 readings/s** → 600 × 0.003 = **1.8 s CPU/s** →
  at least **2 detector instances**, plan for **3** with headroom.
- Rollout: 2,000 × 50 Hz = **100,000 readings/s** → 100,000 × 0.003 =
  **300 s CPU/s** → at least **300 detector instances**, plan for **400–500**
  with headroom.
- Partitions: at least as many as detector instances. Lab: **12** (5 machines
  per partition, 50 readings/s per partition, ~0.15 s CPU/s per partition).
  Rollout: **300–500**.
- Tipping point: PostgreSQL is fine while `readings/s × model cost` is small
  compared to the DB's spare capacity and the pollers' read rate. One
  temperature reading per minute is trivially fine. The tipping point is
  roughly when the write rate saturates the DB's commit/WAL throughput or the
  pollers' reads compete with the writes — a few thousand readings/s for a
  single PostgreSQL instance.

## Stage C — what was built

- Topic `readings`, 12 partitions, replication factor 1 (created **before**
  the plant starts, otherwise the first write auto-creates it with 1
  partition):
  ```bash
  docker exec -it kafka kafka-topics.sh --bootstrap-server localhost:9092 \
    --create --topic readings --partitions 12 --replication-factor 1
  ```
- `KafkaSink` in `plant.py`: key = `machine_id`, `acks=all`, idempotence,
  `linger.ms=5`, `lz4`, `murmur2_random`.
- `detector_service.py`: group `line-guardian`, `auto.offset.reset=latest`,
  producer key = `machine_id` to `anomalies`. On rebalance, the instance
  calls `model.forget()` for the machines of a revoked partition, so a
  partition that comes back does not carry a stale `next_seq` (which would
  count readings as missing).
- Run: `python3 plant.py --sink kafka` and 2–3 ×
  `python3 detector_service.py --name det-N`.
- Scoreboard: `python3 scoreboard.py`. Expected: R2 PASS, R3 PASS, detection
  PASS. If R2 fails, check that the topic has 12 partitions and the key is
  `machine_id`; if detection fails, check that all detector instances use the
  same group and that the plant ran long enough for two faults.
