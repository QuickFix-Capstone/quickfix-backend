# Province/state tax rates (Canada)
# job.location_state expected values like 'ON', 'BC', etc.
RATES = {
    "AB": 0.05,
    "BC": 0.12,
    "MB": 0.12,
    "NB": 0.15,
    "NL": 0.15,
    "NS": 0.15,
    "NT": 0.05,
    "NU": 0.05,
    "ON": 0.13,
    "PE": 0.15,
    "QC": 0.14975,
    "SK": 0.11,
    "YT": 0.05,
}

NAME_TO_CODE = {
    "ALBERTA": "AB",
    "BRITISH COLUMBIA": "BC",
    "MANITOBA": "MB",
    "NEW BRUNSWICK": "NB",
    "NEWFOUNDLAND AND LABRADOR": "NL",
    "NEWFOUNDLAND": "NL",
    "NOVA SCOTIA": "NS",
    "NORTHWEST TERRITORIES": "NT",
    "NUNAVUT": "NU",
    "ONTARIO": "ON",
    "PRINCE EDWARD ISLAND": "PE",
    "QUEBEC": "QC",
    "SASKATCHEWAN": "SK",
    "YUKON": "YT",
}

def normalize_state(val):
    if not val:
        return None
    s = str(val).strip().upper()
    if s in RATES:
        return s
    s2 = s.replace(".", "").replace(",", "")
    return NAME_TO_CODE.get(s2, s[:2] if len(s)>=2 else s)

def get_rate(location_state):
    code = normalize_state(location_state)
    if not code:
        return 0.0, None
    return float(RATES.get(code, 0.0)), code
