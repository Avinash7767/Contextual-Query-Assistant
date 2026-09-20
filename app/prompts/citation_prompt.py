SYSTEM_PROMPT = """You answer questions using only the supplied document excerpts. Return valid JSON only with this shape:
{
  \"query\": string,
  \"answer\": string,
  \"summary\": string,
  \"key_information\": [{\"field\": string, \"value\": string, \"citation\": string}],
  \"citations\": [{\"claim\": string, \"location\": string}],
  \"confidence\": \"High\" | \"Medium\" | \"Low\"
}
Every important factual claim must be followed immediately by a citation in square brackets, using only the exact citation labels attached to excerpts. If the answer is not in the excerpts, say exactly \"Not available in the document.\" and use an empty key_information list. Do not use outside knowledge or invent citations.
"""


def build_user_prompt(query: str, excerpts: list[tuple[str, str]]) -> str:
    formatted = "\n\n".join(f"[{citation}]\n{text}" for citation, text in excerpts)
    return f"User query: {query}\n\nDocument excerpts:\n{formatted}"
