# Sovereign Agent Workbench (prototype)

A local AI agent that runs entirely on this Mac. The model is served by oMLX, and no data leaves the machine.

## Files
| File | What it does |
|---|---|
| `agent.py` | The agent loop: model → tool calls → results → model … until done. Also the terminal chat. |
| `tools.py` | All 12 tools: files, sandboxed Python, OCR/documents, vision, spreadsheets, Word/PowerPoint/Excel, knowledge-base search. |
| `kb.py` | Knowledge base: indexes `workspace/kb/` (with OCR) and searches it using BM25 keyword ranking. |
| `llm.py` | Connection to the local oMLX server (OpenAI-compatible API). |
| `test_smoke.py` | Checks every tool without the model running. |

## Run
```bash
omlx start                                   # start the local model server (port 8000)
export OMLX_API_KEY=...                      # "api_key" from ~/.omlx/settings.json
export MODEL=gemma-4-26B-A4B-it-QAT-MLX-4bit # or Qwen3.8-27B-4bit (see: curl localhost:8000/v1/models)
uv run agent.py                              # interactive chat
uv run agent.py "task..."                    # one task, then exit
uv run test_smoke.py                         # offline tool tests
```

## Use
- Put manuals, SOPs and correspondence in `workspace/kb/`. Then ask the agent to reindex the knowledge base, or delete `workspace/kb_index.json` so it rebuilds.
- Put input files (scans, drawings, photos, spreadsheets) anywhere in `workspace/`.
- Deliverables are written to `workspace/out/`.

## Adding a tool
Write a function in `tools.py` with type hints and a docstring, then add it to `TOOLS`. The schema the model sees is generated automatically.

## Known limits (prototype)
- The code sandbox uses macOS `sandbox-exec`, which blocks network access and writes outside the workspace. It is not a VM, so don't run hostile inputs.
- Knowledge-base search matches keywords, not meaning (no embeddings yet).
- No streaming output. A 26–27B model takes around 10–60 seconds per step on a MacBook Air.
