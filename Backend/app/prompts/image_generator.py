"""Prompt composition for GPT Image generation and editing.

The image model takes a single prompt string (plus, for edits, the prior
image). We always wrap the creative concept prompt with a fixed fidelity
guardrail so product identity is preserved regardless of what the planner
or revision-merge step produced.
"""

FIDELITY_GUARDRAILS = """Preserve the real product's identity exactly: same shape, proportions, \
materials, colors, and any visible labels or packaging text from the source photo. Do not invent \
a different product variant. Do not add features, accessories, or packaging elements that are not \
visibly present in the source photo. Do not render any additional text, price, or logo that was \
not in the source photo."""


def build_generation_prompt(concept_prompt: str, aspect_ratio: str) -> str:
    return (
        f"{concept_prompt.strip()}\n\n{FIDELITY_GUARDRAILS}\n" f"Compose for a {aspect_ratio} Instagram post."
    )


def build_edit_prompt(previous_prompt: str, instruction: str) -> str:
    return (
        f"Starting from this existing image, apply the following change: {instruction.strip()}\n\n"
        f"Keep everything else from the original consistent, including: {previous_prompt.strip()}\n\n"
        f"{FIDELITY_GUARDRAILS}"
    )
