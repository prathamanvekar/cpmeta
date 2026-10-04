# CPNotes 🧠

A thinking-process analyzer for competitive programmers. Takes raw, timestamped scratchpad notes from your practice sessions and turns them into actionable algorithmic insights, stall root causes, and targeted study plans using local LLMs.

---

## Why CPNotes?

When solving LeetCode or Codeforces problems, developers often keep scratchpad notes:

```text
0:00 - read problem statement. contiguous subarrays with k distinct elements.
0:03 - thought about standard sliding window with two pointers.
0:07 - stuck: how to count *exact* k without missing smaller left bounds?
0:15 - breakthrough: exact(k) = atMost(k) - atMost(k - 1)
0:22 - tested edge cases and submitted -> Accepted.
```

These notes capture your real-time cognitive blindspots, but usually get discarded. **CPNotes** parses your notes alongside the problem statement with a local LLM to figure out:
1. **Where and why you got stuck** (root cause analysis with exact durations).
2. **Behavioral patterns** (e.g. abandoning correct approaches too early, missing invariants).
3. **Cumulative weaknesses** across multiple sessions to tell you what to drill next.

---

## Quickstart

### 1. Prerequisites
- Python 3.10+
- [Ollama](https://ollama.ai) installed and running

```bash
# Pull the recommended model (or any coding model you prefer)
ollama pull qwen2.5-coder:7b
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the App
```bash
streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

> **Tip:** In the sidebar, click **⚡ Seed 3 Sample Sessions** to test the full pipeline and cumulative analysis immediately with pre-loaded data.

---

## Core Views

| View | Purpose |
|---|---|
| **📝 New Session** | Log problem details, outcome, and timestamped notes. Get an instant deconstruction of algorithmic insights, stall causes, and drills. Includes a **Load Sample Case** button for testing. |
| **📚 Past Sessions** | Searchable archive of all historical sessions stored in local SQLite (`cpnotes.db`). Filter by platform or solve status and inspect raw notes. |
| **📊 Cumulative Analysis** | Runs cross-session synthesis across all logged problems. Surfaces persistent topic weaknesses, mastered strengths, recurring habits, and a prioritized study plan. |

---

## Configuration

By default, CPNotes connects to Ollama at `http://localhost:11434`.

To use a remote server or tunnel (e.g. Cloudflare Tunnel, Ngrok):
1. Expand **⚙️ Server Settings** in the sidebar and enter your endpoint URL, or
2. Copy `.env.example` to `.env` and configure:
   ```env
   OLLAMA_BASE_URL=http://localhost:11434
   DEFAULT_MODEL=qwen2.5-coder:7b
   ```

---

## Project Structure

```
├── app.py           # Streamlit interface & Minimal Neobrutalist design
├── analyzer.py      # Ollama API client & resilient JSON parsing
├── database.py      # SQLite storage & cross-session aggregation
├── prompts.py       # LLM system prompts & structured output schemas
├── requirements.txt # Minimal dependencies (streamlit, requests)
└── .env.example     # Environment variable defaults
```
