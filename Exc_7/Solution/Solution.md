## Part 1 

1. **Run the example** (section 1 of the notebook). It copies the whole topic
   twice. Why does the checker fail?

The checker fails because it does not remeber where did it stop. Every run it reads from the start of the topic.

## 1. Decision: Architecture A (state file)

- The job keeps the position (next offset per partition) in a small state file.
- Each run: `load_state()` → `read_new()` → write to STAGING → `publish()` → `save_state()`.
- Why A:
  - Simple: one tiny file, easy to inspect and debug.
  - Fast: reading a small JSON file is instant, while `lake_position()`
    has to scan the lake's Parquet metadata, which gets slower as the lake grows.
- Trade-off: two sources of truth (lake and state file) that can disagree.
  If a run crashes between `publish()` and `save_state()`, the data is
  already in the lake but the position is old, so the next run writes it
  again and creates duplicates. `check_all` does not test this exact crash
  point. Architecture B avoids it by deriving the position from the lake itself.

## 2. Result

- The job passes all five situations: no duplicates, no missing records, no lag.
- Why it works:
  - Files are written to STAGING first, which readers never see.
  - `publish()` is a single atomic rename, so the lake contains
    either a whole run or nothing.
  - The position is saved last, only after the data is safely in the lake.

## 3. Output of `check_all`
   # Exercise 7: From the log to the lake

reset: lake, staging and state deleted

situation                                 in lake  duplicates  missing  not loaded    run  check
-----------------------------------------------------------------------------------------------
1 first run                             4,400,000           0        0           0  24.2s  PASS
2 new records arrive, run again         4,500,000           0        0           0   3.1s  PASS
3 nothing new, run again                4,500,000           0        0           0   0.1s  PASS
4 run stops WHILE writing: right after  4,500,000           0        0     100,000         PASS
  ... then the next run                 4,600,000           0        0           0   3.0s  PASS
5 run stops AFTER writing: right after  4,600,000           0        0     100,000         PASS
  ... then the next run                 4,700,000           0        0           0   3.0s  PASS
-----------------------------------------------------------------------------------------------
Exactly once after every run: YES