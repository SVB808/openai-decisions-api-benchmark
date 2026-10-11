# Extended benchmark results

Date (local): 2026-10-11 09:37:32 UTC
Measured API calls: 400 (no retries; no warm-up calls)

|Metric|Decisions|Responses|
|---|---:|---:|
|Attempted calls|200|200|
|API failures|0|0|
|Correct predictions|198|194|
|Accuracy among successes|99.00%|97.00%|
|Median latency|126.84 ms|1468.97 ms|
|P95 latency (nearest rank)|183.70 ms|2263.81 ms|

**Median latency ratio (Responses / Decisions): 11.58×**

## Accuracy by category

|API|Category|Correct / successful|Accuracy|
|---|---|---:|---:|
|decisions|billing|50/50|100.0%|
|decisions|technical|50/50|100.0%|
|decisions|shipping|50/50|100.0%|
|decisions|other|48/50|96.0%|
|responses|billing|50/50|100.0%|
|responses|technical|50/50|100.0%|
|responses|shipping|50/50|100.0%|
|responses|other|44/50|88.0%|

## Disagreements / misclassifications

|ID|API|Gold label|Prediction|Confidence|
|---|---|---|---|---|
|oth-10-1|responses|other|technical||
|oth-03-1|decisions|other|technical|0.59|
|oth-03-3|responses|other|technical||
|oth-03-2|responses|other|technical||
|oth-03-4|decisions|other|technical|0.43|
|oth-03-4|responses|other|technical||
|oth-10-2|responses|other|technical||
|oth-03-1|responses|other|technical||

## Interpret with care

- 200 distinct strings, but only 40 underlying intent scenarios paraphrased five ways: examples are correlated; do not treat this as 200 independent business situations.
- Labels are synthetic, template-assigned and should be reviewed for ambiguity before publication.
- One call per API per example: latency is exploratory; time-of-day, transient service conditions, network, and request structure can affect results.
- Comparison uses different interfaces (`choice` vs structured JSON); it measures workflows, not identical internal computation.
- Results exclude failed API calls from accuracy and latency; failures are reported separately.
- Confidence is an estimate, not a calibrated probability; cost requires actual Platform usage records.
- This run disables automatic retries and caps measured requests. It cannot guarantee a precise dollar cost before billing posts.
