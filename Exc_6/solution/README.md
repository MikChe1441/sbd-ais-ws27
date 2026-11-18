# Exercise 6 - Card Sentinel

## Part 1: How the payments reach the models

I choose option 4, log based CDC with Debezium. The payment path is owned by
another team and is certified, so we may not change it (R1). Polling would add
query load to the database for every reader and would miss payments that commit
out of id order, as the poller of Exercise 5 did. Dual write would change the
payment path, and it can lose an event if the application crashes after the
database commit, or invent an event if it sends before the commit. An outbox is
correct, but it also changes the payment path. Debezium only reads the write
ahead log, so the payment path stays untouched, there is no extra query load,
and every commit arrives in commit order (R2). The cost is the replication
slot: PostgreSQL keeps all WAL that the connector has not read yet. If the
connector stops for a long time, for example over a weekend, the disk can fill
up and the database, and with it the payment path, can stop. In production I
would notice this before it hurts by monitoring the slot lag and the free disk
space and by alerting when the lag grows. If my team owned the payment path, I
would choose the outbox, because it gives the same guarantees without depending
on a replication slot.

## Part 2: the three runs

### Run 1: default settings

Prediction: the topic will get one partition, so only one velocity instance will
receive work and the other two will stay idle. The backlog will grow and R4 will
fail.

Result for the velocity model:

```
R3  frauds caught          4/11  (36%)    FAIL
R3  false alerts           0            PASS
R4  alert latency p50/p95  80.8 s / 107.0 s   FAIL
```

Why: the topic was created with one partition, because nobody set the number of
partitions. Inside a consumer group one partition is read by exactly one
instance, so vel-2 and vel-3 printed `assigned partitions []` and did nothing.
One instance handles about 400 to 550 payments per second, while 1000 arrive
every second, so the lag grew and alerts came too late. The anomaly model passed
(R3 11/11, R4 p95 0.9 s), because one instance can handle the whole rate.

### Run 2: six partitions

I added `topic.creation.default.partitions` with value 6 and
`topic.creation.default.replication.factor` with value 1.

Prediction: all three instances will get two partitions each and keep up, so R4
will pass. But the key is still the primary key `id`, so the payments of one
stolen card will be spread over the partitions and the velocity model will catch
almost no frauds, so R3 will fail.

Result for the velocity model:

```
R3  frauds caught          1/13  (8%)     FAIL
R3  false alerts           0            PASS
R4  alert latency p50/p95  0.8 s / 0.8 s   PASS
```

Why: every instance got two partitions (`vel-1` got 0 and 1, `vel-2` got 2 and 3,
`vel-3` got 4 and 5) and the lag stayed below one second, so freshness was
fixed. Detection was not: the key is the payment id, the partition is chosen
from the key, so the 12 test payments of one card landed on random partitions.
Each instance saw only about four of them in the 60 second window, below the
threshold of 8, so nobody alerted. The anomaly model still passed (R3 13/13),
because it runs as one instance and reads all six partitions.

### Run 3: the cardholder as the key

I added `message.key.columns` with value `public.transactions:user_id`.

Prediction: the key of an event will now be the user_id, all payments of one
cardholder will land in the same partition, and the velocity model will catch
its frauds. Both R3 and R4 will pass.

Result for the velocity model:

```
R3  frauds caught          23/23  (100%)   PASS
R3  false alerts           1            PASS
R4  alert latency p50/p95  0.7 s / 1.0 s   PASS
```

Why: all payments of one cardholder now go to the same partition and are read by
the same instance, in commit order. That instance sees the whole burst and alerts
at the eighth payment. One false alert appeared, an honest cardholder who paid
eight times within a minute, which the rules allow. The anomaly model passed as
well (R3 23/23, R4 p95 0.9 s). This is the final design.

## Closing answer

Debezium chose two defaults for us: one partition for the topic, and the primary
key of the table as the event key. Both are reasonable for copying a table and
both are wrong for a stateful model that has to scale. In production, if nobody
had checked them, nothing would have crashed and no error would have appeared.
The pipeline would look healthy while the fraud model caught fewer and fewer
frauds: first it would fall behind and alerts would arrive too late to block a
card, then, after adding partitions, each instance would see only a part of an
attack. The team could have noticed by watching consumer lag and the number of
partitions in the Kafka UI, by looking at which partitions each instance was
assigned to, and above all by measuring the model against known fraud cases, the
way the scoreboard does. Monitoring is not enough on its own, because the system
stays green while detection quality silently drops.
