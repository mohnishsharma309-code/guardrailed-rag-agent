"""Run the golden set through the agent and score pass/fail per case.

Each case declares machine-checkable expectations:
  contains      — every string must appear in the answer (case-insensitive)
  contains_any  — at least one string must appear
  not_contains  — no string may appear
  refusal       — answer must read as a refusal
"""
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

load_dotenv()

from src.agent import run_agent
from src.guardrails import is_refusal

GOLDEN_SET = os.path.join(os.path.dirname(__file__), "golden_set.json")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


def score_case(case, answer: str):
    checks = case["checks"]
    lowered = answer.lower()
    failures = []

    for s in checks.get("contains", []):
        if s.lower() not in lowered:
            failures.append(f"missing expected text: {s!r}")
    any_list = checks.get("contains_any", [])
    if any_list and not any(s.lower() in lowered for s in any_list):
        failures.append(f"missing any of: {any_list}")
    for s in checks.get("not_contains", []):
        if s.lower() in lowered:
            failures.append(f"forbidden text present: {s!r}")
    if checks.get("refusal") and not is_refusal(answer):
        failures.append("expected a refusal")

    return {"passed": not failures, "failures": failures}


def main():
    with open(GOLDEN_SET, encoding="utf-8") as f:
        cases = json.load(f)

    results = []
    print(f"\nRunning {len(cases)} eval cases...\n")
    for case in cases:
        try:
            result = run_agent(case["question"])
            answer = result.answer
            error = None
        except Exception as e:  # noqa: BLE001 — evals must report, not crash
            answer, error = "", str(e)
        verdict = score_case(case, answer) if not error else {
            "passed": False, "failures": [f"exception: {error}"]}
        results.append({
            "id": case["id"], "type": case["type"],
            "question": case["question"],
            "answer": answer, **verdict,
        })
        mark = "PASS" if verdict["passed"] else "FAIL"
        print(f"[{mark}] {case['id']} ({case['type']})")
        for fl in verdict["failures"]:
            print(f"       - {fl}")

    passed = sum(1 for r in results if r["passed"])
    print(f"\n{passed}/{len(results)} cases passed.")

    os.makedirs(RESULTS_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = os.path.join(RESULTS_DIR, f"eval-{stamp}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"timestamp": stamp, "passed": passed, "total": len(results),
             "cases": results},
            f, indent=2,
        )
    print(f"Report written to {path}")
    return passed == len(results)


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
