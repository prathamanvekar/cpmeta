"""
analyzer.py - Ollama API client and robust JSON extraction engine.
Handles calling the local LLM at /api/generate, managing timeouts, retries,
and multi-stage defensive JSON extraction for cpmeta.
"""

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple
import requests

from prompts import (
    CUMULATIVE_SYSTEM_PROMPT,
    CUMULATIVE_USER_PROMPT_TEMPLATE,
    SINGLE_PROBLEM_SYSTEM_PROMPT,
    SINGLE_PROBLEM_USER_PROMPT_TEMPLATE,
)

DEFAULT_OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL = "qwen2.5-coder:7b"


def get_base_url(custom_url: Optional[str] = None) -> str:
    """Returns normalized Ollama base URL without trailing slash."""
    url = (custom_url or os.environ.get("OLLAMA_BASE_URL") or DEFAULT_OLLAMA_BASE_URL).strip()
    return url.rstrip("/")


def check_ollama_connection(base_url: Optional[str] = None, timeout: float = 3.0) -> Tuple[bool, str, List[str]]:
    """
    Checks if the Ollama server is running and queries /api/tags to list installed models.
    Returns: (is_reachable: bool, status_message: str, installed_models: list[str])
    """
    url = get_base_url(base_url)
    try:
        response = requests.get(f"{url}/api/tags", timeout=timeout)
        if response.status_code == 200:
            data = response.json()
            models_info = data.get("models", [])
            model_names = [m.get("name", "") for m in models_info if m.get("name")]
            return True, f"Connected to Ollama at {url}", model_names
        return False, f"Ollama returned HTTP status {response.status_code}", []
    except requests.exceptions.ConnectionError:
        return (
            False,
            f"Cannot connect to Ollama at {url}. Ensure Ollama is running (`ollama serve`).",
            [],
        )
    except requests.exceptions.Timeout:
        return (
            False,
            f"Connection to Ollama at {url} timed out after {timeout}s.",
            [],
        )
    except Exception as exc:
        return False, f"Error checking Ollama connection: {str(exc)}", []


def extract_json_from_text(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Multi-stage defensive JSON extractor:
    1. Direct json.loads()
    2. Regex match within ```json ... ``` or ``` ... ```
    3. First '{' to last '}' bracket extraction
    4. Heuristic cleanup of common LLM syntax slip-ups (trailing commas)
    """
    if not raw_text or not raw_text.strip():
        return None

    cleaned = raw_text.strip()

    # Stage 1: Direct attempt
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Stage 2: Extract from markdown code blocks
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if code_block_match:
        block_content = code_block_match.group(1).strip()
        try:
            return json.loads(block_content)
        except Exception:
            pass

    # Stage 3: First '{' and last '}' substring
    start_idx = cleaned.find("{")
    end_idx = cleaned.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        candidate = cleaned[start_idx : end_idx + 1]
        try:
            return json.loads(candidate)
        except Exception:
            # Stage 4: Clean up trailing commas in objects/arrays
            try:
                sanitized = re.sub(r",\s*([\]}])", r"\1", candidate)
                return json.loads(sanitized)
            except Exception:
                pass

    return None


def call_ollama(
    prompt: str,
    system: str,
    model_name: str = DEFAULT_MODEL,
    base_url: Optional[str] = None,
    timeout: int = 180,
    max_retries: int = 1,
) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Executes a POST request to Ollama's /api/generate with system prompt,
    handles retries on network or parse failure.
    Returns: (parsed_json_or_none, raw_llm_text, error_message_or_none)
    """
    url = f"{get_base_url(base_url)}/api/generate"
    payload = {
        "model": model_name,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 2048,
        },
    }

    last_raw_text = ""
    last_error = None

    for attempt in range(max_retries + 1):
        # On retry, emphasize strict JSON in prompt
        curr_prompt = prompt
        if attempt > 0:
            curr_prompt = f"{prompt}\n\nIMPORTANT: Your previous response was not parseable JSON. Output STRICT JSON ONLY."

        payload["prompt"] = curr_prompt

        try:
            response = requests.post(url, json=payload, timeout=timeout)
            if response.status_code != 200:
                last_error = f"Ollama returned HTTP {response.status_code}: {response.text}"
                continue

            resp_json = response.json()
            raw_response = resp_json.get("response", "")
            last_raw_text = raw_response

            parsed = extract_json_from_text(raw_response)
            if parsed is not None:
                return parsed, raw_response, None
            else:
                last_error = "LLM response did not contain valid JSON."

        except requests.exceptions.ConnectionError:
            last_error = f"Connection failed to Ollama at {url}. Is `ollama serve` active?"
            break
        except requests.exceptions.Timeout:
            last_error = f"Ollama generation timed out after {timeout} seconds."
            break
        except Exception as exc:
            last_error = f"Unexpected request failure: {str(exc)}"

    return None, last_raw_text, last_error


