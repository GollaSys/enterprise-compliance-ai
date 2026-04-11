"""Seed the LangSmith eval dataset for the compliance demo pipeline.

Run directly to create/upsert the dataset:
    python evals/dataset.py
"""
from langsmith import Client

DATASET_NAME = "compliance-demo-eval"

# Example 2: minimal GDPR policy — deliberately missing Art.17 + Art.30
_GDPR_MINIMAL = """ACME CORP — DATA PROTECTION POLICY v0.1

We collect personal data (name, email, IP address) to provide our service.
Data is stored on secure servers in the EU.
We share data with payment processors and analytics vendors where required.
Users can contact privacy@acme.com to request a copy of their data.
We retain data for as long as the account is active.
We comply with applicable data protection laws.
"""

# Example 3: SOX financial controls — missing segregation of duties
_SOX_FINANCIAL = """FINANCIAL CONTROLS POLICY v1.0

The finance department manages all financial transactions.
One senior accountant handles both payment approvals and disbursements.
Monthly reconciliations are performed by the same team that processes payments.
We conduct an annual external audit. All transactions are logged in our ERP.
Journal entries are approved by the CFO on a quarterly basis.
Access to the general ledger is restricted to finance staff.
"""

_EXAMPLES = [
    {
        "inputs": {
            "document_path": "data/samples/gdpr_policy_sample.txt",
            "regulation_type": "GDPR",
        }
    },
    {
        "inputs": {
            "document_text": _GDPR_MINIMAL,
            "regulation_type": "GDPR",
        }
    },
    {
        "inputs": {
            "document_text": _SOX_FINANCIAL,
            "regulation_type": "SOX",
        }
    },
]


def seed_dataset() -> str:
    """Create or verify the LangSmith eval dataset. Returns dataset name."""
    client = Client()
    datasets = list(client.list_datasets(dataset_name=DATASET_NAME))
    if datasets:
        print(f"Dataset '{DATASET_NAME}' already exists — skipping seed")
        return DATASET_NAME

    dataset = client.create_dataset(
        DATASET_NAME,
        description="Compliance demo pipeline eval dataset — 3 examples (GDPR x2, SOX x1)",
    )
    for ex in _EXAMPLES:
        client.create_example(inputs=ex["inputs"], dataset_id=dataset.id)
    print(f"Created dataset '{DATASET_NAME}' with {len(_EXAMPLES)} examples")
    return DATASET_NAME


if __name__ == "__main__":
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from dotenv import load_dotenv
    load_dotenv(override=True)
    seed_dataset()
