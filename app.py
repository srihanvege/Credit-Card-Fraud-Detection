"""Minimal web UI for the eligibility recommender."""

from __future__ import annotations

from flask import Flask, jsonify, render_template, request

from eligibility_recommender import UserProfile, recommend_cards_structured

app = Flask(__name__)


def _opt_float(val) -> float | None:
    if val is None or val == "":
        return None
    return float(val)


def _opt_int(val) -> int | None:
    if val is None or val == "":
        return None
    return int(val)


def _parse_profile(data: dict) -> UserProfile:
    for key in ("credit_score", "annual_income", "housing"):
        if key not in data:
            raise ValueError(f"Missing required field: {key}")

    loc = (data.get("location") or "US").strip()
    housing = (data.get("housing") or "").strip().lower()
    if housing not in {"rent", "own", "other"}:
        raise ValueError("Housing must be rent, own, or other.")

    cs = int(data["credit_score"])
    if cs < 300 or cs > 850:
        raise ValueError("Credit score must be between 300 and 850.")

    income = float(data["annual_income"])
    if income < 0:
        raise ValueError("Income cannot be negative.")

    return UserProfile(
        credit_score=cs,
        annual_income=income,
        location=loc or "US",
        housing=housing,
        credit_history_years=_opt_float(data.get("credit_history_years")),
        debt_to_income_ratio=_opt_float(data.get("debt_to_income_ratio")),
        employment_years=_opt_float(data.get("employment_years")),
        recent_hard_inquiries_12m=_opt_int(data.get("recent_hard_inquiries_12m")),
        estimated_monthly_card_spend=_opt_float(data.get("estimated_monthly_card_spend")),
        is_student=bool(data.get("is_student")),
    )


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/recommend")
def api_recommend():
    data = request.get_json(silent=True) or {}
    try:
        profile = _parse_profile(data)
    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": str(e) or "Invalid input"}), 400

    return jsonify(recommend_cards_structured(profile))


if __name__ == "__main__":
    app.run(debug=True, port=5050)
