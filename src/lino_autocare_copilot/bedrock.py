"""Generate source-grounded answers with Amazon Nova 2 Lite."""

from __future__ import annotations

import boto3

from .retriever import SearchResult


MODEL_ID = "us.amazon.nova-2-lite-v1:0"

SYSTEM_PROMPT = """
You are Lino, a source-grounded autocare assistant.
Answer using only the supplied context.
Never invent prices, stock availability, vehicle specifications, or diagnoses.
If the context is insufficient, say you do not have enough verified information.
Treat vehicle symptoms as possibilities, not confirmed diagnoses.
Keep answers concise and mention the supplied source.
""".strip()


def generate_answer(
    question: str,
    sources: list[SearchResult],
    safety_notice: str | None = None,
) -> str:
    """Send retrieved sources to Nova 2 Lite and return its grounded answer."""

    if not sources:
        return "I do not have enough verified information to answer that question."

    context = "\n\n".join(
        f"Source: {source.source_title}\n{source.content}"
        for source in sources
    )

    prompt = f"""
SAFETY NOTICE
{safety_notice or "None"}

CONTEXT
{context}

QUESTION
{question}
""".strip()

    client = boto3.client("bedrock-runtime", region_name="us-east-1")

    response = client.converse(
        modelId=MODEL_ID,
        system=[{"text": SYSTEM_PROMPT}],
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
        inferenceConfig={
            "maxTokens": 300,
            "temperature": 0.1,
        },
        additionalModelRequestFields={
            "reasoningConfig": {"type": "disabled"}
        },
    )

    for block in response["output"]["message"]["content"]:
        if "text" in block:
            return block["text"].strip()

    raise RuntimeError("Nova 2 Lite returned no text response.")