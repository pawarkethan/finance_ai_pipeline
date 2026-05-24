# ─────────────────────────────────────────────
# app/extractors.py — Document-specific LLM extractors
# ─────────────────────────────────────────────

from utils.llm import llm_json


# ── DELIVERY CHALLAN ─────────────────────────────────────────────────

def extract_delivery_challan(text: str) -> dict:
    """Full 4-step extraction tuned for Delivery Challans."""

    s1 = llm_json(f"""You are a document classifier. Extract document identity from this DELIVERY CHALLAN.
Return ONLY a raw JSON object.

Keys:
- document_type: always "delivery_challan"
- document_number: challan number (e.g. MH20261160P358)
- document_date: date of supply
- supplier_ref_number: SAP Delivery Ref number
- purchase_order_number: PO number
- purchase_order_date: PO date
- hsn_sac_code: HSN code of the goods
- batch_number: batch number
- drug_licence_number: Oxygen IP Drug Lic No or similar

Text: {text}
JSON only:""")

    s2 = llm_json(f"""Extract party details from this DELIVERY CHALLAN.
Return ONLY a raw JSON object.

Keys:
- issuer_name, issuer_gstin, issuer_pan, issuer_address
- recipient_name, recipient_gstin, recipient_pan, recipient_address
- consignee_name, consignee_address
- party_role: "vendor" (issuer delivered goods)
- transporter_name, tanker_number
- sap_tripsheet_ref: SAP Tripsheet Ref No

Text: {text}
JSON only:""")

    s3 = llm_json(f"""Extract financial details from this DELIVERY CHALLAN.
Return ONLY a raw JSON object.

Keys:
- item_description, quantity, unit_of_measure (UOM), rate_per_unit, basic_value
- transport_charges (0 if absent), taxable_value
- cgst_rate, cgst_amount, sgst_rate, sgst_amount
- igst_rate (0 if absent), igst_amount (0 if absent)
- total_invoice_value, amount_in_words, currency

Note: This challan has NO invoice; total_invoice_value = total challan value.

Text: {text}
JSON only:""")

    s4 = llm_json(f"""You are an expert Indian accountant.
Analyse this DELIVERY CHALLAN and return ONLY a raw JSON object.

Keys:
- voucher_type: "delivery_note"
- business_event: one sentence (e.g. "Oxygen gas delivered by INOX Air Products")
- transaction_family: "purchase"
- transaction_type: "goods delivery without invoice"
- money_moved: "no"
- money_direction: "none"
- debit_ledger, debit_account_type, debit_nature, debit_amount
- credit_ledger, credit_account_type, credit_nature, credit_amount
- is_creditor_created, is_debtor_created, payable_or_receivable
- asset_created: "yes"
- asset_type: "inventory"
- expense_booked, expense_head
- gst_treatment: "input_tax_credit_eligible"
- tally_narration: ready-to-paste narration for Tally ERP

Text: {text}
JSON only:""")

    return {**s1, **s2, **s3, **s4}


# ── TAX INVOICE ──────────────────────────────────────────────────────

def extract_invoice(text: str) -> dict:
    """Full 4-step extraction tuned for Tax Invoices."""

    s1 = llm_json(f"""Extract document identity from this TAX INVOICE.
Return ONLY a raw JSON object.

Keys:
- document_type: "invoice"
- document_number: invoice number
- document_date: invoice date
- supplier_ref_number: supplier reference or SAP ref
- purchase_order_number, purchase_order_date
- hsn_sac_code, batch_number
- drug_licence_number (if present)
- irn_number: Invoice Reference Number (e-invoice)

Text: {text}
JSON only:""")

    s2 = llm_json(f"""Extract party details from this TAX INVOICE.
Return ONLY a raw JSON object.

Keys:
- issuer_name, issuer_gstin, issuer_pan, issuer_address
- recipient_name, recipient_gstin, recipient_pan, recipient_address
- consignee_name, consignee_address
- party_role: "vendor"
- transporter_name, tanker_number
- billing_same_as_shipping: "yes" or "no"

Text: {text}
JSON only:""")

    s3 = llm_json(f"""Extract financial details from this TAX INVOICE.
Return ONLY a raw JSON object.

Keys:
- item_description, quantity, unit_of_measure, rate_per_unit, basic_value
- discount_amount: any trade discount given
- transport_charges, taxable_value
- cgst_rate, cgst_amount, sgst_rate, sgst_amount
- igst_rate, igst_amount
- total_invoice_value, amount_in_words, currency
- round_off: rounding difference

Text: {text}
JSON only:""")

    s4 = llm_json(f"""You are an expert Indian accountant.
Analyse this TAX INVOICE and return ONLY a raw JSON object.

Keys:
- voucher_type: "purchase_voucher"
- business_event, transaction_family: "purchase", transaction_type: "goods purchase"
- money_moved: "no"
- money_direction: "none"
- debit_ledger, debit_account_type, debit_nature, debit_amount
- credit_ledger (Creditor / Sundry Creditor), credit_account_type, credit_nature, credit_amount
- is_creditor_created: "yes"
- is_debtor_created: "no"
- payable_or_receivable: "payable"
- asset_created: "yes", asset_type: "inventory"
- expense_booked, expense_head
- gst_treatment: "input_tax_credit_eligible"
- tally_narration

Text: {text}
JSON only:""")

    return {**s1, **s2, **s3, **s4}


