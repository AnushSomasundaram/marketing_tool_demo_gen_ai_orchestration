"""Prompt composition for Runway image-to-video motion prompts."""

VIDEO_FIDELITY_GUARDRAILS = """Preserve the real product's identity exactly: same shape, \
proportions, materials, and colors as the source image. Do not invent a different product \
variant or add unsupported features. Motion should stay clean and product-focused. Do not \
render any text, price, URL, or logo anywhere in the video — the frame must stay free of \
generated typography."""


def build_generation_prompt(motion_description: str) -> str:
    """Used for both first generation and revisions — a revision merges the previous
    motion description with the user's instruction upstream (see revision_merger.py),
    then starts a brand new Runway task with the merged description."""
    return f"{motion_description.strip()}\n\n{VIDEO_FIDELITY_GUARDRAILS}"
