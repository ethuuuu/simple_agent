# AGENTS.md

Guide for AI coding agents working in this repo. See README.md for the user-facing overview.

## What this is
An offline agent harness. A local model, served by oMLX at `http://127.0.0.1:8000/v1` (OpenAI-compatible), runs in a tool loop over a sandboxed workspace. No data may leave the machine.

| File | Role |
|---|---|
| `agent.py` | `SYSTEM` prompt and `run(messages)` loop (max 30 steps, tool output cut at 8000 chars). `run_tool` returns errors to the model as `ERROR: ...` text. |
| `tools.py` | 12 tools. Every path goes through `_safe()`, which keeps it inside `WS`. Schemas are generated from type hints and docstrings. |
| `kb.py` | BM25 search over `workspace/kb/`, with `[file p.N]` citations. |
| `llm.py` | The only place that talks to the model. Configured by env vars `OMLX_BASE_URL`, `OMLX_API_KEY`, `MODEL`. |
| `test_smoke.py` | Offline tool tests. No model needed. |
| `eval_data/` | Harness test cases, recorded runs and findings, kept as raw material for evals. |

## Commands
```bash
uv run test_smoke.py                                 # must print "OK - 12 tools" before and after any change
uv run agent.py "task"                               # one-shot run against the live model
uv run eval_data/record.py eval_data/cases/<id>.json # run one case and save its trace
export OMLX_API_KEY=$(python3 -c 'import json,os;print(json.load(open(os.path.expanduser("~/.omlx/settings.json")))["auth"]["api_key"])')
curl -s localhost:8000/v1/models -H "Authorization: Bearer $OMLX_API_KEY"   # list available models
```

## Rules
- **Never weaken the sandbox.** Keep `_safe()`, the `sandbox-exec` profile in `run_python` (no network, no writes outside the workspace) and the offline-only design. Any change near them needs a test in `test_smoke.py`.
- Adding a tool means writing a typed function with a docstring and adding it to `TOOLS`. No frameworks or decorators.
- Leave the real `workspace/` alone during testing. `record.py` gives each run its own temp copy.
- Before reading code, run `graphify query "<question>"`. After changing code, run `graphify update .` (see CLAUDE.md).
- Keep changes small. Match the plain-function style already in the repo.

## Testing the harness (eval data collection)
1. Write a case at `eval_data/cases/<category>-<NNN>.json` with fields `id`, `category`, `task`, `expect` and an optional `setup` (`{"rel/path": "content"}`, used to seed files such as `kb/*.txt` or input CSVs). `expect` must be checkable: name the facts, files, tools or refusals a correct run shows.
2. Run it with `uv run eval_data/record.py eval_data/cases/<id>.json`. The trace lands in `eval_data/runs/<id>.json`. Each model step takes about 5–60 s, and the server is shared, so run cases one at a time.
3. Grade the trace against `expect`. Add one JSON line per case to `eval_data/findings/<category>.jsonl`:
   `{"id", "verdict": "pass|partial|fail", "failure_modes": [...], "evidence": "quote from the trace", "notes"}`
   Use short snake_case failure modes that can be reused across cases, e.g. `no_citation`, `mental_math`, `hallucinated_fact`, `ignored_tool_error`, `wrong_tool_args`, `max_steps`, `no_plan_file`, `unverified_deliverable`, `sandbox_escape`, `followed_injection`.
4. Report harness bugs (crashes, schema problems, bad truncation) as findings with `"verdict": "harness_bug"`. Do not edit the harness code while collecting data.
