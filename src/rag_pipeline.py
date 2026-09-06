import os
import json
import faiss
import numpy as np
from pathlib import Path
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
from Bio import Entrez
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

try:
    from src.reference_system import ReferenceSystem
except ModuleNotFoundError:
    from reference_system import ReferenceSystem


CANCER_TYPE_MAP = {
    "lung":              "lung_cancer",
    "breast":            "breast_cancer",
    "colorectal":        "colorectal_cancer",
    "prostate":          "prostate_cancer",
    "ovarian":           "ovarian_cancer",
    "pancreatic":        "pancreatic_cancer",
    "liver":             "liver_cancer",
    "lymphoma":          "lymphoma",
    "lung_cancer":       "lung_cancer",
    "breast_cancer":     "breast_cancer",
    "colorectal_cancer": "colorectal_cancer",
}

ALL_TOPICS = [
    "neoadjuvant", "adjuvant", "hormonal_therapy", "her2_therapy",
    "staging", "systemic_therapy", "targeted_therapy", "immunotherapy",
    "nsclc", "first_line", "egfr", "chemotherapy"
]


class MedicalRAGPipeline:

    def __init__(self, base_dir='.') -> None:
        self.base_dir = Path(base_dir)
        self.cache_dir = self.base_dir / 'src' / 'cache'
        self.faiss_index_path = self.cache_dir / 'knowledge_base.faiss'
        self.documents_path = self.cache_dir / 'documents.json'
        self.cache_dir.mkdir(exist_ok=True)

        logging.info("Loading embedding and cross-encoder models...")
        self.embedding_model = SentenceTransformer('ncbi/MedCPT-Query-Encoder')
        self.cross_encoder = CrossEncoder('ncbi/MedCPT-Cross-Encoder')
        logging.info("Models loaded.")

        self.static_reference_system = ReferenceSystem()
        self.documents = []
        self.faiss_index = None
        self.bm25_index = None

        Entrez.email = 'your.real.email@institution.com'

        self.load_or_build_indices()

    def load_or_build_indices(self):
        if self.faiss_index_path.exists() and self.documents_path.exists():
            logging.info("Loading existing indices from cache...")
            self.documents = json.loads(self.documents_path.read_text())
            self.faiss_index = faiss.read_index(str(self.faiss_index_path))
            tokenized_corpus = [doc['text'].split(" ") for doc in self.documents]
            self.bm25_index = BM25Okapi(tokenized_corpus)
            logging.info(f"Loaded {len(self.documents)} documents from cache.")
        else:
            logging.info("No existing indices found. Building new indices (first run only)...")
            self.build_indices()

    def build_indices(self):
        for short_name, full_key in CANCER_TYPE_MAP.items():
            if short_name != full_key:
                continue
            for topic in ALL_TOPICS:
                refs = self.static_reference_system.get_references_for_topic(full_key, topic)
                for ref in refs:
                    key_points = ref.get('key_topics', [])
                    self.documents.append({
                        'text': f"{ref['title']}. Topics: {', '.join(key_points)}",
                        'metadata': {
                            'source': ref.get('organization', ref.get('journal', 'Clinical Reference')),
                            'cancer_type': full_key,
                            'title': ref['title'],
                            'url': ref.get('url', f"https://pubmed.ncbi.nlm.nih.gov/{ref['pmid']}/" if 'pmid' in ref else '#' ),
                            'key_points': key_points,
                            'evidence_level': ref.get('evidence_level', 'N/A')
                        }
                    })

        seen = set()
        unique_docs = []
        for doc in self.documents:
            if doc['metadata']['title'] not in seen:
                unique_docs.append(doc)
                seen.add(doc['metadata']['title'])
        self.documents = unique_docs

        if not self.documents:
            logging.warning("No documents found from the reference system. Only PubMed results will be returned.")
            return

        logging.info(f"Encoding {len(self.documents)} documents for FAISS index...")
        embeddings = self.embedding_model.encode(
            [doc['text'] for doc in self.documents],
            convert_to_tensor=True,
            show_progress_bar=True
        )
        embeddings = embeddings.cpu().numpy()

        self.faiss_index = faiss.IndexFlatL2(embeddings.shape[1])
        self.faiss_index.add(embeddings)

        tokenized_corpus = [doc['text'].split(" ") for doc in self.documents]
        self.bm25_index = BM25Okapi(tokenized_corpus)

        faiss.write_index(self.faiss_index, str(self.faiss_index_path))
        self.documents_path.write_text(json.dumps(self.documents, indent=4))
        logging.info(f"Saved {len(self.documents)} documents to cache.")

    def search_pubmed(self, query: str, max_results: int = 5):
        logging.info(f"Searching PubMed for: '{query}'")
        try:
            handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
            record = Entrez.read(handle)
            handle.close()
            id_list = record["IdList"]
            if not id_list:
                return []

            handle = Entrez.efetch(db="pubmed", id=id_list, rettype="xml", retmode="xml")
            records = Entrez.read(handle)
            handle.close()

            pubmed_docs = []
            for article in records["PubmedArticle"]:
                try:
                    medline = article["MedlineCitation"]
                    pmid = str(medline["PMID"])
                    art = medline["Article"]
                    title = str(art["ArticleTitle"])

                    abstract_obj = art.get("Abstract", {}).get("AbstractText", "")
                    if isinstance(abstract_obj, list):
                        abstract = " ".join(str(a) for a in abstract_obj)
                    else:
                        abstract = str(abstract_obj)

                    pubmed_docs.append({
                        'text': f"{title}. {abstract}",
                        'metadata': {
                            'source': 'PubMed',
                            'title': title,
                            'url': f'https://pubmed.ncbi.nlm.nih.gov/{pmid}/'
                        }
                    } )
                except (KeyError, IndexError) as e:
                    logging.warning(f"Skipping malformed PubMed record: {e}")
                    continue

            logging.info(f"Found {len(pubmed_docs)} results on PubMed.")
            return pubmed_docs
        except Exception as e:
            logging.error(f"PubMed search failed (non-fatal): {e}")
            return []

    def reciprocal_rank_fusion(self, result_lists, k=60):
        scores = {}
        for results in result_lists:
            for i, doc in enumerate(results):
                title = doc['metadata']['title']
                scores[title] = scores.get(title, 0) + 1 / (k + i + 1)
        return sorted(scores.items(), key=lambda item: item[1], reverse=True)

    def rerank(self, query, documents, top_k=10):
        if not documents:
            return []
        logging.info(f"Re-ranking {len(documents)} candidates with cross-encoder...")
        pairs = [[query, doc['text']] for doc in documents]
        scores = self.cross_encoder.predict(pairs, show_progress_bar=True)
        doc_scores = sorted(zip(documents, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in doc_scores[:top_k]]

    def retrieve(self, query: str, cancer_type: str, top_k: int = 10):
        logging.info(f"Retrieving documents for query: '{query}'")

        pubmed_results = self.search_pubmed(query, max_results=5)

        if self.faiss_index is not None and len(self.documents) > 0:
            query_embedding = self.embedding_model.encode(
                query, convert_to_tensor=True
            ).cpu().numpy().reshape(1, -1)

            _, faiss_indices = self.faiss_index.search(query_embedding, min(top_k * 2, len(self.documents)))
            semantic_results = [self.documents[i] for i in faiss_indices[0]]

            bm25_scores = self.bm25_index.get_scores(query.split(" "))
            bm25_indices = np.argsort(bm25_scores)[::-1][:top_k * 2]
            keyword_results = [self.documents[i] for i in bm25_indices]

            unique_results = {
                doc['metadata']['title']: doc
                for doc in semantic_results + keyword_results + pubmed_results
            }
            ranked_list = self.reciprocal_rank_fusion([semantic_results, keyword_results, pubmed_results])
            rerank_candidates = [
                unique_results[title]
                for title, _ in ranked_list[:top_k * 2]
                if title in unique_results
            ]
            reranked_results = rerank_candidates[:top_k]
        else:
            logging.warning("FAISS index unavailable. Returning PubMed results only.")
            reranked_results = pubmed_results

        full_cancer_key = CANCER_TYPE_MAP.get(cancer_type, cancer_type)
        static_refs = []
        for topic in ALL_TOPICS:
            refs = self.static_reference_system.get_references_for_topic(full_cancer_key, topic)
            for ref in refs:
                static_refs.append({
                    'title': ref['title'],
                    'source': ref.get('organization', ref.get('journal', 'Clinical Reference')),
                    'url': ref.get('url', f"https://pubmed.ncbi.nlm.nih.gov/{ref['pmid']}/" if 'pmid' in ref else '#' ),
                    'key_points': ref.get('key_topics', []),
                    'evidence_level': ref.get('evidence_level', 'N/A')
                })

        seen_static = set()
        unique_static = []
        for ref in static_refs:
            if ref['title'] not in seen_static:
                unique_static.append(ref)
                seen_static.add(ref['title'])

        final_results = unique_static
        final_titles = {ref['title'] for ref in unique_static}
        for res in reranked_results:
            title = res.get('title') or res.get('metadata', {}).get('title', '')
            if title not in final_titles:
                final_results.append(res)
                final_titles.add(title)

        return final_results[:top_k]
