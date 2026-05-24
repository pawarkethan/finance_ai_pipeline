# ─────────────────────────────────────────────
# app/accounting.py — SubsidiaryBook, JournalProper, Ledger, TrialBalance
# ─────────────────────────────────────────────

import uuid
from datetime import datetime, timezone
from config import DEFAULT_USER

# ── In-memory stores (replace with DB calls in production) ────────────
_subsidiary_book:  list[dict] = []
_journal_proper:   list[dict] = []
_ledger:           list[dict] = []

_voucher_counters: dict[str, int] = {}
_ledger_balances:  dict[str, dict] = {}
_account_ids:      dict[str, str]  = {}

NOW = lambda: datetime.now(timezone.utc).isoformat()

# ─────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────

_VOUCHER_PREFIXES = {
    "Purchase": "PUR",
    "Sales":    "SAL",
    "Bank":     "BNK",
    "Cash":     "CSH",
    "Journal":  "JNL",
}


def _next_voucher_id(book_type: str) -> str:
    year   = datetime.now().year
    prefix = _VOUCHER_PREFIXES.get(book_type, "GEN")
    key    = f"{prefix}-{year}"
    _voucher_counters[key] = _voucher_counters.get(key, 0) + 1
    return f"{key}-{_voucher_counters[key]:04d}"


def _resolve_book_type(extracted_json: dict) -> str:
    doc_type  = extracted_json.get("document_type", "")
    money_dir = extracted_json.get("money_direction", "none")
    voucher_t = extracted_json.get("voucher_type", "")

    if doc_type in ("invoice", "delivery_challan", "debit_note"):
        return "Purchase"
    if doc_type == "credit_note":
        return "Purchase"
    if doc_type == "receipt":
        return "Cash" if money_dir == "inflow" else "Bank"
    if doc_type == "bank_statement":
        return "Bank"
    if voucher_t == "sales_voucher":
        return "Sales"
    return "Purchase"


