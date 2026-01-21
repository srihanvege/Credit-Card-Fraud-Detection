def recommend_cards(
    credit_score: int,
    annual_income: float,
    credit_history_length: float | None = None,
    account_age: float | None = None,
    debt_to_income_ratio: float | None = None,
    employment_length: float | None = None,
) -> str:
    cs = int(credit_score)
    inc = float(annual_income)
    chl = None if credit_history_length is None else float(credit_history_length)
    aa = None if account_age is None else float(account_age)
    dti = None if debt_to_income_ratio is None else float(debt_to_income_ratio)
    el = None if employment_length is None else float(employment_length)
    if dti is not None and dti > 1:
        dti = dti / 100.0

    recs = []

    if cs < 580:
        recs.append(("Secured / credit-builder cards", "With scores below ~580, many people start with secured cards and focus on on-time payments and low utilization."))
    elif cs < 670:
        recs.append(("Beginner-friendly / secured / student cards", "With fair credit (~580–669), focus on cards that help build history and keep utilization low."))
    elif cs < 690:
        recs.append(("Citi Double Cash (or similar cash-back cards)", "Good credit (~670+) can qualify for rewards cards; cash-back cards are a solid baseline."))
        recs.append(("Capital One Venture (travel starter)", "If you want travel rewards, many people have approval odds starting in the high-600s."))
        recs.append(("Amex Gold (charge card)", "Often considered good-to-excellent; if your profile is strong, you may have a shot in this range."))
    elif cs < 740:
        recs.append(("Chase Sapphire Preferred", "Common guidance is ~690–700+ for stronger approval odds."))
        recs.append(("Amex Platinum", "Common guidance is ~690+ for stronger approval odds."))
        recs.append(("Citi Double Cash / cash-back cards", "Still great value if you want simplicity and low friction rewards."))
    else:
        recs.append(("Chase Sapphire Reserve", "Often cited as requiring very good credit (~740+ for typical approvals)."))
        recs.append(("Amex Platinum", "With very good/excellent credit, premium travel cards may be in reach."))
        recs.append(("Chase Sapphire Preferred", "Often easier than Reserve while still strong for travel rewards."))

    premium_note = ""
    if inc < 40000:
        premium_note = "Because your income is under ~$40k, be cautious with high annual-fee cards and prioritize low/zero-fee options unless the credits clearly outweigh the fee."
    elif inc < 80000:
        premium_note = "With income in the ~$40k–$80k range, mid-tier annual-fee cards can make sense if you’ll actually use the benefits; premium cards can still work if credits match your spending."
    else:
        premium_note = "With income ~$80k+, premium annual-fee cards are more plausible if you’ll use the perks/credits; still do a simple break-even on the annual fee."

    lines = []
    summary_parts = [f"credit score ({cs})", f"annual income (${inc:,.0f})"]
    if chl is not None:
        summary_parts.append(f"credit history length ({chl:g} years)")
    if aa is not None:
        summary_parts.append(f"account age ({aa:g} years)")
    if dti is not None:
        summary_parts.append(f"debt-to-income ratio ({dti:.0%})")
    if el is not None:
        summary_parts.append(f"employment length ({el:g} years)")
    lines.append(f"Based on your {', '.join(summary_parts)}, here are some cards/types to consider:")
    for name, why in recs:
        lines.append(f"- {name}: {why}")
    lines.append(premium_note)
    profile_notes = []
    if chl is not None and chl < 2:
        profile_notes.append("With a short credit history, approvals for premium rewards cards can be harder; starter/secured options may be more realistic while you build history.")
    if aa is not None and aa < 1:
        profile_notes.append("With a very new/young account profile, lenders may be more conservative; consider building tenure before applying for premium cards.")
    if dti is not None and dti >= 0.4:
        profile_notes.append("A higher debt-to-income ratio can reduce approval odds and limits; prioritize lowering debt and keeping utilization low before premium applications.")
    if el is not None and el < 1:
        profile_notes.append("A shorter employment length can make approvals harder depending on issuer; consider waiting until income/employment is more established.")
    if profile_notes:
        lines.extend(profile_notes)
    lines.append("This is educational, not financial advice. Issuers consider many factors beyond score/income (history length, utilization, recent inquiries, etc.).")
    return "\n".join(lines)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--credit_score", type=int, required=True)
    p.add_argument("--income", type=float, required=True)
    p.add_argument("--credit_history_length", type=float, required=False, default=None)
    p.add_argument("--account_age", type=float, required=False, default=None)
    p.add_argument("--debt_to_income_ratio", type=float, required=False, default=None)
    p.add_argument("--employment_length", type=float, required=False, default=None)
    args = p.parse_args()
    print(
        recommend_cards(
            args.credit_score,
            args.income,
            args.credit_history_length,
            args.account_age,
            args.debt_to_income_ratio,
            args.employment_length,
        )
    )
