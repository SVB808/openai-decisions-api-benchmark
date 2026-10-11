# OpenAI Decisions API benchmark

A reproducible experiment comparing **POST /v1/decisions** and **POST /v1/responses** using the same model (`gpt-6-luna`) to route customer-support messages to four departments.

Official docs: https://developers.openai.com/api/docs/guides/decisions

## Fast setup (Windows PowerShell)

Extract the ZIP, open PowerShell in the extracted `decisions_api_benchmark` folder, and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run.ps1
```

The launcher installs packages, requests your key privately, performs a 4-request smoke check plus 2 warm-ups, then runs the 24-case 3-pass benchmark only if all smoke-check calls succeeded. API usage is billed. The key is kept only in the current process; it is not written to a file.

## Manual setup (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:OPENAI_API_KEY = 'YOUR_API_KEY'  # Set locally; never commit or share the key
python benchmark.py --limit 2 --runs 1
python benchmark.py --runs 3
```

On macOS/Linux, use `python3 -m venv .venv`, `source .venv/bin/activate`, and `export OPENAI_API_KEY='YOUR_API_KEY'`.

Each run makes two calls per sample, plus one warm-up per API. With the 24-entry dataset and `--runs 3`, that is 146 total calls. Running this incurs API charges and requires a funded OpenAI Platform project; ChatGPT subscription access is separate.

## Measurement methodology

- Identical model and classification categories; Decision API uses `choice`, Responses API uses structured JSON (`text.format`). The prompts differ because the API interfaces differ, so this is an *application task comparison*, not proof of identical computational work.
- Both endpoints get warm-up requests. Execution order is randomized with a fixed seed, and all requests run sequentially to avoid local concurrency interference.
- CSV captures each result, latency, label, confidence from Decisions, Responses token usage, and errors. **Error rows are excluded from latency and accuracy calculations but reported separately**.
- `accuracy` is computed only among successful calls; inspect the failure count. The 24 labels are manually assigned, and some cases are intentionally potentially ambiguous; review the gold labels before publishing conclusions.
- The script does not claim end-to-end cost comparisons; use the actual Platform billing/usage dashboard and provider pricing. Decisions currently charges for input tokens, with caveats for regions/long context.
- For publishable claims: scale to at least 100 manually reviewed cases, repeat 3–5 passes, record exact date, model, region, traffic conditions, sample count, accuracy, median latency, p95 latency, and failures. Avoid treating the provider's “10×” statement as your own finding.
- Decisions' returned `confidence` and option probabilities are estimates; calibrate against labeled examples before using an automatic-routing threshold.

## Files

`benchmark.py`: the benchmark. `dataset.json`: illustrative labeled examples. `results.csv`: created locally by a run.

## Extensions

1. Add `predicate` for “Does this request indicate subscription cancellation?”
2. Add `score` for incident priority with explicitly ordered levels.
3. Build a threshold-based `human_review` policy and evaluate coverage versus accuracy.
4. Move the routing capability behind a Java/Spring Boot API after establishing a baseline.

Do not send customer PII or company-confidential records to third-party APIs without authorization. Only use synthetic data here.


## Extended Benchmark — October 2026

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


### Limitations

- 200 messages represent 40 underlying scenarios with five paraphrases each.
- Labels are synthetic and have not been independently reviewed.
- One request per API per message; measurements are exploratory.
- API interfaces differ, so this is a workflow-level comparison.
- Reproducing this experiment incurs API usage charges.
