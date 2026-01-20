def recommend_cards(credit_score: int, annual_income: float) -> str:
    cs = int(credit_score)
    inc = float(annual_income)

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
    lines.append(f"Based on your credit score ({cs}) and annual income (${inc:,.0f}), here are some cards/types to consider:")
    for name, why in recs:
        lines.append(f"- {name}: {why}")
    lines.append(premium_note)
    lines.append("This is educational, not financial advice. Issuers consider many factors beyond score/income (history length, utilization, recent inquiries, etc.).")
    return "\n".join(lines)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--credit_score", type=int, required=True)
    p.add_argument("--income", type=float, required=True)
    args = p.parse_args()
    print(recommend_cards(args.credit_score, args.income))
