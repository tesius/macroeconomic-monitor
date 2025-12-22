<!-- .github/copilot-instructions.md -->
# Copilot / AI Agent Instructions — market_rader

Purpose: give an AI coding agent the minimal, actionable context to be productive quickly in this repo.

- Project type: single-page Streamlit app. Entrypoint: `main.py`.
- Runtime: Python >= 3.13 (see `pyproject.toml`). Key deps: `streamlit`, `pandas`, `plotly`.

Quick start (what human devs run):
- Run locally: `streamlit run main.py` (the app uses Streamlit layout primitives).
- Use a Python 3.13 venv. Dependencies are listed in `pyproject.toml`.

Big-picture architecture & intent
- This is a lightweight dashboard (macro/market monitor) implemented in a single module: `main.py`.
- UI is organized into three conceptual sections: "Market Pulse (Daily)", "Macro Health (Monthly)", and "AI Analysis".
- Data flow: currently the app uses placeholder/random data in `main.py` (see `chart_data = pd.DataFrame(np.random.randn(90, 2)...)`). Real data sources are expected to be swapped in (yfinance, FRED, internal CSVs, or LLM APIs).

Key patterns and conventions (copy these examples)
- Page config and wide layout: `st.set_page_config(layout="wide", page_title="...")` — preserve this when changing layout.
- Four-metric row using columns: `col1, col2, col3, col4 = st.columns(4)` and `st.metric(...)` for top-level KPIs.
- Sectioning: use `st.markdown('---')` between major sections.
- Tabs: `tab1, tab2 = st.tabs(["...","..."])` for alternate views inside a section.
- AI integration point: the "Generate AI Report" button contains an LLM stub — keep the UX pattern (button -> spinner -> results) when wiring a real LLM.

Integration points and where to edit
- Replace placeholders in `main.py`:
  - Market metrics: the top metrics are generated inline; replace with calls to data fetchers (yfinance or CSV loader).
  - `chart_data = pd.DataFrame(np.random.randn(...))` is an explicit placeholder for time series.
  - AI analysis: the button handler contains a comment about calling an LLM (Gemini). Add a small service module (e.g., `services/llm.py`) if implementing API calls.
- Secrets/config: create a `.env` or `config.py` (not present yet). Do not hardcode API keys in `main.py`.

Developer workflows and commands
- Start app: `streamlit run main.py` (runs on default 8501). Use `--server.port` to change port.
- Debugging: run with `streamlit run main.py --logger.level=debug` and watch console logs.
- Packaging: dependencies are declared in `pyproject.toml`; prefer using an editable install or pinned requirements for deployments.

Project-specific notes for agents
- Keep changes minimal and localized: the repo is intentionally simple; prefer adding small modules (`services/*`, `data/*`) rather than expanding `main.py` excessively.
- Follow the file-level style: inline comments in Korean are present in `main.py` — preserve or mirror locale if adding UI text.
- No tests exist; if you add tests, keep them small and use pytest (add `pyproject` test config if needed).

Files to inspect first
- `main.py` — primary app and UI layout (most behaviors live here).
- `pyproject.toml` — runtime and dependency hints.
- `README.md` — currently empty; update only after features are stabilized.

When making PRs
- Explain why the change improves data sourcing, UX, or reliability (e.g., "replace placeholder chart_data with yfinance fetch for US 10Y series").
- Include a short manual test plan: how to run the streamlit app and what to look for (e.g., metrics show non-random values, AI report appears).

Questions to ask the human before risky changes
- Preferred external data sources and API keys handling (yfinance vs paid APIs; where to store secrets).
- Whether to break `main.py` into modules now or after initial feature work.

If anything here is unclear or you want the new file to follow a different tone/length, tell me which sections to change and I will update it.
