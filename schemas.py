# ─────────────────────────────────────────────
# models/schemas.py — Pydantic output schemas
# ─────────────────────────────────────────────

from pydantic import BaseModel
from typing import Literal, Optional


class Step1_DocumentIdentity(BaseModel):
    document_type: Literal[
        "invoice", "delivery_challan", "receipt",
        "bank_statement", "credit_note", "debit_note", "invalid"
    ]
    document_number: str
    document_date: str
    supplier_ref_number: str
    purchase_order_number: str
    purchase_order_date: str
    hsn_sac_code: str
    batch_number: str
    drug_licence_number: str


class Step2_Parties(BaseModel):
    issuer_name: str
    issuer_gstin: str
    issuer_pan: str
    issuer_address: str
    recipient_name: str
    recipient_gstin: str
    recipient_pan: str
    recipient_address: str
    consignee_name: str
    consignee_address: str
    party_role: Literal["vendor", "customer", "bank", "unknown"]
    transporter_name: str
    tanker_number: str


class Step3_Financials(BaseModel):
    item_description: str
    quantity: str
    unit_of_measure: str
    rate_per_unit: str
    basic_value: str
    transport_charges: str
    taxable_value: str
    cgst_rate: str
    cgst_amount: str
    sgst_rate: str
    sgst_amount: str
    igst_rate: str
    igst_amount: str
    total_invoice_value: str
    amount_in_words: str
    currency: str


class Step4_AccountingEntry(BaseModel):
    voucher_type: Literal[
        "purchase_voucher", "sales_voucher", "payment_voucher",
        "receipt_voucher", "journal_voucher", "delivery_note"
    ]
    business_event: str
    transaction_family: Literal["purchase", "sale", "payment", "receipt", "transfer"]
    transaction_type: str
    money_moved: Literal["yes", "no", "partial"]
    money_direction: Literal["inflow", "outflow", "none"]
    debit_ledger: str
    debit_account_type: Literal["asset", "expense", "liability", "income", "equity"]
    debit_nature: Literal["real", "personal", "nominal"]
    debit_amount: str
    credit_ledger: str
    credit_account_type: Literal["asset", "expense", "liability", "income", "equity"]
    credit_nature: Literal["real", "personal", "nominal"]
    credit_amount: str
    is_creditor_created: Literal["yes", "no"]
    is_debtor_created: Literal["yes", "no"]
    payable_or_receivable: Literal["payable", "receivable", "none"]
    asset_created: Literal["yes", "no"]
    asset_type: str
    expense_booked: Literal["yes", "no"]
    expense_head: str
    gst_treatment: str
    tally_narration: str