def build_single_problem_fallback(
    raw_notes: str,
    problem_title: str,
    raw_output: str,
    error_msg: str,
) -> Dict[str, Any]:
    """Generates a graceful fallback dictionary matching the exact single problem schema."""
    return {
        "problem_analysis": {
            "core_topics": ["Competitive Programming", "Pattern Recognition"],
            "difficulty_tier": "Unspecified (Parsing Fallback)",
            "key_insight": f"Analysis encountered a formatting issue. Raw output saved below.",
        },
        "thinking_analysis": {
            "correct_moves": ["Problem was practiced and notes were recorded."],
            "stall_points": [
                {
                    "timestamp_range": "N/A",
                    "duration_minutes": 0,
                    "description": f"Parser notice: {error_msg}",
                    "root_cause": "LLM response was not valid JSON.",
                }
            ],
            "behavioral_observations": [
                "Detailed timestamp notes logged.",
                "Review raw LLM output for qualitative insights."
            ],
        },
        "recommendations": {
            "topics_to_strengthen": ["Edge Case Analysis", "Invariant Proofs"],
            "behavioral_advice": "Check constraints and verify sample cases manually before coding.",
            "similar_problems": [],
        },
        "_is_fallback": True,
        "_raw_output": raw_output,
        "_error": error_msg,
    }


def build_cumulative_fallback(raw_output: str, error_msg: str) -> Dict[str, Any]:
    """Generates a graceful fallback dictionary matching the cumulative schema."""
    return {
        "weak_topics": [
            {
                "topic": "Synthesis Fallback",
                "frequency": 1,
                "severity": "Medium",
                "evidence": f"Failed to parse cumulative LLM JSON output. Reason: {error_msg}",
            }
        ],
        "strong_topics": [
            {
                "topic": "Consistency",
                "frequency": 1,
                "evidence": "Regular problem practice and timestamped metacognition logging.",
            }
        ],
        "behavioral_patterns": [
            {
                "pattern": "Consistent note recording during sessions",
                "type": "strength",
                "frequency": 1,
            }
        ],
        "study_plan": [
            {
                "priority": 1,
                "action": "Ensure Ollama model output is running cleanly with low temperature.",
                "reason": f"Parsing error occurred: {error_msg}",
            }
        ],
        "overall_assessment": f"Cumulative analysis was completed but JSON decoding failed: {error_msg}. Check raw output.",
        "_is_fallback": True,
        "_raw_output": raw_output,
        "_error": error_msg,
    }


def analyze_single_problem(
    problem_statement: str,
    raw_notes: str,
    platform: str = "LeetCode",
    problem_title: str = "Untitled Problem",
    solved: bool = True,
    time_taken_minutes: int = 30,
    model_name: str = DEFAULT_MODEL,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyzes a single problem's statement and timestamped thinking notes.
    Returns parsed dictionary matching SINGLE_PROBLEM_SYSTEM_PROMPT schema.
    """
    user_prompt = SINGLE_PROBLEM_USER_PROMPT_TEMPLATE.format(
        platform=platform,
        problem_title=problem_title,
        outcome="SOLVED (Accepted)" if solved else "UNSOLVED / TIMED OUT",
        time_taken_minutes=time_taken_minutes,
        problem_statement=problem_statement.strip(),
        raw_notes=raw_notes.strip(),
    )

    parsed_json, raw_text, error_msg = call_ollama(
        prompt=user_prompt,
        system=SINGLE_PROBLEM_SYSTEM_PROMPT,
        model_name=model_name,
        base_url=base_url,
    )

    if parsed_json is not None:
        return parsed_json

    return build_single_problem_fallback(
        raw_notes=raw_notes,
        problem_title=problem_title,
        raw_output=raw_text,
        error_msg=error_msg or "Unknown JSON decoding error.",
    )


def analyze_cumulative(
    sessions_data: Dict[str, Any],
    model_name: str = DEFAULT_MODEL,
    base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Synthesizes cumulative practice logs across multiple sessions.
    Returns parsed dictionary matching CUMULATIVE_SYSTEM_PROMPT schema.
    """
    summary_text = sessions_data.get("condensed_log", "")
    session_count = sessions_data.get("session_count", 0)

    user_prompt = CUMULATIVE_USER_PROMPT_TEMPLATE.format(
        session_count=session_count,
        cumulative_data_summary=summary_text,
    )

    parsed_json, raw_text, error_msg = call_ollama(
        prompt=user_prompt,
        system=CUMULATIVE_SYSTEM_PROMPT,
        model_name=model_name,
        base_url=base_url,
    )

    if parsed_json is not None:
        return parsed_json

    return build_cumulative_fallback(
        raw_output=raw_text,
        error_msg=error_msg or "Unknown JSON decoding error.",
    )