def _safe_float(val) -> float:
    try:
        return float(str(val).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


def _get_account_id(account_name: str) -> str:
    if account_name not in _account_ids:
        _account_ids[account_name] = str(uuid.uuid5(uuid.NAMESPACE_DNS, account_name))
    return _account_ids[account_name]


def _update_running_balance(
    account_name: str,
    account_type: str,
    debit_amt: float,
    credit_amt: float,
) -> tuple[float, str]:
    prev   = _ledger_balances.get(account_name, {"balance": 0.0, "balance_type": "Dr"})
    bal    = prev["balance"]
    b_type = prev["balance_type"]

    normal_dr = account_type in ("asset", "expense")
    if normal_dr:
        bal    = bal + debit_amt - credit_amt
        b_type = "Dr" if bal >= 0 else "Cr"
    else:
        bal    = bal + credit_amt - debit_amt
        b_type = "Cr" if bal >= 0 else "Dr"

    bal = abs(bal)
    _ledger_balances[account_name] = {"balance": bal, "balance_type": b_type}
    return bal, b_type


# ─────────────────────────────────────────────────────────────────────
# 1. Subsidiary Book
# ─────────────────────────────────────────────────────────────────────

def create_subsidiary_book_entry(
    extracted_json: dict,
    created_by: str = DEFAULT_USER,
    remark: str = "",
) -> dict:
    book_type  = _resolve_book_type(extracted_json)
    voucher_id = _next_voucher_id(book_type)

    money_dir = extracted_json.get("money_direction", "none")
    if money_dir == "outflow":
        party_name  = extracted_json.get("issuer_name", "")
        party_gstin = extracted_json.get("issuer_gstin", "")
    else:
        party_name  = extracted_json.get("recipient_name") or extracted_json.get("issuer_name", "")
        party_gstin = extracted_json.get("recipient_gstin") or extracted_json.get("issuer_gstin", "")

    auto_remark = (
        remark
        or extracted_json.get("tally_narration")
        or extracted_json.get("business_event")
        or f"{book_type} entry via {extracted_json.get('document_number', 'N/A')}"
    )

    row = {
        "sb_id":              str(uuid.uuid4()),
        "book_type":          book_type,
        "voucher_id":         voucher_id,
        "voucher_series":     voucher_id.rsplit("-", 1)[0] + "-",
        "document_type":      extracted_json.get("document_type"),
        "document_number":    extracted_json.get("document_number"),
        "document_date":      extracted_json.get("document_date"),
        "party_name":         party_name,
        "party_gstin":        party_gstin,
        "total_amount":       extracted_json.get("total_invoice_value", "0"),
        "taxable_value":      extracted_json.get("taxable_value", "0"),
        "cgst_amount":        extracted_json.get("cgst_amount", "0"),
        "sgst_amount":        extracted_json.get("sgst_amount", "0"),
        "igst_amount":        extracted_json.get("igst_amount", "0"),
        "currency":           extracted_json.get("currency", "INR"),
        "transaction_details": extracted_json,
        "remark":             auto_remark,
        "status":             "draft",
        "created_at":         NOW(),
        "updated_at":         NOW(),
        "created_by":         created_by,
        "updated_by":         created_by,
        "verified":           False,
        "verified_by":        None,
        "verified_at":        None,
    }
    _subsidiary_book.append(row)
    return row


# ─────────────────────────────────────────────────────────────────────
# 2. Journal Proper
# ─────────────────────────────────────────────────────────────────────

def create_journal_entry(sb_row: dict, created_by: str = DEFAULT_USER) -> list[dict]:
    j           = sb_row["transaction_details"]
    amount      = _safe_float(j.get("total_invoice_value", 0))
    jp_group_id = str(uuid.uuid4())
    txn_date    = j.get("document_date", sb_row["document_date"])
    narration   = j.get("tally_narration") or j.get("business_event", "")

    debit_row = {
        "jp_id":            str(uuid.uuid4()),
        "jp_group_id":      jp_group_id,
        "voucher_id":       sb_row["voucher_id"],
        "sb_id":            sb_row["sb_id"],
        "ledger_folio":     j.get("debit_ledger", "Suspense A/c"),
        "account_name":     j.get("debit_ledger", "Suspense A/c"),
        "account_type":     j.get("debit_account_type", ""),
        "account_nature":   j.get("debit_nature", ""),
        "transaction_date": txn_date,
        "entry_type":       "Dr",
        "particulars":      f"Dr  {j.get('debit_ledger', 'Suspense A/c')}",
        "amount_debit":     amount,
        "amount_credit":    0.0,
        "narration":        narration,
        "hsn_sac_code":     j.get("hsn_sac_code", ""),
        "gst_treatment":    j.get("gst_treatment", ""),
        "created_at":       NOW(),
        "updated_at":       NOW(),
        "created_by":       created_by,
        "updated_by":       created_by,
        "verified":         False,
        "verified_by":      None,
        "verified_at":      None,
    }

    credit_row = {
        "jp_id":            str(uuid.uuid4()),
        "jp_group_id":      jp_group_id,
        "voucher_id":       sb_row["voucher_id"],
        "sb_id":            sb_row["sb_id"],
        "ledger_folio":     j.get("credit_ledger", "Suspense A/c"),
        "account_name":     j.get("credit_ledger", "Suspense A/c"),
        "account_type":     j.get("credit_account_type", ""),
        "account_nature":   j.get("credit_nature", ""),
        "transaction_date": txn_date,
        "entry_type":       "Cr",
        "particulars":      f"    To  {j.get('credit_ledger', 'Suspense A/c')}",
        "amount_debit":     0.0,
        "amount_credit":    amount,
        "narration":        narration,
        "hsn_sac_code":     j.get("hsn_sac_code", ""),
        "gst_treatment":    j.get("gst_treatment", ""),
        "created_at":       NOW(),
        "updated_at":       NOW(),
        "created_by":       created_by,
        "updated_by":       created_by,
        "verified":         False,
        "verified_by":      None,
        "verified_at":      None,
    }

    _journal_proper.extend([debit_row, credit_row])
    return [debit_row, credit_row]


# ─────────────────────────────────────────────────────────────────────
# 3. Ledger
# ─────────────────────────────────────────────────────────────────────

def create_ledger_entries(journal_pair: list[dict], created_by: str = DEFAULT_USER) -> list[dict]:
    assert len(journal_pair) == 2, "Expected exactly [debit_row, credit_row]"
    dr_row, cr_row = journal_pair
    entries = []

    for this, contra in [(dr_row, cr_row), (cr_row, dr_row)]:
        is_dr     = this["entry_type"] == "Dr"
        dr_amt    = this["amount_debit"]
        cr_amt    = this["amount_credit"]
        acct_name = this["account_name"]
        acct_type = this["account_type"]

        new_bal, b_type = _update_running_balance(acct_name, acct_type, dr_amt, cr_amt)
        particulars = (
            f"To {contra['account_name']}" if is_dr
            else f"By {contra['account_name']}"
        )

        entry = {
            "ledger_entry_id":  str(uuid.uuid4()),
            "account_id":       _get_account_id(acct_name),
            "account_name":     acct_name,
            "account_type":     acct_type,
            "account_nature":   this["account_nature"],
            "journal_ref":      this["jp_group_id"],
            "voucher_id":       this["voucher_id"],
            "transaction_date": this["transaction_date"],
            "particulars":      particulars,
            "amount_debit":     dr_amt,
            "amount_credit":    cr_amt,
            "amount_balance":   round(new_bal, 2),
            "balance_type":     b_type,
            "narration":        this["narration"],
            "created_at":       NOW(),
            "updated_at":       NOW(),
            "created_by":       created_by,
            "updated_by":       created_by,
            "verified":         "Draft",
            "verified_by":      None,
            "verified_at":      None,
            "remark":           this["narration"],
        }
        entries.append(entry)

    _ledger.extend(entries)
    return entries


# ─────────────────────────────────────────────────────────────────────
# 4. Trial Balance
# ─────────────────────────────────────────────────────────────────────

def generate_trial_balance(created_by: str = DEFAULT_USER) -> dict:
    details  = []
    total_dr = 0.0
    total_cr = 0.0

    for acct_name, bal_info in _ledger_balances.items():
        bal    = bal_info["balance"]
        b_type = bal_info["balance_type"]
        dr_col = round(bal, 2) if b_type == "Dr" else 0.0
        cr_col = round(bal, 2) if b_type == "Cr" else 0.0
        total_dr += dr_col
        total_cr += cr_col
        details.append({
            "account_id":    _get_account_id(acct_name),
            "account_name":  acct_name,
            "account_type":  "",
            "amount_debit":  dr_col,
            "amount_credit": cr_col,
            "balance":       dr_col - cr_col,
        })

    is_balanced = round(total_dr, 2) == round(total_cr, 2)
    return {
        "tb_id":                  str(uuid.uuid4()),
        "trial_balance_details":  details,
        "total_debits":           round(total_dr, 2),
        "total_credits":          round(total_cr, 2),
        "is_balanced":            is_balanced,
        "balance_difference":     round(abs(total_dr - total_cr), 2),
        "generated_at":           NOW(),
        "created_at":             NOW(),
        "updated_at":             NOW(),
        "created_by":             created_by,
        "updated_by":             created_by,
        "verified":               False,
        "verified_by":            None,
        "verified_at":            None,
    }


# ─────────────────────────────────────────────────────────────────────
# Master accounting runner
# ─────────────────────────────────────────────────────────────────────

def run_accounting_pipeline(
    extracted_json: dict,
    created_by: str = DEFAULT_USER,
    remark: str = "",
) -> dict:
    if extracted_json.get("document_type") == "invalid":
        print("❌ Blocked: Cannot create accounting entries for an invalid document.")
        return {
            "subsidiary_book": None,
            "journal_proper":  None,
            "ledger_entries":  None,
            "trial_balance":   None,
            "error":           extracted_json.get("error", "Invalid document"),
        }

    print("\n" + "═" * 60)
    print("  ACCOUNTING AUTOMATION PIPELINE")
    print("═" * 60)

    print("\n[1/4] Creating SubsidiaryBook entry...")
    sb_row = create_subsidiary_book_entry(extracted_json, created_by, remark)
    print(f"  ✅  Voucher ID : {sb_row['voucher_id']}")
    print(f"       Book Type  : {sb_row['book_type']}")
    print(f"       Party      : {sb_row['party_name']}")
    print(f"       Amount     : ₹{sb_row['total_amount']}")

    print("\n[2/4] Creating JournalProper entries...")
    jp_pair       = create_journal_entry(sb_row, created_by)
    dr_row, cr_row = jp_pair
    print(f"  ✅  Dr  {dr_row['account_name']:35s}  ₹{dr_row['amount_debit']:>12,.2f}")
    print(f"       Cr      {cr_row['account_name']:35s}  ₹{cr_row['amount_credit']:>12,.2f}")
    print(f"       Narration: {dr_row['narration']}")

    print("\n[3/4] Posting Ledger entries...")
    ledger_entries = create_ledger_entries(jp_pair, created_by)
    for le in ledger_entries:
        print(f"  ✅  {le['account_name']:35s}  Bal: ₹{le['amount_balance']:>10,.2f} {le['balance_type']}")

    print("\n[4/4] Refreshing Trial Balance...")
    tb     = generate_trial_balance(created_by)
    status = "✅ BALANCED" if tb["is_balanced"] else f"❌ OUT BY ₹{tb['balance_difference']}"
    print(f"  {status}  |  Dr: ₹{tb['total_debits']:,.2f}  Cr: ₹{tb['total_credits']:,.2f}")

    print("\n" + "═" * 60)
    print("  PIPELINE COMPLETE")
    print("═" * 60)

    return {
        "subsidiary_book": sb_row,
        "journal_proper":  jp_pair,
        "ledger_entries":  ledger_entries,
        "trial_balance":   tb,
    }


# ── Getters (for API responses) ────────────────────────────────────────

def get_subsidiary_book() -> list[dict]:
    return _subsidiary_book

def get_journal_proper() -> list[dict]:
    return _journal_proper

def get_ledger() -> list[dict]:
    return _ledger