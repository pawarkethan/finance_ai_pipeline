# ─────────────────────────────────────────────
# app/pipeline.py — LangChain extraction pipeline
# ─────────────────────────────────────────────

from langchain.schema.runnable import RunnableLambda, RunnableBranch

from app.classifier import classifier_chain
from app.extractors import (
    extract_delivery_challan,
    extract_invoice,
    extract_bank_statement,
    extract_credit_note,
    extract_receipt,
    extract_debit_note,
    extract_invalid,
)


def _make_extractor(fn):
    """Wrap an extraction function as a LangChain Runnable."""
    return RunnableLambda(lambda inp: fn(inp["text"]))


# Route by doc_type to the appropriate extractor
extraction_router = RunnableBranch(
    (
        lambda inp: inp["doc_type"] == "delivery_challan",
        _make_extractor(extract_delivery_challan),
    ),

    (
        lambda inp: inp["doc_type"] == "invoice",
        _make_extractor(extract_invoice),
    ),

    (
        lambda inp: inp["doc_type"] == "bank_statement",
        _make_extractor(extract_bank_statement),
    ),

    (
        lambda inp: inp["doc_type"] == "credit_note",
        _make_extractor(extract_credit_note),
    ),

    (
        lambda inp: inp["doc_type"] == "receipt",
        _make_extractor(extract_receipt),
    ),

    (
        lambda inp: inp["doc_type"] == "debit_note",
        _make_extractor(extract_debit_note),
    ),

    # Default fallback
    _make_extractor(extract_invalid),
)


def _classify_and_package(text: str) -> dict:
    """
    Classify the document and package the result.
    """

    doc_type = classifier_chain.invoke(text)

    print(f"\n✅ Classifier detected: '{doc_type}'")

    return {
        "text": text,
        "doc_type": doc_type,
    }


# Full pipeline
full_pipeline = (
    RunnableLambda(_classify_and_package)
    | extraction_router
)


# ─────────────────────────────────────────────
# TEST BLOCK
# ─────────────────────────────────────────────

if __name__ == "__main__":

    sample_text = """
    TAX INVOICE

    ABC Electronics Store
    Invoice Number: INV-1001
    Total Amount: ₹15,000
    """

    print("\nRunning Pipeline Test...\n")

    try:

        result = full_pipeline.invoke(sample_text)

        print("\nPipeline Output:\n")
        print(result)

    except Exception as e:

        print("\nError:\n")
        print(e)