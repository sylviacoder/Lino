"""HTTP API for Lino AutoCare Copilot."""

import os
from pathlib import Path
from mangum import Mangum

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .bedrock import generate_answer
from .retriever import AutoCareRetriever


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR = Path(
    os.getenv("LINO_DATA_DIR", str(DEFAULT_DATA_DIR))
)
retriever = AutoCareRetriever(DATA_DIR)


app = FastAPI(
    title="Lino AutoCare Copilot API",
    description=(
        "A source-grounded autocare assistant using local retrieval "
        "and Amazon Bedrock."
    ),
    version="0.1.0",
)


class AskRequest(BaseModel):
    """Information accepted from an API user."""

    question: str = Field(
        min_length=3,
        max_length=500,
        description="The user's autocare question",
    )
    top_k: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum number of sources to retrieve",
    )


class SourceResponse(BaseModel):
    """A source used to support Lino's answer."""

    id: str
    title: str
    content: str
    category: str
    source_title: str
    source_url: str
    score: float
    safety_level: str
    price_status: str | None = None


class AskResponse(BaseModel):
    """The complete grounded response returned by Lino."""

    question: str
    answer: str
    safety_notice: str | None
    supported: bool
    sources: list[SourceResponse]


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    """Provide basic API navigation."""

    return {
        "service": "Lino AutoCare Copilot API",
        "health": "/health",
        "documentation": "/docs",
    }


@app.get("/health", tags=["System"])
def health_check() -> dict[str, str]:
    """Confirm that the API process is running."""

    return {
        "status": "healthy",
        "service": "lino-autocare-copilot",
    }


@app.post("/ask", response_model=AskResponse, tags=["Assistant"])
def ask_question(request: AskRequest) -> AskResponse:
    """Retrieve approved evidence and generate a grounded answer."""

    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=422,
            detail="Question must contain visible text.",
        )

    results = retriever.search(
        question,
        top_k=request.top_k,
    )
    safety_notice = retriever.urgent_safety_notice(question)

    try:
        answer = generate_answer(
            question=question,
            sources=results,
            safety_notice=safety_notice,
        )
    except (BotoCoreError, ClientError, RuntimeError) as error:
        raise HTTPException(
            status_code=502,
            detail="The language-model service is temporarily unavailable.",
        ) from error

    return AskResponse(
        question=question,
        answer=answer,
        safety_notice=safety_notice,
        supported=bool(results),
        sources=[
            SourceResponse(**result.to_dict())
            for result in results
        ],
    )


handler = Mangum(app, lifespan="off")