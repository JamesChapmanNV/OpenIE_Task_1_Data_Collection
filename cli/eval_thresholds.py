#!/usr/bin/env python
"""
Evaluate PR/ROC/F1 on a labeled devset to pick a KEEP threshold.

Input CSV: the file produced & annotated from sample_for_labeling.py
Required columns:
  score (float), gold_keep (0/1)

Outputs:
  - Prints PR@threshold, F1, ROC-AUC
  - Recommends KEEP_MIN by maximizing F1 (tie-break by higher precision)
  - Optional: writes a thresholds_report.csv with metrics across thresholds

Usage:
  python cli/eval_thresholds.py --labels labels_devset.csv --report thresholds_report.csv
"""
import argparse, csv, math
from typing import List, Tuple
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score, average_precision_score

def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True, help="Path to labeled CSV with 'score' and 'gold_keep'")
    ap.add_argument("--report", default=None, help="Optional: CSV path to dump per-threshold metrics")
    return ap.parse_args()

def _load(labels_csv: str) -> Tuple[List[float], List[int]]:
    y_true, y_score = [], []
    with open(labels_csv, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            g = row.get("gold_keep", "").strip()
            s = row.get("score", "").strip()
            if g in ("0","1") and s not in ("", "nan"):
                try:
                    y_true.append(int(g))
                    y_score.append(float(s))
                except ValueError:
                    pass
    if not y_true:
        raise RuntimeError("No labeled rows with gold_keep in {0,1} and valid scores.")
    return y_score, y_true

def _sweep_thresholds(y_score: List[float], y_true: List[int]):
    lo, hi = min(y_score), max(y_score)
    if hi <= lo:
        # Degenerate—use a slim range around the single value
        thresholds = [lo - 1e-6, lo, lo + 1e-6]
    else:
        # 101 evenly spaced thresholds in [lo, hi]
        step = (hi - lo) / 100.0
        thresholds = [lo + i*step for i in range(101)]
    results = []
    for t in thresholds:
        y_pred = [1 if s >= t else 0 for s in y_score]
        p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="binary", zero_division=0)
        results.append((t, p, r, f1))
    return results

def main():
    args = parse_args()
    y_score, y_true = _load(args.labels)

    # Summary metrics (independent of threshold)
    try:
        roc = roc_auc_score(y_true, y_score)
    except Exception:
        roc = float("nan")
    try:
        ap = average_precision_score(y_true, y_score)
    except Exception:
        ap = float("nan")

    sweep = _sweep_thresholds(y_score, y_true)

    # Pick threshold by F1, break ties by higher precision, then by higher threshold
    best = max(sweep, key=lambda x: (x[3], x[1], x[0]))
    keep_min = best[0]

    print("=== Devset summary ===")
    print(f"ROC-AUC: {roc:.4f}")
    print(f"Avg Precision (PR-AUC): {ap:.4f}")
    print()
    print(" t\tPrec\tRec\tF1")
    for t,p,r,f1 in sweep[::10]:  # print every ~10th
        print(f"{t:6.2f}\t{p:5.2f}\t{r:5.2f}\t{f1:5.2f}")
    print()
    print(f"Recommended KEEP_MIN by max F1: {keep_min:.2f}")
    print(f"(At t={keep_min:.2f})  Precision={best[1]:.3f}  Recall={best[2]:.3f}  F1={best[3]:.3f}")

    if args.report:
        with open(args.report, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["threshold","precision","recall","f1"])
            for t,p,r,f1 in sweep:
                w.writerow([f"{t:.6f}", f"{p:.6f}", f"{r:.6f}", f"{f1:.6f}"])
        print(f"Wrote per-threshold metrics → {args.report}")

if __name__ == "__main__":
    main()

# Example usage:
# python cli/eval_thresholds.py --labels labels_devset.csv --report thresholds_report.csv
# Note the "Recommended KEEP_MIN ..." line
