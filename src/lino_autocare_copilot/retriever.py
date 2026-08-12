"""Local, source-grounded retrieval for Lino AutoCare Copilot."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.pipeline import FeatureUnion


URGENT_TERMS = {
    "brake failure",
    "brakes failed",
    "cannot steer",
    "loss of steering",
    "overheating",
    "smoke",
    "fuel smell",
    "tyre blowout",
    "tire blowout",
    "bulge"
}


@dataclass(frozen=True)
class Document:
    id: str
    title: str
    content: str
    source_title: str
    source_url: str
    category: str
    safety_level: str = "routine"
    price_status: str | None = None


@dataclass(frozen=True)
class SearchResult:
    id: str
    title: str
    content: str
    category: str
    source_title: str
    source_url: str
    score: float
    safety_level: str
    price_status: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AutoCareRetriever:
    """TF-IDF baseline that searches only approved, PII-free project data."""

    def __init__(self, data_dir: str | Path):
        self.data_dir = Path(data_dir)
        self.documents = self._load_documents()
        if not self.documents:
            raise ValueError("No approved documents were loaded.")
        self.vectorizer = FeatureUnion(
            [
                (
                     "word",
                    TfidfVectorizer(
                        lowercase=True,
                        ngram_range=(1, 2),
                        stop_words="english",
                        strip_accents="unicode",
                        sublinear_tf=True,
                    ),
               ),
               (
                   "character",
                   TfidfVectorizer(
                       analyzer="char_wb",
                       lowercase=True,
                       ngram_range=(3, 5),
                       strip_accents="unicode",
                       sublinear_tf=True,
                    ),
                ),
            ],
            transformer_weights={
                "word": 0.7,
                "character": 0.3,
            },
        )
        corpus = [f"{d.title} {d.category} {d.content}" for d in self.documents]
        self.matrix = self.vectorizer.fit_transform(corpus)

    def _load_documents(self) -> list[Document]:
        docs = self._load_knowledge_seed()
        docs.extend(self._load_business_catalog())
        return docs

    def _load_knowledge_seed(self) -> list[Document]:
        path = self.data_dir / "autocare_knowledge_seed.jsonl"
        docs: list[Document] = []
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                item = json.loads(line)
                docs.append(
                    Document(
                        id=item["id"],
                        title=item["title"],
                        content=item["content"],
                        source_title=item["source_title"],
                        source_url=item["source_url"],
                        category=item["category"],
                        safety_level=item.get("safety_level", "routine"),
                    )
                )
        return docs

    def _load_business_catalog(self) -> list[Document]:
        path = self.data_dir / "lino_business_catalog.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        docs: list[Document] = []

        for index, item in enumerate(catalog["confirmed_services"], start=1):
            price = f"₦{item['current_price_ngn']:,.0f}"
            docs.append(
                Document(
                    id=f"SERVICE-{index:03d}",
                    title=item["service"],
                    content=f"{item['service']} costs {price}. This is a confirmed current fixed price.",
                    source_title="Lino confirmed service catalogue",
                    source_url="internal://lino/confirmed-services",
                    category="service_price",
                    price_status=item["status"],
                )
            )

        for index, item in enumerate(catalog["tyre_catalog"]["products"], start=1):
            price = f"₦{item['latest_recorded_unit_price_ngn']:,.0f}"
            content = (
                f"Tyre size {item['size_normalized']}; product {item['product_name']}; "
                f"brand or description {item.get('brand_or_description')}; latest historical unit price "
                f"{price} recorded on {item['latest_recorded_date']}. Confirm the current price and vehicle "
                "fitment before quoting or selling."
            )
            docs.append(
                Document(
                    id=f"TYRE-{index:03d}",
                    title=f"{item['size_normalized']} — {item.get('brand_or_description')}",
                    content=content,
                    source_title="Lino historical tyre catalogue",
                    source_url="internal://lino/historical-tyres",
                    category="tyre_product",
                    safety_level="caution",
                    price_status=item["price_status"],
                )
            )

        for index, item in enumerate(catalog["engine_oil_catalog"]["products"], start=1):
            price = f"₦{item['latest_recorded_unit_price_ngn']:,.0f}"
            content = (
                f"Engine oil product {item['product_name']}; brand {item.get('brand')}; viscosity "
                f"{item.get('viscosity')}; pack size {item.get('pack_size_litres')} litres; latest historical "
                f"unit price {price} recorded on {item['latest_recorded_date']}. Confirm the vehicle's required "
                "oil specification and the current price before recommending it."
            )
            docs.append(
                Document(
                    id=f"OIL-{index:03d}",
                    title=item["product_name"],
                    content=content,
                    source_title="Lino historical engine-oil catalogue",
                    source_url="internal://lino/historical-engine-oils",
                    category="engine_oil_product",
                    safety_level="caution",
                    price_status=item["price_status"],
                )
            )
        return docs

    def search(self, query: str, top_k: int = 5, minimum_score: float = 0.18) -> list[SearchResult]:
        query = query.strip()
        if not query:
            raise ValueError("Query must not be empty.")
        top_k = max(1, min(int(top_k), 10))
        expanded_query = query

        if any(
            term in query.casefold()
            for term in ("bulge", "bulged", "bulging")
        ):
            expanded_query = (
                f"{query} tyre damage bulges cuts cracks "
                "exposed material unusual deformation"
            )

        query_vector = self.vectorizer.transform([expanded_query])
        scores = cosine_similarity(query_vector, self.matrix).ravel()
        ranked = scores.argsort()[::-1]

        results: list[SearchResult] = []
        for index in ranked:
            score = float(scores[index])
            if score < minimum_score:
                break
            doc = self.documents[int(index)]
            results.append(
                SearchResult(
                    id=doc.id,
                    title=doc.title,
                    content=doc.content,
                    category=doc.category,
                    source_title=doc.source_title,
                    source_url=doc.source_url,
                    score=round(score, 4),
                    safety_level=doc.safety_level,
                    price_status=doc.price_status,
                )
            )
            if len(results) == top_k:
                break
        return results

    @staticmethod
    def urgent_safety_notice(query: str) -> str | None:
        lowered = query.casefold()
        if any(term in lowered for term in URGENT_TERMS):
            return (
                "Safety warning: stop driving as soon as it is safe and arrange professional inspection. "
                "Do not rely on a chatbot to confirm a safety-critical fault."
            )
        return None
