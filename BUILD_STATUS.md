# QueueCraft — 2026-10-16

Source MVP implemented: three scheduling policies, strict JSON input, idle/job timeline, waiting/completion/turnaround/deadline metrics, HTML and JSON exports, synthetic fixture and automated tests.

Authorized destination supplied October 16: oshada28nilendra-debug/queuecraft. Existing source build resumed for feature-branch PR delivery. No deployment or auto-merge. See PR for current CI status.

Verification: Python 3.12, 11 unittest tests passed (including 648 schedules in exhaustive small-input invariant checks). CLI export passed. See evaluation/results.json for measured policy results. Visual browser inspection is not performed; HTML escaping and generation are covered by tests. Results describe a synthetic workload only.
