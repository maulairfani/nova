"""One-off dev seed: uploads the project's dummy SOP documents
(documents/kb/<business_unit>/*.md|*.pdf at the repo root) into each
business unit's real MinIO bucket - the exact same entry point a human
upload through Manage Documents or the MinIO console uses. There is no
direct-to-Qdrant shortcut anymore (ADR-0022's real ingestion pipeline
replaces the old mcp_servers/<unit>/seed/seed_qdrant.py bypass): each
upload here triggers the same webhook -> Celery -> parse/embed/upsert
flow as any other document, and updates/creates the matching `documents`
row (worker/db.py's insert_pending is a get-or-create, so re-running this
script is idempotent).

Requires the repo's documents/kb/ tree to be mounted into the container
(it isn't baked into the image - it's dev seed content, not app code):

    docker compose run --rm -v "$PWD/documents/kb:/kb:ro" worker python seed_documents.py

Requires bootstrap_buckets.py to have already run (buckets must exist and
be subscribed to the webhook), and backend-api's `alembic upgrade head`
to have created the `documents` table.
"""
import pathlib
import sys

from db import pre_create
from minio_client import ensure_bucket, get_client

_BUCKETS = {"tv": "mcn-tv", "plus": "mcn-plus", "news": "mcn-news"}
_CONTENT_TYPES = {".md": "text/markdown", ".pdf": "application/pdf"}
_FORMATS = {".md": "markdown", ".pdf": "pdf"}

# The PDF parser (parser.py's _parse_pdf) has no title extraction - it
# falls back to the raw filename. These PDFs were converted from the
# project's own SOP markdown, which does have a real title (its H1) -
# registering it here means Manage Documents shows the real title
# instead of "02-content-standards-and-compliance.pdf" (see db.py's
# pre_create). Markdown files don't need an entry: parser.py's
# _parse_markdown already extracts their real title from the H1 itself.
_TITLES = {
    ("tv", "02-content-standards-and-compliance.pdf"): "Content Standards and Compliance SOP — MCN TV",
    ("tv", "03-broadcast-incident-escalation.pdf"): "Broadcast Incident Escalation SOP — MCN TV",
    ("plus", "02-subscription-billing-and-churn-handling-sop.pdf"): "Subscription Billing and Churn Handling SOP — MCN+",
    ("plus", "03-shorts-coin-purchase-and-refund-policy.pdf"): "Shorts Coin Purchase and Refund Policy — MCN+",
    ("news", "02-breaking-news-publication-sop.pdf"): "Breaking News Publication SOP — MCN News",
    ("news", "03-correction-retraction-escalation-sop.pdf"): "Correction/Retraction Escalation SOP — MCN News",
}


def seed(root: pathlib.Path) -> None:
    client = get_client()
    for unit, bucket in _BUCKETS.items():
        unit_dir = root / unit
        if not unit_dir.is_dir():
            print(f"{unit}: no directory at {unit_dir}, skipping")
            continue

        ensure_bucket(client, bucket)
        for doc_path in sorted(unit_dir.iterdir()):
            extension = doc_path.suffix.lower()
            if extension not in _CONTENT_TYPES:
                continue

            title = _TITLES.get((unit, doc_path.name))
            if title:
                pre_create(unit, doc_path.name, title, _FORMATS[extension])

            client.fput_object(
                bucket,
                doc_path.name,
                str(doc_path),
                content_type=_CONTENT_TYPES[extension],
            )
            print(f"{unit}: uploaded {doc_path.name} to {bucket}")


if __name__ == "__main__":
    seed(pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "/kb"))
