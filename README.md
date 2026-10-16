# QueueCraft

A small offline discrete-event scheduling lab for CS students and developers comparing scheduling trade-offs. Runs FIFO, shortest-job-first (SJF) and earliest-deadline-first (EDF) on the **same** workload. Exports per-job results, metrics and a self-contained HTML timeline. No paid services or dependencies.

## Run

Requires Python 3.12+.

```sh
python queuecraft.py examples/workload.json --out output
python -m unittest discover -s tests -v
```

Open `output/index.html`; inspect `output/results.json` for machine-readable evidence. Output directory must not already exist, preventing accidental report replacement. Example results are included in `evaluation/`.

## Input

JSON array of objects with exactly `id`, `arrival`, `duration`, `deadline`. IDs are unique nonempty strings. All times are integer ticks, arrival/deadline nonnegative, duration positive. Deadlines are absolute, not relative. A deadline before arrival is accepted and will be infeasible. Empty workloads, duplicate IDs, floats, booleans, missing fields and invalid values fail explicitly. See `examples/workload.json`, a hand-authored **synthetic** workload, not a production benchmark.

## Assumptions

- One worker, no preemption, no context-switch cost, no I/O blocking, no job dependencies.
- Exact durations and deadlines are known at arrival; this is an oracle assumption for SJF.
- Work-conserving: pick an available job whenever idle; never wait deliberately for future arrivals.
- FIFO priority is arrival; SJF priority is duration; EDF priority is deadline. Ties resolve by arrival then original input index. All arrivals at a completion tick are admitted before selecting the next job.
- A job completing exactly at its deadline is on time. Missed jobs still execute.
- Simulation starts at tick zero, includes initial/intermediate idle intervals, and stops at final completion.

## Metrics

Waiting = start − arrival. Turnaround = completion − arrival. Tardiness = max(0, completion − deadline). Reports include each completion timestamp, mean waiting/turnaround/tardiness, deadline misses, makespan (final completion from tick zero), busy ticks and utilization = busy ticks / makespan.

## Architecture

Validation → sorted arrival events → ready heap → completion event → reports. The clock jumps between events instead of iterating through ticks. Each job enters/leaves the heap once: O(n log n) time and O(n) space, excluding rendering. Pure simulation functions do not mutate inputs. HTML escapes job IDs and needs no JavaScript/server.

## Measured example

Five synthetic jobs: FIFO mean wait 4.4 ticks and 2 deadline misses; SJF 3.0 ticks and 2 misses; EDF 3.2 ticks and 3 misses. These are exact results for this workload, not general superiority claims. In FIFO the waiting times are 0, 3, 9, 10, 0. SJF produces 0, 3, 4, 8, 0; EDF produces 0, 2, 6, 8, 0. EDF's urgent job starts too late because A cannot be preempted; serving D first then delays C.

## Verification and limitations

Tests cover expected schedules/metrics, idle intervals, boundary arrivals, deterministic ties, non-preemption, infeasible deadlines, malformed inputs, HTML escaping, input immutability and CLI overwrite refusal. An exhaustive invariant test evaluates 216 small workloads under all three policies (648 schedules). It checks no execution before arrival, no overlapping work, duration preservation and complete timeline accounting; it is not an optimality proof.

No real cluster, deployment, distributed clock, queue limits, priorities, aging or scheduler overhead. SJF may starve long jobs under continued arrivals, which this finite workload model does not simulate indefinitely. No policy is universally best. Very large logs may produce unwieldy HTML; use small teaching workloads. Browser visual layout has not been manually verified.

## Interview explanation

“I implemented event-driven scheduling with a priority heap, made tie-breaking and non-preemption explicit, and compared policies on identical inputs. I tested edge cases and exhaustive small-workload invariants rather than claiming one policy always wins.”
