from typing import List, Optional
from ..config import settings
from ..schemas.document import Citation, QueryResponse

# Standardized fallback message when retrieved context is absent or below similarity threshold
UNGROUNDED_FALLBACK_MESSAGE = (
    "The provided equipment manuals do not contain sufficient verified technical details to answer this query. "
    "Please consult official manufacturer engineering support or verify the manual has been ingested."
)

GROUNDED_SYSTEM_PROMPT = """You are GridGuard AI, a certified electrical substation engineering assistant specializing in technical documentation, protective relays, switchgear, and power transformers (ABB, Siemens, Schneider Electric).

CRITICAL GROUNDING RULES:
1. Answer ONLY using the facts, ratings, wiring schematics, and procedures explicitly stated in the Provided Technical Excerpts below.
2. NEVER guess, extrapolate, or assume unstated specifications. If the excerpts do not contain the exact information needed, output EXACTLY:
"{fallback_message}"
3. CITATION ENFORCEMENT: Every statement, step, or technical parameter MUST include an inline citation citing the exact document name and page number, in the format:
   [Document: <document_name> | Page: <page_num>]
4. Highlight safety warnings, trip curves, and operational voltage/current limits prominently when present.
"""

USER_PROMPT_TEMPLATE = """Provided Technical Excerpts:
----------------------------------------
{context_block}
----------------------------------------

Technical Operator Query: {query}

Provide a concise, technically grounded answer citing the source document and page number for each point. If the excerpts are insufficient, output the fallback message."""


def format_context_block(citations: List[Citation]) -> str:
    """
    Format a list of retrieved citations into a structured, labeled context block.
    """
    if not citations:
        return "No relevant technical documentation excerpts found."

    blocks = []
    for i, cit in enumerate(citations, 1):
        header = f"--- Excerpt {i} [Document: {cit.document_name} | Manufacturer: {cit.manufacturer} | Asset: {cit.asset_type} | Page: {cit.page_num} | Similarity: {cit.similarity_score:.2f}] ---"
        blocks.append(f"{header}\n{cit.excerpt.strip()}")

    return "\n\n".join(blocks)


def build_qa_prompt(query: str, citations: List[Citation]) -> str:
    """
    Construct the full prompt for grounded Q&A with system instructions and formatted context.
    """
    system_part = GROUNDED_SYSTEM_PROMPT.format(
        fallback_message=UNGROUNDED_FALLBACK_MESSAGE
    )
    context_block = format_context_block(citations)
    user_part = USER_PROMPT_TEMPLATE.format(
        context_block=context_block,
        query=query,
    )
    return f"{system_part}\n\n{user_part}"


def generate_grounded_answer(
    query: str,
    citations: List[Citation],
    similarity_threshold: Optional[float] = None,
) -> QueryResponse:
    """
    Synthesize a grounded answer response.
    If retrieved citations are empty or maximum similarity is below threshold,
    strictly enforces the ungrounded fallback message to eliminate hallucinations.
    """
    threshold = similarity_threshold or settings.SIMILARITY_THRESHOLD

    if not citations:
        return QueryResponse(
            query=query,
            answer=UNGROUNDED_FALLBACK_MESSAGE,
            citations=[],
            is_grounded=False,
            max_similarity=0.0,
        )

    max_sim = max(c.similarity_score for c in citations)

    # Check if context meets the cosine similarity confidence threshold
    if max_sim < threshold:
        return QueryResponse(
            query=query,
            answer=UNGROUNDED_FALLBACK_MESSAGE,
            citations=citations,
            is_grounded=False,
            max_similarity=max_sim,
        )

    # In baseline Sprint 1, construct the grounded answer directly with citations
    grounded_points = []
    for cit in citations:
        if cit.similarity_score >= threshold:
            # Extract first sentence or headline from excerpt
            excerpt_summary = cit.excerpt.strip().split("\n")[0][:180]
            grounded_points.append(
                f"- {excerpt_summary} [Document: {cit.document_name} | Page: {cit.page_num}]"
            )

    if not grounded_points:
        answer = UNGROUNDED_FALLBACK_MESSAGE
        is_grounded = False
    else:
        answer = (
            f"Based on verified substation equipment documentation:\n\n"
            + "\n".join(grounded_points)
        )
        is_grounded = True

    valid_citations = [c for c in citations if c.similarity_score >= threshold]
    relevant_images: List[str] = []
    for c in valid_citations:
        for img in c.images:
            if img not in relevant_images:
                relevant_images.append(img)

    return QueryResponse(
        query=query,
        answer=answer,
        citations=valid_citations,
        images=relevant_images,
        is_grounded=is_grounded,
        max_similarity=max_sim,
    )
