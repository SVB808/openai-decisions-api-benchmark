"""Compare OpenAI Decisions API and Responses API on the same labeled routing task.
Requires openai>=3.26.0 and OPENAI_API_KEY. Live API calls cost money.
"""
import argparse
import csv
import json
import os
import random
import statistics
import time
from pathlib import Path

from openai import OpenAI

ROOT = Path(__file__).resolve().parent
CATEGORIES = {
    "billing": "Payments, charges, invoices, refunds, subscriptions, and billing disputes.",
    "technical": "Bugs, broken features, crashes, application errors, or troubleshooting.",
    "shipping": "Order shipping, delivery dates, delayed packages, and tracking.",
    "other": "Anything not covered by billing, technical, or shipping.",
}
DECISION_QUESTION = {
    "type": "choice",
    "name": "department",
    "instructions": "Route this customer message to the one best department. Choose other if no department matches.",
    "choices": [{"value": k, "description": v} for k, v in CATEGORIES.items()],
}
JSON_SCHEMA = {
    "type": "json_schema",
    "name": "routing_result",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {"department": {"type": "string", "enum": list(CATEGORIES)}},
        "required": ["department"],
        "additionalProperties": False,
    },
}


def classify(client, mode, message, model):
    start = time.perf_counter()
    if mode == "decisions":
        response = client.decisions.create(model=model, input=message, questions=[DECISION_QUESTION])
        elapsed = (time.perf_counter() - start) * 1000
        answer = response.answers[0]
        if answer.type == "refusal":
            raise ValueError("Decisions API refused the request")
        if answer.type != "choice":
            raise ValueError(f"Unexpected Decisions answer type: {answer.type}")
        return answer.choice, elapsed, answer.confidence, None

    prompt = (
        "Classify the customer message into exactly one department. "
        "The options are: " + json.dumps(CATEGORIES) + ". "
        "Select the best department; use other if none match."
    )
    response = client.responses.create(
        model=model,
        instructions=prompt,
        input=message,
        text={"format": JSON_SCHEMA},
    )
    elapsed = (time.perf_counter() - start) * 1000
    if not response.output_text:
        raise ValueError("Responses API returned no text")
    answer = json.loads(response.output_text)["department"]
    usage = response.usage
    return answer, elapsed, None, (usage.model_dump() if usage else None)


def summarize(rows):
    for mode in ("decisions", "responses"):
        group = [r for r in rows if r["api"] == mode]
        ok = [r for r in group if not r["error"]]
        latency = sorted(float(r["latency_ms"]) for r in ok)
        correct = sum(r["prediction"] == r["expected"] for r in ok)
        p95 = latency[max(0, int((len(latency) - 1) * 0.95))] if latency else None
        print(f"\n{mode.upper()} | successful {len(ok)}/{len(group)} | accuracy {correct}/{len(ok)}" if ok else f"\n{mode.upper()} | no successful calls")
        if latency:
            print(f"Median latency {statistics.median(latency):.1f} ms | p95 (nearest rank approximation) {p95:.1f} ms")
        print(f"Failed calls {len(group) - len(ok)} (excluded from accuracy and latency; reported separately)")
    for mode in ("decisions", "responses"):
        errors = [r for r in rows if r["api"] == mode and r["error"]]
        for r in errors[:3]:
            print(f"Error [{mode} id={r['id']}]: {r['error']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default=str(ROOT / "dataset.json"))
    parser.add_argument("--out", default=str(ROOT / "results.csv"))
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--runs", type=int, default=2, help="Repeated passes over the dataset")
    parser.add_argument("--limit", type=int, default=0, help="Limit dataset for smoke test; 0=all")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if not os.getenv("OPENAI_API_KEY"):
        parser.error("Set OPENAI_API_KEY in your terminal; never hard-code it")
    if args.runs < 1 or args.limit < 0:
        parser.error("--runs must be >=1 and --limit must be >=0")
    dataset = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    if args.limit:
        dataset = dataset[:args.limit]
    if not dataset:
        parser.error("Dataset is empty")
    randomizer = random.Random(args.seed)
    client = OpenAI(timeout=30.0, max_retries=0)
    print("Warming up each API once (not included in results)...")
    for mode in ("decisions", "responses"):
        try:
            classify(client, mode, "I need a refund for an extra charge.", args.model)
        except Exception as ex:
            print(f"Warning: {mode} warmup failed: {type(ex).__name__}: {ex}")
    tasks = [(sample, mode, repetition) for repetition in range(args.runs) for sample in dataset for mode in ("decisions", "responses")]
    randomizer.shuffle(tasks)
    rows = []
    for n, (sample, mode, repetition) in enumerate(tasks, 1):
        row = {"id": sample["id"], "run": repetition + 1, "api": mode, "expected": sample["label"], "prediction": "", "latency_ms": "", "confidence": "", "input_tokens": "", "output_tokens": "", "error": ""}
        try:
            predicted, ms, confidence, usage = classify(client, mode, sample["text"], args.model)
            row.update(prediction=predicted, latency_ms=f"{ms:.2f}", confidence=confidence if confidence is not None else "")
            if usage:
                row["input_tokens"] = usage.get("input_tokens", "")
                row["output_tokens"] = usage.get("output_tokens", "")
        except Exception as ex:
            row["error"] = f"{type(ex).__name__}: {ex}"
        rows.append(row)
        print(f"{n:>3}/{len(tasks)} {mode:>9} {sample['id']}: {row['prediction'] or 'ERROR'}")
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved raw results: {output}")
    summarize(rows)
    print("\nNote: Decisions usage is not recorded in the same way as Responses. Compare billed costs using Platform usage reports and published pricing, not unsupported token assumptions.")


if __name__ == "__main__":
    main()