# ── BANK STATEMENT ───────────────────────────────────────────────────

def extract_bank_statement(text: str) -> dict:
    """Extraction tuned for Bank Statements."""

    s1 = llm_json(f"""Extract document identity from this BANK STATEMENT.
Return ONLY a raw JSON object.

Keys:
- document_type: "bank_statement"
- document_number: statement reference number
- document_date: statement generation date
- statement_period_from, statement_period_to
- account_number, ifsc_code
- supplier_ref_number: "", purchase_order_number: "", purchase_order_date: ""
- hsn_sac_code: "", batch_number: "", drug_licence_number: ""

Text: {text}
JSON only:""")

    s2 = llm_json(f"""Extract party details from this BANK STATEMENT.
Return ONLY a raw JSON object.

Keys:
- issuer_name: bank name
- issuer_gstin: "", issuer_pan: "", issuer_address: bank branch address
- recipient_name: account holder name
- recipient_gstin: "", recipient_pan, recipient_address
- consignee_name: "", consignee_address: ""
- party_role: "bank"
- transporter_name: "", tanker_number: ""
- bank_branch_code

Text: {text}
JSON only:""")

    s3 = llm_json(f"""Extract financial details from this BANK STATEMENT.
Return ONLY a raw JSON object.

Keys:
- item_description: "bank transactions"
- quantity: "1", unit_of_measure: "lumpsum", rate_per_unit: "", basic_value: ""
- transport_charges: "0"
- taxable_value: ""
- cgst_rate: "0", cgst_amount: "0"
- sgst_rate: "0", sgst_amount: "0"
- igst_rate: "0", igst_amount: "0"
- total_invoice_value: closing balance
- amount_in_words: closing balance in words
- currency: "INR"
- opening_balance, closing_balance, total_credits, total_debits
- transactions: list of {{date, narration, debit, credit, balance}}

Text: {text}
JSON only:""")

    s4 = llm_json(f"""You are an expert Indian accountant.
Analyse this BANK STATEMENT and return ONLY a raw JSON object.

Keys:
- voucher_type: "journal_voucher"
- business_event: "Bank statement for period X showing opening and closing balances"
- transaction_family: "transfer", transaction_type: "bank reconciliation"
- money_moved: "yes", money_direction: "inflow"
- debit_ledger: "Bank A/c", debit_account_type: "asset", debit_nature: "real", debit_amount: total credits
- credit_ledger: "Bank A/c", credit_account_type: "asset", credit_nature: "real", credit_amount: total debits
- is_creditor_created: "no", is_debtor_created: "no"
- payable_or_receivable: "none"
- asset_created: "no", asset_type: "none"
- expense_booked: "no", expense_head: "none"
- gst_treatment: "exempt"
- tally_narration: "Being bank statement reconciliation for period ..."

Text: {text}
JSON only:""")

    return {**s1, **s2, **s3, **s4}


# ── CREDIT NOTE ──────────────────────────────────────────────────────

def extract_credit_note(text: str) -> dict:
    s1 = llm_json(f"""Extract document identity from this CREDIT NOTE.
Return ONLY a raw JSON object.

Keys:
- document_type: "credit_note"
- document_number: credit note number, document_date
- original_invoice_number, original_invoice_date
- reason_for_credit
- supplier_ref_number, purchase_order_number, purchase_order_date
- hsn_sac_code, batch_number, drug_licence_number

Text: {text}
JSON only:""")

    s2 = llm_json(f"""Extract party details from this CREDIT NOTE.
Return ONLY a raw JSON object.
Keys: issuer_name, issuer_gstin, issuer_pan, issuer_address,
recipient_name, recipient_gstin, recipient_pan, recipient_address,
consignee_name, consignee_address, party_role, transporter_name, tanker_number
Text: {text}
JSON only:""")

    s3 = llm_json(f"""Extract financials from this CREDIT NOTE.
Return ONLY a raw JSON object.
Keys: item_description, quantity, unit_of_measure, rate_per_unit, basic_value,
transport_charges, taxable_value, cgst_rate, cgst_amount, sgst_rate, sgst_amount,
igst_rate, igst_amount, total_invoice_value, amount_in_words, currency,
credit_note_value
Text: {text}
JSON only:""")

    s4 = llm_json(f"""Analyse this CREDIT NOTE as an Indian accountant. Return ONLY a raw JSON object.
Keys: voucher_type: "journal_voucher", business_event, transaction_family: "purchase",
transaction_type: "purchase return / credit note",
money_moved: "no", money_direction: "none",
debit_ledger, debit_account_type: "liability", debit_nature: "personal", debit_amount,
credit_ledger, credit_account_type: "income", credit_nature: "nominal", credit_amount,
is_creditor_created: "no", is_debtor_created: "no",
payable_or_receivable: "none",
asset_created: "no", asset_type: "none",
expense_booked: "no", expense_head: "none",
gst_treatment: "input_tax_credit_eligible",
tally_narration
Text: {text}
JSON only:""")

    return {**s1, **s2, **s3, **s4}


