**Stage A: Today’s system**
*Question 1:* The detector keeps up, but readings are reported as “missing”. Are they really missing from the table? Why didn’t the detector see them?

Answer: The missing readings are in the table: SELECT count(*) for the run returns 6,100, the same as the 6,100 readings the plant sent. The detector read only 5,056 and counted 1,044 missing (5,056 + 1,044 = 6,100). It kept up (backlog under 35 rows, delay about 0.2 s), so this is not a speed problem. id is a BIGSERIAL assigned at INSERT, but a row is visible to others only after COMMIT, and each gateway sleeps a random 0-120 ms before committing (see PostgresSink in plant.py). In the timeline, gateway 2 commits ids 115-129 immediately, a poll in between sees them and remembers last_id = 129, and ids 100-114 commit afterwards. WHERE id > 129 never returns them, so they are skipped permanently.


*Question 2:* With the full plant running, what happens to delay, backlog and missing, and why?

Answer: The model needs 3 ms per reading. At 600 readings per second that is 1.8 seconds of work for every second that passes. One detector can only process about 333 readings per second.

backlog keeps growing, by roughly 270 rows per second. After 60 s it was about [X].
delay keeps growing as well, because new readings wait behind the backlog. It reached about [Y] s, far above the 5 s limit.
missing [grew / your observation]. The commit-order problem from Question 1 gets worse with more gateways writing at once.

After the plant stops, the detector only works through its backlog.

Two separate problems: one detector is too slow (a capacity problem), and polling by id loses rows (a correctness problem).
**Stage B: Decision record**
*Question 3:* Compare the two options against the requirements. Which does each meet, and which are at risk?

The requirements are:

R1: it must scale to 100,000 readings per second
R2: the model gets every reading of a machine, in order
R3: alerts within 5 seconds
R4: other consumers (archive, dashboard) can be added without slowing down or breaking anything

Option 1: keep PostgreSQL and poll better (several pollers)

R1: only partly. PostgreSQL has to handle all the writes and all the polling reads.
R2: at risk. The commit-order problem remains. Workarounds exist (waiting a safety margin, other tricks), but they are fragile and add delay.
R3: possible only with frequent polling and many pollers, and every poll is a database query.
R4: fails. Every new consumer is another poller hitting the same table.

Option 2: gateways write to Kafka, detectors read as a consumer group

R1: met. Kafka scales by adding partitions.
R2: met if the key is the machine id. All readings of one machine go to the same partition, in order, and to one detector. The risk is a wrong key or too few partitions.
R3: met, but only with enough detector instances. Kafka fixes the lost-rows problem, but the 3 ms per reading still needs parallel instances.
R4: met. Each consumer group tracks its own position, so nothing interferes with anything else and PostgreSQL gets no extra load.
*Question 4:* What is your decision?

Answer: Option 2, Kafka. PostgreSQL stays in place as the system of record for the machine registry.

*Question 5:* How many detector instances are needed?

Answer:

Lab: 600 × 3 ms = 1.8 s of work per second, so at least 2 instances. Plan 3 for headroom.
Rollout: 100,000 × 3 ms = 300 s of work per second, so at least 300 instances. Aiming for about 70% load gives roughly 430, so plan about 500.
Partitions: at least as many as instances, since one partition feeds only one instance in a group. Use 12 for the lab and about 500 for the rollout.
*Question 6:* Where is the tipping point? A small office logs one temperature per minute. Option 1 is fine there, but when does it stop being fine?

Answer: One reading per minute is trivial for PostgreSQL. Raw write speed is usually not the first problem, since PostgreSQL can handle thousands of batched inserts per second. The switch to a log like Kafka makes sense when several of these come together:

the rate reaches hundreds to a few thousand events per second
several independent consumers need the same data
per-machine order and completeness matter
results are needed within seconds
you want to replay old data

The office has none of these, so option 1 is the right choice there.

Stage C (optional): Build it
----