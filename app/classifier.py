# ─────────────────────────────────────────────
# app/classifier.py — LangChain document classifier
# ─────────────────────────────────────────────

import re
from langchain.schema.runnable import RunnableLambda
from langchain.prompts import PromptTemplate

from utils.llm import run_llm

VALID_TYPES = {
    "invoice", "delivery_challan", "receipt",
    "bank_statement", "credit_note", "debit_note", "invalid",
}

CLASSIFIER_PROMPT = PromptTemplate.from_template("""
You are a document classifier. Read the text below and return ONLY one word —
the document type. Choose from:
  invoice | delivery_challan | receipt | bank_statement | credit_note | debit_note | invalid

Rules:
- "Delivery Challan" or "DELIVERY CHALLAN" → delivery_challan
- "Tax Invoice" or "Invoice"               → invoice
- "Bank Statement" or "Account Statement"  → bank_statement
- "Credit Note"                            → credit_note
- "Debit Note"                             → debit_note
- If unclear                               → invalid

Return ONLY the single type word, nothing else.

Text:
{text}

Document type:""")


def classify_document(text: str) -> str:
    """Classify a document from its OCR text. Returns one of VALID_TYPES."""
    prompt = CLASSIFIER_PROMPT.format(text=text[:2000])
    raw    = run_llm(prompt).strip().lower()
    word   = re.split(r'[\s\n,.]', raw)[0]
    return word if word in VALID_TYPES else "invalid"


# LangChain runnable wrapper
classifier_chain = RunnableLambda(classify_document)