# ── RECEIPT ──────────────────────────────────────────────────────────

def extract_receipt(text: str) -> dict:
    s1 = llm_json(f"""Extract identity from this RECEIPT. Return ONLY a raw JSON object.
Keys: document_type: "receipt", document_number, document_date,
payment_mode: cash/cheque/upi/neft, cheque_number,
supplier_ref_number, purchase_order_number, purchase_order_date,
hsn_sac_code, batch_number, drug_licence_number
Text: {text}
JSON only:""")

    s2 = llm_json(f"""Extract parties from this RECEIPT. Return ONLY a raw JSON object.
Keys: issuer_name, issuer_gstin, issuer_pan, issuer_address,
recipient_name, recipient_gstin, recipient_pan, recipient_address,
consignee_name, consignee_address, party_role: "vendor",
transporter_name, tanker_number
Text: {text}
JSON only:""")

    s3 = llm_json(f"""Extract financials from this RECEIPT. Return ONLY a raw JSON object.
Keys: item_description, quantity: "1", unit_of_measure: "lumpsum",
rate_per_unit, basic_value, transport_charges: "0",
taxable_value, cgst_rate, cgst_amount, sgst_rate, sgst_amount,
igst_rate, igst_amount, total_invoice_value, amount_in_words, currency
Text: {text}
JSON only:""")

    s4 = llm_json(f"""Analyse this RECEIPT as an Indian accountant. Return ONLY a raw JSON object.
Keys: voucher_type: "receipt_voucher", business_event,
transaction_family: "receipt", transaction_type: "cash/bank receipt",
money_moved: "yes", money_direction: "inflow",
debit_ledger: "Cash A/c or Bank A/c", debit_account_type: "asset",
debit_nature: "real", debit_amount,
credit_ledger: debtor being settled, credit_account_type: "asset",
credit_nature: "personal", credit_amount,
is_creditor_created: "no", is_debtor_created: "no",
payable_or_receivable: "none",
asset_created: "no", asset_type: "none",
expense_booked: "no", expense_head: "none",
gst_treatment: "exempt",
tally_narration
Text: {text}
JSON only:""")

    return {**s1, **s2, **s3, **s4}


# ── DEBIT NOTE ───────────────────────────────────────────────────────

def extract_debit_note(text: str) -> dict:
    s1 = llm_json(f"""Extract identity from this DEBIT NOTE. Return ONLY a raw JSON object.
Keys: document_type: "debit_note", document_number, document_date,
original_invoice_number, original_invoice_date, reason_for_debit,
supplier_ref_number, purchase_order_number, purchase_order_date,
hsn_sac_code, batch_number, drug_licence_number
Text: {text}
JSON only:""")

    s2 = llm_json(f"""Extract parties from this DEBIT NOTE. Return ONLY a raw JSON object.
Keys: issuer_name, issuer_gstin, issuer_pan, issuer_address,
recipient_name, recipient_gstin, recipient_pan, recipient_address,
consignee_name, consignee_address, party_role, transporter_name, tanker_number
Text: {text}
JSON only:""")

    s3 = llm_json(f"""Extract financials from this DEBIT NOTE. Return ONLY a raw JSON object.
Keys: item_description, quantity, unit_of_measure, rate_per_unit, basic_value,
transport_charges, taxable_value, cgst_rate, cgst_amount, sgst_rate, sgst_amount,
igst_rate, igst_amount, total_invoice_value, amount_in_words, currency, debit_note_value
Text: {text}
JSON only:""")

    s4 = llm_json(f"""Analyse this DEBIT NOTE as an Indian accountant. Return ONLY a raw JSON object.
Keys: voucher_type: "journal_voucher", business_event,
transaction_family: "purchase", transaction_type: "purchase debit note",
money_moved: "no", money_direction: "none",
debit_ledger: "Purchases A/c", debit_account_type: "expense",
debit_nature: "nominal", debit_amount,
credit_ledger: "Vendor A/c (Creditor)", credit_account_type: "liability",
credit_nature: "personal", credit_amount,
is_creditor_created: "yes", is_debtor_created: "no",
payable_or_receivable: "payable",
asset_created: "no", asset_type: "none",
expense_booked: "yes", expense_head,
gst_treatment: "input_tax_credit_eligible",
tally_narration
Text: {text}
JSON only:""")

    return {**s1, **s2, **s3, **s4}


# ── INVALID ───────────────────────────────────────────────────────────

def extract_invalid(text: str) -> dict:
    return {
        "document_type":    "invalid",
        "error":            "Could not classify document. Manual review needed.",
        "raw_text_preview": text[:500],
    }