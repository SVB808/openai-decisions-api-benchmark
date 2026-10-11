# Extended benchmark — single run

This is an optional upgrade of the existing repo. Keep the existing `benchmark.py`, `requirements.txt`, baseline results and README. The provided ZIP adds `dataset_200.json`, `benchmark_extended.py`, and `run_extended.sh`.

From the existing WSL repository directory, extract ZIP contents there and run `bash run_extended.sh`. The script reuses `.venv`, requests an API key if missing, and asks for a single confirmation before sending 400 billable requests (no warmups or retries).

Outputs: `extended_results.csv` and `extended_report.md`; upload both for analysis. Re-running the script sends another 400 requests and overwrites the results: **don't rerun unless intentionally repeating the paid benchmark**. It does not auto-push to GitHub.

The 200 unique strings represent 40 distinct intent scenarios with five paraphrases each, so treat findings as exploratory, not fully independent accuracy evidence. Synthetic labels should be reviewed before publication. API charges are account-specific: the runner hard-caps *request count*, not dollars. It will not continue if the request cap is exceeded.
