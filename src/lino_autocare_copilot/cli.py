"""Command-line RAG demo for Lino AutoCare Copilot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bedrock import generate_answer
from .retriever import AutoCareRetriever


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ask Lino questions using the approved AutoCare knowledge base."
    )
    parser.add_argument(
        "question",
        help="Vehicle, tyre, oil, or service question",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Number of sources to retrieve",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data",
        help="Directory containing the approved project datasets",
    )
    args = parser.parse_args()

    retriever = AutoCareRetriever(args.data_dir)
    results = retriever.search(args.question, top_k=args.top_k)
    safety_notice = retriever.urgent_safety_notice(args.question)

    answer = generate_answer(
        question=args.question,
        sources=results,
        safety_notice=safety_notice,
    )

    output = {
        "question": args.question,
        "answer": answer,
        "safety_notice": safety_notice,
        "supported": bool(results),
        "sources": [result.to_dict() for result in results],
    }

    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()