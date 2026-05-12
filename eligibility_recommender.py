from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass

from card_catalog import CARDS, CardSpec


@dataclass
class UserProfile:
    credit_score: int
    annual_income: float
    location: str  # U.S. state code, region name, or free text
    housing: str  # rent | own | other
    credit_history_years: float | None
    debt_to_income_ratio: float | None  # 0-1 preferred; accepts 0-100
    employment_years: float | None
    recent_hard_inquiries_12m: int | None
    estimated_monthly_card_spend: float | None
    is_student: bool


def _normalize_dti(dti: float | None) -> float | None:
    if dti is None:
        return None
    d = float(dti)
    if d > 1:
        d = d / 100.0
    return max(0.0, min(d, 1.5))


def _location_note(location: str) -> str:
    loc = location.strip().upper()
    regional = {
        "TX": "Texas has many local credit unions—worth comparing if you want relationship banking.",
        "CA": "California users sometimes compare local CU cards with national issuers for fees and branches.",
        "NY": "NYC-heavy spend often fits dining/grocery multipliers; check transit benefits on specific products.",
        "FL": "Florida travelers sometimes lean airline cobrands—only if you actually use that airline.",
        "WA": "Pacific Northwest shoppers sometimes compare Chase (HQ region familiarity) vs other national issuers.",
    }
    if len(loc) == 2 and loc in regional:
        return regional[loc]
    if "NORTHEAST" in loc or loc in {"MA", "CT", "RI", "NH", "VT", "ME", "NJ", "PA"}:
        return "Northeast profiles vary; national issuers are usually comparable—focus on spend categories you already have."
    if "SOUTH" in loc or loc in {"GA", "NC", "SC", "TN", "AL", "MS", "LA", "AR", "OK", "KY", "WV", "VA"}:
        return "Southern states have strong national issuer availability; regional CU promos can be worth a look."
    if "MIDWEST" in loc or loc in {"OH", "MI", "IN", "IL", "WI", "MN", "IA", "MO", "KS", "NE", "ND", "SD"}:
        return "Midwest users often value simple no-annual-fee cash back unless travel is frequent."
    if "WEST" in loc or loc in {"CO", "UT", "AZ", "NM", "NV", "OR", "ID", "MT", "WY"}:
        return "Western states: compare travel cards if you fly often; otherwise flat cash back stays easy."
    return "Location mainly affects local CU promos and tax context; national card rules are mostly the same."


def _fit_score(profile: UserProfile, card: CardSpec) -> tuple[float, list[str]]:
    """Higher is better. Returns (score, reasons for tier messaging)."""
    notes: list[str] = []
    cs = profile.credit_score
    inc = profile.annual_income

    # Base credit overlap with typical issuer band (soft trapezoid)
    lo, hi = card.score_typical_min, card.score_typical_max
    if cs < lo:
        gap = lo - cs
        credit_part = max(0.0, 85.0 - gap * 1.2)
        notes.append(f"Below typical score band for this product (~{lo}+).")
    elif cs > hi + 60:
        credit_part = 95.0
        notes.append("Your score is above the typical band—you may be overqualified for starter products.")
    elif cs > hi:
        credit_part = 90.0
    else:
        credit_part = 100.0

    # Income vs annual fee comfort
    fee_penalty = 0.0
    if card.income_comfortable_min is not None and inc < card.income_comfortable_min:
        shortfall = card.income_comfortable_min - inc
        fee_penalty = min(35.0, shortfall / 2500.0 * 3.0)
        notes.append(
            f"Income under a rough comfort threshold (~${card.income_comfortable_min:,}/yr) for this fee level—check break-even carefully."
        )

    dti = _normalize_dti(profile.debt_to_income_ratio)
    dti_penalty = 0.0
    if dti is not None:
        if dti >= 0.45 and card.category in {"premium_travel", "travel", "charge"}:
            dti_penalty = 28.0
            notes.append("High debt-to-income reduces realistic approval odds for premium/travel cards.")
        elif dti >= 0.35:
            dti_penalty = 12.0
            notes.append("Elevated debt-to-income—issuers may offer lower limits or decline premium products.")

    history_penalty = 0.0
    ch = profile.credit_history_years
    if ch is not None and ch < 2 and lo >= 680:
        history_penalty = 22.0
        notes.append("Short credit history makes premium approvals less predictable.")

    inq_penalty = 0.0
    if profile.recent_hard_inquiries_12m is not None and profile.recent_hard_inquiries_12m >= 5:
        inq_penalty = 15.0
        notes.append("Many recent hard inquiries can hurt approval odds in the next few months.")

    # Product mismatch rules
    student_bonus = 0.0
    if card.category == "student" and profile.is_student:
        student_bonus = 10.0
        notes.append("Student-focused products can match well while you are enrolled.")

    mismatch_penalty = 0.0
    if card.category == "secured" and cs >= 700:
        mismatch_penalty = 40.0
        notes.append("You may not need a secured card at your score—compare unsecured options.")
    if card.category == "student" and not profile.is_student and cs >= 660:
        mismatch_penalty = 25.0
        notes.append("Student cards are best when you actually qualify as a student with the issuer.")
    if card.annual_fee_usd >= 250 and profile.estimated_monthly_card_spend is not None:
        annual_spend = profile.estimated_monthly_card_spend * 12
        if annual_spend < 1500:
            mismatch_penalty += 10.0
            notes.append("Low estimated card spend makes high-fee cards harder to justify via rewards alone.")

    raw = credit_part + student_bonus - fee_penalty - dti_penalty - history_penalty - inq_penalty - mismatch_penalty
    return max(0.0, min(100.0, raw)), notes


