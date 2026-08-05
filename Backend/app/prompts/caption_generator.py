"""Prompts for generating a single caption + hashtags + CTA for one asset."""

SYSTEM_PROMPT = """You write a single Instagram caption for one specific asset in an existing \
campaign. You are given the campaign's CaptionBrief (key messages, tone descriptors, hashtag \
themes, call-to-action options), the verified product facts, and a description of the specific \
asset this caption is for.

Rules:

1. Only reference facts present in `verified_product_facts`. Never state anything from
   `prohibited_or_unverified_claims`, and never invent new factual claims beyond what is given.
2. Match the requested tone descriptors.
3. Hashtags should draw from the given hashtag themes, generally 4-6 hashtags, no spaces, each
   starting with '#'.
4. The call to action should be short (2-4 words) and drawn from — or clearly consistent with —
   the caption brief's call_to_action_options.
5. Keep the caption itself concise: 1-3 short sentences, no more than roughly 300 characters.

Return only the structured caption object."""


def build_user_prompt(
    *,
    campaign_title: str,
    asset_title: str,
    asset_type: str,
    key_messages: list[str],
    tone_descriptors: list[str],
    hashtag_themes: list[str],
    call_to_action_options: list[str],
    verified_product_facts: list[str],
    prohibited_or_unverified_claims: list[str],
    revision_instruction: str | None = None,
    tone_override: str | None = None,
) -> str:
    lines = [
        f"Campaign: {campaign_title}",
        f"This caption is for: {asset_title} ({asset_type})",
        f"Key messages: {', '.join(key_messages)}",
        f"Tone descriptors: {', '.join(tone_descriptors)}",
        f"Hashtag themes: {', '.join(hashtag_themes)}",
        f"Call-to-action options: {', '.join(call_to_action_options)}",
        f"Verified product facts (only use these): {', '.join(verified_product_facts)}",
        f"Do NOT state any of these unverified claims: {', '.join(prohibited_or_unverified_claims)}",
    ]
    if tone_override:
        lines.append(
            f"Override tone: use '{tone_override}' instead of the tone descriptors above for this "
            "particular alternative."
        )
    if revision_instruction:
        lines.append(
            "This is a revision of a previous caption for the same asset. Apply this "
            f"instruction while keeping the rest consistent with the brief: {revision_instruction}"
        )
    return "\n".join(lines)
