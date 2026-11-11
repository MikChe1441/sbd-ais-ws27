"""The anomaly detector as a Kafka service. YOUR CODE (Part 2, Stage C2).

The plumbing is here, the decisions (marked TODO) are yours. Contract with
the maintenance team: every reading goes through model.score(); every
reading with score >= model.threshold becomes ONE anomaly event,
model.anomaly_event(reading, score), as JSON, published to the topic
`anomalies`.

    python3 detector_service.py --name det-1
    python3 detector_service.py --name det-2          # one more instance
"""
import argparse
import json
import time

from confluent_kafka import Consumer, Producer

from model import BearingModel

ap = argparse.ArgumentParser()
ap.add_argument("--name", default="det-1", help="instance name (shows up in the scoreboard)")
ap.add_argument("--in-topic", default="readings", help="the topic the gateways write to")
ap.add_argument("--group", default="line-guardian", help="the consumer group of this detector")
ap.add_argument("--out-topic", default="anomalies")
ap.add_argument("--bootstrap", default="localhost:9092")
args = ap.parse_args()

model = BearingModel(instance=args.name)
consumer = Consumer({
    "bootstrap.servers": args.bootstrap,
    "group.id": args.group,
    "client.id": args.name,
    # "latest": a live detector only processes new readings. "earliest" would
    # replay the whole topic on a fresh group and make the detector fall behind.
    "auto.offset.reset": "latest",
})
producer = Producer({
    "bootstrap.servers": args.bootstrap,
    "client.id": args.name,
    "acks": "all",
    "enable.idempotence": True,
    "linger.ms": 5,
    "compression.type": "lz4",
})

# Which machines we have seen on which partition. A machine's readings all go
# to one partition (key = machine_id), so this maps 1:1. On revoke we forget
# the machines of that partition: if the partition later comes back to this
# instance, the model must not remember a stale next_seq (that would count
# readings as missing).
partition_machines = {}


def on_assign(_consumer, partitions):
    for tp in partitions:
        partition_machines.setdefault(tp.partition, set())


def on_revoke(_consumer, partitions):
    for tp in partitions:
        for mid in partition_machines.pop(tp.partition, set()):
            model.forget(mid)


consumer.subscribe([args.in_topic], on_assign=on_assign, on_revoke=on_revoke, on_lost=on_revoke)
print(f"[{args.name}] {args.in_topic} -> {args.out_topic} (Ctrl+C to stop)", flush=True)

readings = anomalies = 0
report_at = time.time() + 5
try:
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"[{args.name}] {msg.error()}")
            continue
        reading = json.loads(msg.value())
        partition_machines.setdefault(msg.partition(), set()).add(reading["machine_id"])
        score = model.score(reading)
        readings += 1
        if score is not None and score >= model.threshold:
            anomalies += 1
            event = model.anomaly_event(reading, score)
            # key = machine_id: all anomalies of a machine land in the same
            # partition, in order, for the maintenance team.
            producer.produce(args.out_topic, key=reading["machine_id"],
                             value=json.dumps(event))
        producer.poll(0)
        if time.time() >= report_at:
            print(f"[{args.name}] {readings:>9,} readings  {anomalies:>6,} anomalies  "
                  f"missing {model.missing}  out-of-order {model.out_of_order}", flush=True)
            report_at += 5
except KeyboardInterrupt:
    pass
finally:
    producer.flush(10)
    consumer.close()
    print(f"[{args.name}] stopped after {readings:,} readings, {anomalies:,} anomalies")
