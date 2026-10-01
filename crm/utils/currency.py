"""Currency catalog and money formatting.

The clinic picks a currency in Settings. Each invoice snapshots the code it was
issued in, so historical documents keep their original currency.

Formatting is deliberately locale-independent: the app has always rendered money
as `f"${amount:.2f}"`, so we keep a single consistent style (dot decimal
separator, comma thousands) and only vary the symbol and its position.
"""

# code: (symbol, default position, display name)
CURRENCIES = {
    "USD": ("$", "before", "US Dollar"),
    "EUR": ("€", "after", "Euro"),
    "GBP": ("£", "before", "British Pound"),
    "MAD": ("MAD", "before", "Moroccan Dirham"),
    "DZD": ("DZD", "before", "Algerian Dinar"),
    "TND": ("TND", "before", "Tunisian Dinar"),
    "EGP": ("EGP", "before", "Egyptian Pound"),
    "SAR": ("SAR", "before", "Saudi Riyal"),
    "AED": ("AED", "before", "UAE Dirham"),
    "QAR": ("QAR", "before", "Qatari Riyal"),
    "KWD": ("KWD", "before", "Kuwaiti Dinar"),
    "CAD": ("CA$", "before", "Canadian Dollar"),
    "AUD": ("A$", "before", "Australian Dollar"),
    "CHF": ("CHF", "before", "Swiss Franc"),
    "JPY": ("¥", "before", "Japanese Yen"),
    "CNY": ("¥", "before", "Chinese Yuan"),
    "INR": ("₹", "before", "Indian Rupee"),
    "TRY": ("₺", "before", "Turkish Lira"),
    "ZAR": ("R", "before", "South African Rand"),
}

DEFAULT_CODE = "USD"
DEFAULT_SYMBOL = "$"

# Currencies whose symbol is conventionally written after the amount.
SUFFIX_CODES = {"EUR"}


def is_known(code):
    return bool(code) and code.upper() in CURRENCIES


def symbol_for(code, fallback=DEFAULT_SYMBOL):
    """Symbol for a currency code, or the fallback for user-defined codes."""
    entry = CURRENCIES.get((code or "").upper())
    return entry[0] if entry else fallback


def position_for(code, fallback="before"):
    entry = CURRENCIES.get((code or "").upper())
    return entry[1] if entry else fallback


def label_for(code, fallback=None):
    """Human label for a combo entry, e.g. 'USD - US Dollar ($)'."""
    key = (code or "").upper()
    entry = CURRENCIES.get(key)
    if not entry:
        return fallback or key
    return f"{key} - {entry[2]} ({entry[0]})"


def sorted_codes():
    return sorted(CURRENCIES)


def format_money(amount, symbol=DEFAULT_SYMBOL, position="before", decimals=2):
    """Format an amount as `1,234.56 $` or `$1,234.56`."""
    try:
        value = float(amount)
    except (TypeError, ValueError):
        value = 0.0
    text = f"{abs(value):,.{decimals}f}"
    if value < 0:
        text = f"-{text}"
    symbol = (symbol or "").strip()
    if not symbol:
        return text
    if position == "after":
        return f"{text} {symbol}"
    return f"{symbol}{text}"


def clinic_currency(clinic=None):
    """Resolve (code, symbol, position) from a ClinicInfo row.

    Falls back to USD/$ so a half-migrated database still renders amounts.
    """
    if clinic is None:
        return DEFAULT_CODE, DEFAULT_SYMBOL, "before"
    keys = clinic.keys()
    code = (clinic["currency_code"] if "currency_code" in keys else "") or ""
    symbol = (clinic["currency_symbol"] if "currency_symbol" in keys else "") or ""
    position = (clinic["currency_position"] if "currency_position" in keys else "") or ""
    if not code:
        # Pre-currency databases: infer the code from the stored symbol.
        code = next((c for c, (s, _, _) in CURRENCIES.items() if s == symbol), DEFAULT_CODE)
    if not symbol:
        symbol = symbol_for(code)
    if not position:
        position = position_for(code)
    return code.upper(), symbol, position


def format_for_clinic(amount, clinic=None, decimals=2):
    """Format an amount using a ClinicInfo row's currency settings."""
    _, symbol, position = clinic_currency(clinic)
    return format_money(amount, symbol, position, decimals)


# Insurance claim states stored on Billing.insurance_claim_status.
CLAIM_NOT_SUBMITTED = 'NOT_SUBMITTED'
CLAIM_SUBMITTED = 'SUBMITTED'
CLAIM_SETTLED = 'SETTLED'
CLAIM_DENIED = 'DENIED'
CLAIM_STATUSES = (CLAIM_NOT_SUBMITTED, CLAIM_SUBMITTED, CLAIM_SETTLED, CLAIM_DENIED)


def claim_label(status):
    return {
        CLAIM_NOT_SUBMITTED: "Not submitted",
        CLAIM_SUBMITTED: "Submitted",
        CLAIM_SETTLED: "Settled",
        CLAIM_DENIED: "Denied",
    }.get(status, "Not submitted")


def claim_color(status):
    return {
        CLAIM_NOT_SUBMITTED: "#64748B",
        CLAIM_SUBMITTED: "#B45309",
        CLAIM_SETTLED: "#15803D",
        CLAIM_DENIED: "#B91C1C",
    }.get(status, "#64748B")


def split_coverage(total, percent):
    """Split a total into (insurer_share, patient_share) for a coverage percent.

    The insurer share is rounded to 2 decimals and the patient share takes the
    remainder, so the two always add back up to the total with no lost penny.
    Percent is clamped to 0-100.
    """
    try:
        total = float(total)
    except (TypeError, ValueError):
        total = 0.0
    try:
        percent = float(percent)
    except (TypeError, ValueError):
        percent = 0.0
    percent = min(100.0, max(0.0, percent))

    insurer = round(total * percent / 100.0, 2)
    patient = round(total - insurer, 2)
    return insurer, patient
