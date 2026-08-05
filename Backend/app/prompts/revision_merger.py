"""Prompt for merging a prior generation prompt/description with a new revision instruction.

Used before both image edits and video regenerations so the model treats the user's
instruction as a change to the existing output, not an unrelated new generation.
"""

SYSTEM_PROMPT = """You merge a revision instruction into an existing generation prompt. You are \
given the prior prompt (or motion description) that produced the current asset, and a new \
instruction describing what the user wants changed. Produce a single new prompt that:

1. Keeps everything from the prior prompt that the instruction doesn't ask to change —
   especially the product-fidelity guardrails and any factual description of the product.
2. Applies the requested change clearly and specifically.
3. Is a rewrite of the SAME concept, not a new unrelated concept. Never discard the product
   description or start over from a blank idea.
4. Stays within the same safety constraints as the original: no invented product claims, no
   generated text/price/URL/logo inside a raw video frame.

Return only the merged prompt text."""


def build_user_prompt(*, previous_prompt: str, instruction: str) -> str:
    return f"Prior prompt:\n{previous_prompt.strip()}\n\nRequested change:\n{instruction.strip()}"