def _tier(fit: float, hard_skip: bool) -> str:
    if hard_skip:
        return "avoid"
    if fit >= 72:
        return "good"
    if fit >= 48:
        return "maybe"
    return "avoid"


def _hard_skip(profile: UserProfile, card: CardSpec) -> tuple[bool, str | None]:
    cs = profile.credit_score
    if card.category in {"premium_travel", "charge"} and cs < 640:
        return True, "Score is far below typical profiles for this premium/charge product."
    if card.category == "travel" and card.annual_fee_usd >= 300 and cs < 660:
        return True, "High-fee travel cards are unrealistic at this score range."
    if card.category == "secured" and cs >= 740:
        return True, "You likely qualify for stronger unsecured products—skip secured unless you have a specific reason."
    return False, None


def _format_card_block(card: CardSpec, tier_label: str, fit_notes: list[str]) -> list[str]:
    fee = "No annual fee" if card.annual_fee_usd == 0 else f"${card.annual_fee_usd}/yr annual fee"
    lines = [
        f"** {card.name} ** ({card.issuer}) — {fee} — [{tier_label}]",
        f"  Typical score band (rough): {card.score_typical_min}–{card.score_typical_max}",
        "  Pros:",
    ]
    for p in card.pros:
        lines.append(f"    + {p}")
    lines.append("  Cons:")
    for c in card.cons:
        lines.append(f"    − {c}")
    if card.avoid_if:
        lines.append("  When people often skip:")
        for a in card.avoid_if:
            lines.append(f"    · {a}")
    if fit_notes:
        uniq = list(dict.fromkeys(fit_notes))[:4]
        lines.append("  Notes for your profile:")
        for n in uniq:
            lines.append(f"    · {n}")
    return lines


def analyze_profile(profile: UserProfile) -> dict:
    """Run matching logic; used by text and JSON recommenders."""
    dti = _normalize_dti(profile.debt_to_income_ratio)
    good: list[tuple[CardSpec, float, list[str]]] = []
    maybe: list[tuple[CardSpec, float, list[str]]] = []
    avoid: list[tuple[CardSpec, float, list[str]]] = []

    for card in CARDS:
        hard, hard_reason = _hard_skip(profile, card)
        fit, notes = _fit_score(profile, card)
        if hard and hard_reason:
            notes = [hard_reason] + notes
        tier = _tier(fit, hard)
        entry = (card, fit, notes)
        if tier == "good":
            good.append(entry)
        elif tier == "maybe":
            maybe.append(entry)
        else:
            avoid.append(entry)

    good.sort(key=lambda x: -x[1])
    maybe.sort(key=lambda x: -x[1])
    avoid.sort(key=lambda x: x[1])

    housing = profile.housing.strip().lower()
    housing_hint = ""
    if housing == "rent":
        housing_hint = "Renters often value no-annual-fee cash back and emergency fund stability before premium fees."
    elif housing == "own":
        housing_hint = "Homeowners still benefit from the same break-even math—tie card fees to spend you already do."

    return {
        "good": good,
        "maybe": maybe,
        "avoid": avoid,
        "dti": dti,
        "location_note": _location_note(profile.location),
        "housing_hint": housing_hint or None,
    }


