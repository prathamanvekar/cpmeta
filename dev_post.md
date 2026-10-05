*This is a submission for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/challenges/hacktoberfest-weekend-2026-10-01)*

## What I Built
My friend **Ved** and I have been grinding competitive programming together for months. After discussing Colin Galen's video on how top competitors dissect their practice, we started doing something specific: keeping a text file open while solving LeetCode and Codeforces problems to record **timestamped "metacognition notes"** of our thoughts:

```text
0:00 - read problem statement. contiguous subarrays with k distinct elements.
0:03 - thought about standard sliding window with two pointers.
0:06 - issue: how to count *exact* k without missing smaller left bounds?
0:12 - stuck trying to rewind left pointer. count gets messy with duplicates.
0:18 - breakthrough: exact(k) = atMost(k) - atMost(k - 1)!
0:25 - wrote helper, tested edge cases, submitted -> Accepted.
```

These notes capture our real-time **cognitive blindspots** - the exact minute we got confused, the false paths we went down, and the habits that cost us time, like jumping straight into code before proving invariants. But the moment a problem was accepted, we always discarded them.

I built **cpmeta** for Ved and myself to stop that hard-earned data from going to waste.

**cpmeta** is a project that analyzes raw thinking notes alongside the problem statement using an open-weight LLM. Instead of just handing you an algorithmic solution, it acts like an **ICPC coach** reviewing your thought process. It calculates exactly how long you stalled and diagnoses the **root cause**, such as missing a monotonic reduction trick. It also detects recurring **cognitive traps**, like abandoning valid approaches too early or overlooking problem constraints. Over time, it aggregates data across all your logged sessions to generate a **prioritized study plan** that highlights your persistent topic weaknesses and proven strengths.

When I showed it to Ved and fed his last three practice logs into the pipeline, he was stunned: *"Bro, this called out my habit of rewriting binary search from scratch every single time instead of checking invariants. We're actually using this for our contest prep."*

## Demo

Below is the full demo of the project, you may have to wait good 2 sec for it to load!

![cpmeta Full Project Demo](https://dev-to-uploads.s3.us-east-2.amazonaws.com/uploads/articles/2r1880ndjno3ilb7esdt.gif)

## Code
{% embed https://github.com/prathamanvekar/cpmeta %}

## How I Built It
The engine is powered by **Ollama** running open-weight coding models like `qwen2.5-coder:7b` locally. It connects directly to the local Ollama instance on port 11434, while also supporting remote endpoints via Cloudflare tunnels or Ngrok when needed.

To make local models output consistent coaching data instead of unstructured chat, we constrain inference to a **strict JSON schema** and pair it with a multi-stage parser that heals trailing truncations:

```python
# Querying local Ollama with JSON enforcement and defensive extraction
response = requests.post(
    f"{base_url}/api/generate",
    json={
        "model": model_name,
        "system": SINGLE_PROBLEM_SYSTEM_PROMPT,
        "prompt": user_prompt,
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.2, "top_p": 0.9},
    },
    timeout=120,
)
analysis = extract_clean_json(response.json().get("response", ""))
```

The interface is built with **Python and Streamlit**.

All sessions, raw notes, and coach metrics persist in an embedded **SQLite database** (`cpmeta.db`). For longitudinal synthesis, a custom aggregator condenses weeks of practice history into high-signal JSON summaries that fit comfortably within local LLM context windows without blowing past token limits. To ensure stable UI rendering, a multi-stage parser sanitizes raw model responses and auto-recovers valid JSON schemas.

## Why Does Open Innovation Matter?
Competitive programmers solve hundreds of problems every month. Paying metered cloud API bills for every quick thought note or practice session is unrealistic for students and independent builders. Open-weight models running on consumer hardware **cost nothing to run**, making deliberate practice truly unlimited.

Problem-solving scratchpads are also raw, unfiltered mental dumps. Keeping inference **entirely on-device** ensures that no personal notes, contest thoughts, or thinking habits ever leave the machine.

Finally, practice happens anywhere - on commutes, in libraries with restrictive firewalls, or during offline study sprints. Because cpmeta relies on local Ollama inference, the entire diagnostic suite works seamlessly **without internet access**, accounts, or third-party API dependencies.

## My Agent Session
{% agent_session 521 %}

## Prize Categories
Thinking Machines (Tinker), Render, Backboard.