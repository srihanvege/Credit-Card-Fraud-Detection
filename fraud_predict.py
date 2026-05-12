import argparse
import os
import sys

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support, roc_auc_score

from utils import FRAUD_MODEL_PATH, get_fraud_dataset_path


def _risk_label(prob: float, threshold: float) -> str:
    if prob < threshold * 0.4:
        return "low"
    if prob < threshold:
        return "elevated"
    return "high"


def _fmt_row(i: int, amount: float, time_s: float, prob: float, y_true: int, y_pred: int, threshold: float) -> str:
    band = _risk_label(prob, threshold)
    agree = "matches label" if y_pred == y_true else "differs from label"
    return (
        f"  [{i}] Amount=${amount:,.2f}  Time={time_s:,.0f}s  "
        f"P(fraud)={prob:.4f}  threshold={threshold:.2f}  pred={'fraud' if y_pred else 'legit'}  "
        f"true={'fraud' if y_true else 'legit'}  risk={band}  ({agree})"
    )


def _threshold_sweep(y_true: np.ndarray, y_prob: np.ndarray, thresholds: np.ndarray) -> None:
    print("\n--- How the alert threshold moves precision/recall (same held-out rows) ---")
    rows = []
    for t in thresholds:
        y_hat = (y_prob >= t).astype(int)
        prec, rec, f1, _ = precision_recall_fscore_support(
            y_true, y_hat, average="binary", pos_label=1, zero_division=0
        )
        rows.append((t, prec, rec, f1))
    print(f"{'thr':>6} {'precision':>10} {'recall':>10} {'f1':>10}")
    for t, prec, rec, f1 in rows:
        print(f"{t:6.2f} {prec:10.4f} {rec:10.4f} {f1:10.4f}")
    print(
        "Lower threshold → more fraud alerts (higher recall, more false alarms).\n"
        "Higher threshold → fewer alerts (higher precision on alerts, more missed fraud)."
    )


def run_demo(
    n_samples: int,
    threshold: float,
    seed: int,
    sweep: bool,
    sweep_size: int,
) -> None:
    if not os.path.exists(FRAUD_MODEL_PATH):
        raise FileNotFoundError("Trained model not found. Run fraud_train.py first.")

    print(
        "\n".join(
            [
                "",
                "=== Credit card fraud model demo ===",
                "Dataset: anonymized transactions. Columns V1–V28 are PCA-transformed features (not readable merchants).",
                "Amount and Time are the only directly interpretable fields in this public file.",
                "The real world adds velocity rules, device fingerprints, and issuer-specific scores—this is a simplified slice.",
                "",
            ]
        )
    )

    model = xgb.XGBClassifier()
    model.load_model(FRAUD_MODEL_PATH)

    path = get_fraud_dataset_path()
    csv_path = os.path.join(path, "creditcard.csv")
    df = pd.read_csv(csv_path)

    fraud_rate = df["Class"].mean()
    print(
        f"Loaded {len(df):,} rows. Overall fraud rate in file: {fraud_rate*100:.4f}% "
        f"({int(df['Class'].sum()):,} positives).\n"
    )

    if sweep:
        rng = np.random.RandomState(seed)
        if sweep_size > len(df):
            sweep_size = len(df)
        idx = rng.choice(df.index.values, size=sweep_size, replace=False)
        sub = df.loc[idx]
        X_s = sub.drop(columns=["Class"])
        y_s = sub["Class"].values.astype(int)
        prob_s = model.predict_proba(X_s)[:, 1]
        thr_grid = np.round(np.linspace(0.05, 0.95, 10), 2)
        _threshold_sweep(y_s, prob_s, thr_grid)
        print(
            "\nAUC on this random slice is only a rough sanity check (not a full test protocol):",
            f"{roc_auc_score(y_s, prob_s):.4f}",
        )

    sample = df.sample(n_samples, random_state=seed)
    X_sample = sample.drop(columns=["Class"])
    y_true = sample["Class"].values.astype(int)
    y_prob = model.predict_proba(X_sample)[:, 1]
    y_pred = (y_prob >= threshold).astype(int)

    print(f"\n--- {n_samples} random transactions (seed={seed}) at decision threshold {threshold:.2f} ---\n")
    amounts = sample["Amount"].values
    times = sample["Time"].values
    for i in range(len(sample)):
        print(_fmt_row(i, float(amounts[i]), float(times[i]), float(y_prob[i]), int(y_true[i]), int(y_pred[i]), threshold))

    print("\n--- Batch summary ---")
    print("Confusion matrix [rows=true, cols=pred] (fraud positive):")
    print(confusion_matrix(y_true, y_pred, labels=[0, 1]))
    print("\nClassification report:")
    print(classification_report(y_true, y_pred, digits=4, zero_division=0))

    misses = int(np.sum((y_pred == 0) & (y_true == 1)))
    false_alarms = int(np.sum((y_pred == 1) & (y_true == 0)))
    print(
        f"\nMissed frauds (model said legit, actually fraud): {misses}. "
        f"False alarms (model said fraud, actually legit): {false_alarms}."
    )
    print(
        "\nWhy it can feel 'gappy': extreme class imbalance means a model can look accurate while still missing many frauds; "
        "single-number accuracy hides the trade-off you care about in ops (alerts vs misses). "
        "Use precision/recall at a chosen alert rate, not accuracy alone."
    )