def _serialize_card_rows(entries: list[tuple[CardSpec, float, list[str]]], tier_slug: str) -> list[dict]:
    rows: list[dict] = []
    for card, fit, notes in entries:
        rows.append(
            {
                "id": card.id,
                "name": card.name,
                "issuer": card.issuer,
                "category": card.category,
                "annual_fee_usd": card.annual_fee_usd,
                "annual_fee_label": "No annual fee" if card.annual_fee_usd == 0 else f"${card.annual_fee_usd}/yr",
                "score_band": f"{card.score_typical_min}–{card.score_typical_max}",
                "pros": list(card.pros),
                "cons": list(card.cons),
                "avoid_if": list(card.avoid_if),
                "profile_notes": list(dict.fromkeys(notes))[:6],
                "fit_score": round(fit, 1),
                "tier_slug": tier_slug,
            }
        )
    return rows


def recommend_cards_structured(profile: UserProfile) -> dict:
    """API/UI payload: grouped cards with pros, cons, and notes."""
    r = analyze_profile(profile)
    return {
        "profile": {
            "credit_score": profile.credit_score,
            "annual_income": profile.annual_income,
            "location": profile.location.strip(),
            "housing": profile.housing.strip().lower(),
            "is_student": profile.is_student,
            "credit_history_years": profile.credit_history_years,
            "debt_to_income_ratio": r["dti"],
            "employment_years": profile.employment_years,
            "recent_hard_inquiries_12m": profile.recent_hard_inquiries_12m,
            "estimated_monthly_card_spend": profile.estimated_monthly_card_spend,
        },
        "meta": {
            "location_note": r["location_note"],
            "housing_hint": r["housing_hint"],
            "disclaimer": "Educational guidance only—not financial advice. Issuers use additional factors.",
        },
        "tiers": {
            "good": _serialize_card_rows(r["good"], "good"),
            "maybe": _serialize_card_rows(r["maybe"], "maybe"),
            "avoid": _serialize_card_rows(r["avoid"], "avoid"),
        },
    }


def recommend_cards(profile: UserProfile) -> str:
    r = analyze_profile(profile)
    dti = r["dti"]
    good, maybe, avoid = r["good"], r["maybe"], r["avoid"]
    loc_line = r["location_note"]
    housing_hint = r["housing_hint"] or ""

    header = [
        "=== Credit card ideas (educational only, not financial advice) ===",
        f"Profile: score {profile.credit_score}, income ${profile.annual_income:,.0f}/yr, location: {profile.location.strip()}",
        f"Housing: {profile.housing}, student: {'yes' if profile.is_student else 'no'}",
    ]
    if profile.credit_history_years is not None:
        header.append(f"Credit history: ~{profile.credit_history_years:g} years")
    if dti is not None:
        header.append(f"Debt-to-income (stated): {dti:.0%}")
    if profile.employment_years is not None:
        header.append(f"Employment with current role/employer (stated): ~{profile.employment_years:g} years")
    if profile.recent_hard_inquiries_12m is not None:
        header.append(f"Hard inquiries (last ~12 months, stated): {profile.recent_hard_inquiries_12m}")
    if profile.estimated_monthly_card_spend is not None:
        header.append(f"Estimated monthly card spend: ${profile.estimated_monthly_card_spend:,.0f}")
    header.append(f"Location note: {loc_line}")
    if housing_hint:
        header.append(housing_hint)
    header.append("")
    lines = header

    lines.append("--- Cards that may fit well (stronger match on score + profile) ---")
    if not good:
        lines.append("(None scored as a strong automatic match—check the “compare carefully” list.)")
    else:
        for card, _fit, notes in good:
            lines.extend(_format_card_block(card, "better fit", notes))
            lines.append("")

    lines.append("--- Compare carefully (possible, but more uncertainty) ---")
    if not maybe:
        lines.append("(Nothing landed in the middle bucket with current rules.)")
    else:
        for card, _fit, notes in maybe:
            lines.extend(_format_card_block(card, "maybe", notes))
            lines.append("")

    lines.append("--- Often skip for now (weak match, wrong product, or too aggressive) ---")
    for card, _fit, notes in avoid[:12]:
        lines.extend(_format_card_block(card, "skip / weak", notes))
        lines.append("")
    if len(avoid) > 12:
        lines.append(f"... and {len(avoid) - 12} more cards scored as weaker fits (same logic).")

    lines.append(
        "Issuers use more than score/income: utilization, payment history, internal risk models, and rules like Chase 5/24."
    )
    return "\n".join(lines).rstrip()


def _prompt_int(message: str, min_v: int, max_v: int) -> int:
    while True:
        raw = input(message).strip()
        try:
            v = int(raw)
        except ValueError:
            print("Please enter a whole number.", file=sys.stderr)
            continue
        if v < min_v or v > max_v:
            print(f"Enter a value between {min_v} and {max_v}.", file=sys.stderr)
            continue
        return v


