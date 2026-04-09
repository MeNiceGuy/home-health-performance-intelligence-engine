from openai import OpenAI
import os

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.3")

SYSTEM_PROMPT = """You are an expert healthcare data analyst. Extract a structured agency profile in JSON with the following fields from the free text input:
- agency_name
- region
- agency_size
- ownership_type (Privately owned, Government, Nonprofit)
- tech_stack
- challenges
- hhvbp_concerns
- workforce_issues
- budget_posture (lean budget, moderate, generous)
- leadership_readiness (low, moderate, high)
- learning_culture (nascent, developing, mature)
- notes
Only output JSON strictly with these keys and valid values."""


def parse_freeform_profile(text_input: str) -> dict:
    client = OpenAI()

    user_prompt = f"Extract the home health agency profile from this text:\n""""{text_input}""""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        max_tokens=700,
    )

    json_text = response.choices[0].message.content.strip()
    try:
        import json
        data = json.loads(json_text)
    except Exception:
        data = {}
    return data
