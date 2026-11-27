"""
GridGuard AI - Live Troubleshooting Vector Query Verification
Tests semantic retrieval from isolated ChromaDB equipment_troubleshooting collection.
"""

import sys
from pathlib import Path

# Add ai-service to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.rag.manual_ingester import ManualIngestionWorker


def run_verification():
    worker = ManualIngestionWorker()

    queries = [
        ("SF6 gas pressure density monitor alarm", "Siemens"),
        ("Transformer oil dielectric BDV breakdown voltage", "ABB"),
        ("Mounting locations and feeder circuit breaker installation", None),
    ]

    print("=" * 70)
    print("GRIDGUARD AI - EQUIPMENT TROUBLESHOOTING MULTIMODAL RAG VERIFICATION")
    print("=" * 70)

    for q, target_oem in queries:
        print(f"\n[QUERY]: '{q}' (Target OEM: {target_oem or 'Any'})")
        res = worker.query_kb(q, n_results=2, oem_filter=target_oem)

        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        distances = res.get("distances", [[]])[0]

        for idx, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
            citation = meta.get("citation", "Unknown")
            oem = meta.get("oem", "Unknown")
            fault = meta.get("fault_category", "Unknown")
            has_table = meta.get("has_table", False)
            has_img = meta.get("has_image", False)
            img_paths = meta.get("image_paths", "[]")

            print(f"  --> Result #{idx+1} [Cosine Distance: {dist:.4f}]")
            print(f"      OEM: {oem} | Citation: {citation} | Fault Category: {fault}")
            print(f"      Multimodal Assets: Table={has_table}, Image={has_img}")
            if has_img and img_paths != "[]":
                print(f"      Associated Images: {img_paths}")
            snippet = doc.replace("\n", " ")[:200]
            print(f"      Content: {snippet}...\n")


if __name__ == "__main__":
    run_verification()
