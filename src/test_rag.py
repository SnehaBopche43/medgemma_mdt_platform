import sys
import os

# Add the project root to Python path so 'src' is importable
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from src.rag_pipeline import MedicalRAGPipeline


def test_pipeline():
    print("\n--- MedGemma MDT Platform RAG Pipeline Test ---\n")

    rag_pipeline = MedicalRAGPipeline(base_dir=PROJECT_ROOT)

    query = "treatment for metastatic EGFR-mutant lung cancer"
    cancer_type = "lung"

    print(f"Query: {query}  |  Cancer Type: {cancer_type}\n")

    results = rag_pipeline.retrieve(query, cancer_type)

    print(f"\n--- Top {len(results)} Results ---")

    if not results:
        print("No results found.")
        return

    for i, result in enumerate(results):
        # Handle both flat format (static refs) and nested metadata format (PubMed/FAISS)
        if 'metadata' in result:
            source = result['metadata'].get('source', 'N/A')
            title  = result['metadata'].get('title', 'N/A')
            url    = result['metadata'].get('url', 'N/A')
            text   = result.get('text', '')
        else:
            source = result.get('source', 'N/A')
            title  = result.get('title', 'N/A')
            url    = result.get('url', 'N/A')
            text   = ''

        print(f"\n{i+1}. {title}  (Source: {source})")
        print(f"   URL: {url}")

        key_points = result.get('key_points', [])
        if key_points:
            print(f"   Key Points: {' '.join(key_points)}")
        elif text:
            snippet = text[:300].replace('\n', ' ').strip()
            print(f"   Abstract: {snippet}...")

        print("-" * 120)


if __name__ == "__main__":
    test_pipeline()