def _prompt_float(message: str, min_v: float) -> float:
    while True:
        raw = input(message).strip().replace(",", "")
        try:
            v = float(raw)
        except ValueError:
            print("Please enter a number.", file=sys.stderr)
            continue
        if v < min_v:
            print(f"Enter a value >= {min_v}.", file=sys.stderr)
            continue
        return v


def _prompt_optional_float(message: str) -> float | None:
    raw = input(message).strip().replace(",", "")
    if raw == "":
        return None
    try:
        return float(raw)
    except ValueError:
        print("Invalid number—treating as blank.", file=sys.stderr)
        return None


def _prompt_optional_int(message: str) -> int | None:
    raw = input(message).strip()
    if raw == "":
        return None
    try:
        return int(raw)
    except ValueError:
        print("Invalid integer—treating as blank.", file=sys.stderr)
        return None


def _prompt_choice(message: str, allowed: set[str]) -> str:
    while True:
        raw = input(message).strip().lower()
        if raw in allowed:
            return raw
        print(f"Please enter one of: {', '.join(sorted(allowed))}", file=sys.stderr)


def _prompt_yes_no(message: str) -> bool:
    while True:
        raw = input(message).strip().lower()
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Answer y or n.", file=sys.stderr)


def interactive_profile() -> UserProfile:
    print("Answer a few questions so we can line up card ideas with your situation.\n")
    credit_score = _prompt_int("Credit score (300–850): ", 300, 850)
    annual_income = _prompt_float("Annual income (gross, USD): ", 0.0)
    location = input("Where you live (U.S. state code like CA, or region like 'Northeast'): ").strip() or "US"
    housing = _prompt_choice("Housing: rent, own, or other? ", {"rent", "own", "other"})
    ch = _prompt_optional_float("Years of credit history (blank if unknown): ")
    dti = _prompt_optional_float("Debt-to-income ratio as decimal 0.35 or percent 35 (blank if unknown): ")
    emp = _prompt_optional_float("Years at current job (blank if unknown): ")
    inq = _prompt_optional_int("Hard credit inquiries in last 12 months (blank if unknown): ")
    spend = _prompt_optional_float("Average monthly purchases you would put on a card (blank if unknown): ")
    student = _prompt_yes_no("Are you a current student? (y/n): ")
    return UserProfile(
        credit_score=credit_score,
        annual_income=annual_income,
        location=location,
        housing=housing,
        credit_history_years=ch,
        debt_to_income_ratio=dti,
        employment_years=emp,
        recent_hard_inquiries_12m=inq,
        estimated_monthly_card_spend=spend,
        is_student=student,
    )


def _build_profile_from_args(args: argparse.Namespace) -> UserProfile:
    return UserProfile(
        credit_score=int(args.credit_score),
        annual_income=float(args.income),
        location=args.location.strip() or "US",
        housing=args.housing.strip().lower(),
        credit_history_years=args.credit_history_years,
        debt_to_income_ratio=args.debt_to_income_ratio,
        employment_years=args.employment_years,
        recent_hard_inquiries_12m=args.recent_inquiries,
        estimated_monthly_card_spend=args.monthly_card_spend,
        is_student=bool(args.student),
    )


def main() -> None:
    p = argparse.ArgumentParser(
        description="Educational credit card ideas from a fuller profile (not financial advice)."
    )
    p.add_argument("--interactive", action="store_true", help="Prompt for all fields interactively")
    p.add_argument("--credit_score", type=int, help="FICO-style score 300–850")
    p.add_argument("--income", type=float, help="Annual gross income USD")
    p.add_argument(
        "--location",
        type=str,
        default=None,
        help="State code (TX) or region label for soft local notes",
    )
    p.add_argument(
        "--housing",
        type=str,
        choices=("rent", "own", "other"),
        default=None,
        help="Housing situation",
    )
    p.add_argument("--credit_history_years", type=float, default=None)
    p.add_argument("--debt_to_income_ratio", type=float, default=None)
    p.add_argument("--employment_years", type=float, default=None)
    p.add_argument("--recent_inquiries", type=int, default=None)
    p.add_argument("--monthly_card_spend", type=float, default=None)
    p.add_argument("--student", action="store_true", help="Flag as student")
    args = p.parse_args()

    if args.interactive or not all(
        x is not None for x in (args.credit_score, args.income, args.location, args.housing)
    ):
        if not sys.stdin.isatty():
            p.error("Interactive mode needs a TTY, or pass --credit_score, --income, --location, --housing.")
        profile = interactive_profile()
    else:
        profile = _build_profile_from_args(args)

    print(recommend_cards(profile))


if __name__ == "__main__":
    main()