def _interactive_args() -> tuple[int, float, int, bool, int]:
    print("Configure the fraud demo (press Enter for defaults in brackets).\n")

    def read_int(prompt: str, default: int, min_v: int = 1) -> int:
        raw = input(prompt).strip()
        if raw == "":
            return default
        try:
            v = int(raw)
        except ValueError:
            print("Invalid integer—using default.", file=sys.stderr)
            return default
        return max(min_v, v)

    def read_float(prompt: str, default: float) -> float:
        raw = input(prompt).strip()
        if raw == "":
            return default
        try:
            return float(raw)
        except ValueError:
            print("Invalid float—using default.", file=sys.stderr)
            return default

    n_samples = read_int("How many random transactions to score [5]: ", 5, 1)
    threshold = read_float("Alert threshold on P(fraud) [0.5]: ", 0.5)
    threshold = min(0.999, max(0.001, threshold))
    seed = read_int("Random seed [0]: ", 0, 0)
    sweep_ans = input("Run a quick threshold sweep on a larger random slice? (y/N): ").strip().lower()
    sweep = sweep_ans in {"y", "yes"}
    sweep_size = 20_000
    if sweep:
        sweep_size = read_int("Rows to use for sweep (max ~full dataset) [20000]: ", 20_000, 1000)
    return n_samples, threshold, seed, sweep, sweep_size


def main() -> None:
    parser = argparse.ArgumentParser(description="Score sample transactions with the trained fraud model.")
    parser.add_argument("--n_samples", type=int, default=5, help="Number of random rows to print in detail")
    parser.add_argument("--threshold", type=float, default=0.5, help="Probability cutoff for fraud alert")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for sampling")
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="Also print precision/recall/F1 across thresholds on a larger random slice",
    )
    parser.add_argument("--sweep_size", type=int, default=20_000, help="Rows for threshold sweep when --sweep is set")
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt for sample count, threshold, and optional sweep",
    )
    args = parser.parse_args()

    if args.interactive:
        if not sys.stdin.isatty():
            parser.error("--interactive requires a TTY.")
        n_samples, threshold, seed, sweep, sweep_size = _interactive_args()
    else:
        n_samples, threshold, seed, sweep, sweep_size = (
            args.n_samples,
            args.threshold,
            args.seed,
            args.sweep,
            args.sweep_size,
        )

    if n_samples < 1:
        parser.error("--n_samples must be >= 1")

    run_demo(
        n_samples=n_samples,
        threshold=threshold,
        seed=seed,
        sweep=sweep,
        sweep_size=sweep_size,
    )


if __name__ == "__main__":
    main()
