def to_cents(amount):
    # amount may be Decimal, float, int, str
    if amount is None:
        raise ValueError("amount is None")
    # avoid float issues by using string
    s = str(amount)
    if s.strip() == "":
        raise ValueError("amount is empty")
    # handle already cents
    if isinstance(amount, int):
        # assume dollars if small? nope. we assume dollars is decimal elsewhere.
        pass
    dollars = float(s)
    return int(round(dollars * 100))

def compute_amounts(base_cents, tax_rate, app_fee_rate=0.07):
    tax_cents = int(round(base_cents * float(tax_rate)))
    app_fee_cents = int(round((base_cents + tax_cents) * float(app_fee_rate)))
    final_cents = base_cents + tax_cents + app_fee_cents
    return tax_cents, app_fee_cents, final_cents
