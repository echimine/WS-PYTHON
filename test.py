from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from openai import OpenAI
from Message import *  # tu as tes enums ici

# Configuration connexion serveur llama.cpp
BASE_URL = os.environ.get("LLAMA_CPP_BASE_URL", "http://127.0.0.1:8080/v1")
API_KEY = os.environ.get("LLAMA_CPP_API_KEY", "devkey")
MODEL_NAME = os.environ.get("LLAMA_CPP_MODEL", "functiongemma-270m-it-Q4_K_M.gguf")


# --- Fonctions Python exposées ---
def convert_currency(amount: float, currency_from: str, currency_to: str) -> Dict[str, Any]:
    rates = {("EUR", "USD"): 1.08, ("USD", "EUR"): 0.93}
    rate = rates.get((currency_from.upper(), currency_to.upper()))
    if rate is None:
        raise ValueError(f"Aucun taux démo pour {currency_from}->{currency_to}")
    from datetime import timezone
    return {
        "original_amount": amount,
        "original_currency": currency_from.upper(),
        "amount": round(amount * rate, 2),
        "currency": currency_to.upper(),
        "rate_used": rate,
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def add_days(start_date: str, days: int) -> Dict[str, Any]:
    base = datetime.fromisoformat(start_date)
    target = base + timedelta(days=days)
    return {"result_date": target.date().isoformat()}


def get_room_temperature(**kwargs) -> Dict[str, Any]:
    temperature = 20
    return {
        "message_type": MessageType.ENVOI.SENSOR,
        "sensor_id": SENSOR_ID.TEMPERATURE,
        "temperature": temperature,
    }


def switch_on_light(index: int, dest: str = "ALL") -> Dict[str, Any]:
    return {
        "message_type": MessageType.ENVOI.SENSOR,
        "sensor_id": SENSOR_ID.LED,
        "led_id": index,
        "dest": dest,
        "state": "on",
    }


FUNC_MAP = {
    "convert_currency": convert_currency,
    "add_days": add_days,
    "get_room_temperature": get_room_temperature,
    "switch_on_light": switch_on_light,
}

# Déclarations simplifiées pour le prompt (format attendu par FunctionGemma)
TOOL_DECLARATIONS_TEXT = [
    {
        "name": "convert_currency",
        "description": "Convert an amount between two currencies.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "currency_from": {"type": "string"},
                "currency_to": {"type": "string"},
            },
            "required": ["amount", "currency_from", "currency_to"],
        },
    },
    {
        "name": "add_days",
        "description": "Add days to a date (YYYY-MM-DD).",
        "parameters": {
            "type": "object",
            "properties": {
                "start_date": {"type": "string"},
                "days": {"type": "integer"},
            },
            "required": ["start_date", "days"],
        },
    },
    {
        "name": "get_room_temperature",
        "description": "Get the current room temperature and humidity.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "switch_on_light",
        "description": "Turn on a light.",
        "parameters": {
            "type": "object",
            "properties": {"index": {"type": "integer"}, "dest": {"type": "string"}},
            "required": ["index", "dest"],
        },
    },
]

SYSTEM_PROMPT = """<start_of_turn>system
You are a helpful assistant. You have access to these functions:

"""

FUNCTION_CALL_INSTRUCTION = """
Example: If user says "Convert 100 USD to EUR", respond with:
{"name": "convert_currency", "parameters": {"amount": 100, "currency_from": "USD", "currency_to": "EUR"}}

Example: If user says "What date is 10 days after 2024-01-15", respond with:
{"name": "add_days", "parameters": {"start_date": "2024-01-15", "days": 10}}

Example: If user says "What is the temperature in the room" or "Quelle température fait-il", respond with:
{"name": "get_room_temperature", "parameters": {}}

Example: If user says "Turn on the light at index 1 of ESP32_ELIOTT", respond with:
{"name": "switch_on_light", "parameters": {"index": 1, "dest": "ESP32_ELIOTT"}}

Example: If user says "Allume la led 5 de ALL", respond with:
{"name": "switch_on_light", "parameters": {"index": 5, "dest": "ALL"}}

IMPORTANT: Output ONLY the JSON. No text before or after.
IMPORTANT: You MUST extract the EXACT number from the user's request. Do NOT copy the examples.
<end_of_turn>
<start_of_turn>user
"""


def build_prompt_with_tools(user_prompt: str) -> str:
    tools_json = json.dumps(TOOL_DECLARATIONS_TEXT, indent=2, ensure_ascii=False)
    return (
        f"{SYSTEM_PROMPT}{tools_json}{FUNCTION_CALL_INSTRUCTION}"
        f"{user_prompt}<end_of_turn>\n<start_of_turn>model\n"
    )


def clean_parameters(params: Any) -> Dict[str, Any]:
    if not isinstance(params, dict):
        return {}
    if params.get("type") == "object":  # le modèle a recraché le schéma
        return {}
    return params


def fix_json_trailing_commas(text: str) -> str:
    import re
    text = re.sub(r",\s*}", "}", text)
    text = re.sub(r",\s*]", "]", text)
    return text


def parse_function_call(response: str) -> Optional[Dict[str, Any]]:
    text = response.strip()

    text = text.replace("<start_function_call>", "").replace("<end_function_call>", "")
    text = text.replace("<end_of_turn>", "").strip()

    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines and lines[-1].startswith("```") else lines[1:])

    text = fix_json_trailing_commas(text)

    try:
        data = json.loads(text)
        if isinstance(data, dict) and "name" in data:
            data["parameters"] = clean_parameters(data.get("parameters", {}))
            return data
    except json.JSONDecodeError:
        import re
        match = re.search(
            r'\{[^{}]*"name"\s*:\s*"[^"]+"\s*,\s*"parameters"\s*:\s*\{[^}]*\}[^}]*\}',
            text,
            re.DOTALL,
        )
        if match:
            try:
                fixed = fix_json_trailing_commas(match.group())
                parsed = json.loads(fixed)
                parsed["parameters"] = clean_parameters(parsed.get("parameters", {}))
                return parsed
            except json.JSONDecodeError:
                pass

    return None


def run_chat(user_prompt: str) -> Dict[str, Any]:
    """
    Retourne toujours un dict JSON (sans print).
    """
    client = OpenAI(base_url=BASE_URL, api_key=API_KEY)
    full_prompt = build_prompt_with_tools(user_prompt)

    resp = client.completions.create(
        model=MODEL_NAME,
        prompt=full_prompt + '{"name": "',  # tu veux garder ton forcing
        temperature=0.0,
        max_tokens=120,
        stop=["\n", "<end_of_turn>", "<end_function_call>"],
    )

    raw_response = '{"name": "' + (resp.choices[0].text or "")

    func_call = parse_function_call(raw_response)
    if func_call is None:
        # Le modèle n'a pas sorti un tool-call parsable
        return {"type": "final", "raw": raw_response}

    name = func_call.get("name", "")
    params = func_call.get("parameters", {})

    func = FUNC_MAP.get(name)
    if func is None:
        return {"type": "error", "error": f"fonction '{name}' non disponible", "tool_call": func_call}

    try:
        result = func(**params)
    except Exception as exc:
        return {"type": "error", "error": str(exc), "tool_call": func_call}

    return {"type": "tool_result", "tool_call": func_call, "result": result}


def main() -> None:
    prompt = " ".join(sys.argv[1:]).strip() or "Convertis 42 EUR en USD."
    out = run_chat(prompt)
    # sortie JSON finale unique (pas de prints de debug)
    sys.stdout.write(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()