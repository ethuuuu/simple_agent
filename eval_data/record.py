"""
record.py - run ONE test case through the real agent loop and save a full trace.

    uv run eval_data/record.py eval_data/cases/<id>.json

Case file (JSON):
    {"id": "kb-001", "category": "kb", "task": "prompt sent to the agent",
     "setup": {"kb/extra.txt": "file content", ...},   # optional seed files
     "expect": "what a correct run looks like (for graders)"}

Each run gets a fresh temp workspace (a copy of workspace/kb + the setup files),
so cases never touch the real workspace or each other.
Writes eval_data/runs/<id>.json: messages, every tool call with timing, model
latency per step, final answer, stop reason, and the files the agent produced.
"""
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
case = json.loads(Path(sys.argv[1]).read_text())
ws = Path(tempfile.mkdtemp(prefix=f"eval-{case['id']}-"))
shutil.copytree(ROOT / "workspace" / "kb", ws / "kb")
for rel, content in case.get("setup", {}).items():
    (ws / rel).parent.mkdir(parents=True, exist_ok=True)
    (ws / rel).write_text(content)
before = set(ws.rglob("*"))
os.environ["WORKSPACE"] = str(ws)  # must be set before tools is imported
sys.path.insert(0, str(ROOT))
import agent  # noqa: E402
import llm  # noqa: E402

steps, calls = [], []
_chat, _run_tool = llm.chat, agent.run_tool


def timed_chat(messages, tools=None):
    t = time.time()
    msg = _chat(messages, tools)
    steps.append({"latency_s": round(time.time() - t, 2), "n_tool_calls": len(msg.tool_calls or [])})
    return msg


def is_error(out: str) -> bool:
    # run_tool errors start with ERROR; run_python failures start with exit=<non-zero>
    return out.startswith("ERROR") or (out.startswith("exit=") and not out.startswith("exit=0\n"))


def logged_tool(call):
    t = time.time()
    out = _run_tool(call)
    calls.append({"step": len(steps), "name": call.function.name, "args": call.function.arguments,
                  "result": out[:2000], "error": is_error(out),
                  "latency_s": round(time.time() - t, 2)})
    return out


llm.chat, agent.run_tool = timed_chat, logged_tool
messages = [{"role": "system", "content": agent.SYSTEM}, {"role": "user", "content": case["task"]}]
t0, crash = time.time(), None
try:
    answer = agent.run(messages)
except Exception as e:  # record harness crashes instead of losing the run
    answer, crash = "", f"{type(e).__name__}: {e}"

produced = {}
for p in sorted(set(ws.rglob("*")) - before):
    if p.is_file() and p.name != "kb_index.json":
        rel = str(p.relative_to(ws))
        produced[rel] = (p.read_text(errors="replace")[:3000] if p.suffix in {".txt", ".md", ".py", ".csv", ".json"}
                         else f"<binary {p.stat().st_size} bytes>")

out = {
    "case": case, "model": llm.MODEL, "started": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(t0)),
    "wall_s": round(time.time() - t0, 1), "crash": crash,
    "stop_reason": ("crash" if crash else "max_steps" if answer.startswith("(stopped after")
                    else "empty_answer" if not answer.strip() else "final_answer"),
    "n_steps": len(steps), "n_tool_calls": len(calls), "n_tool_errors": sum(c["error"] for c in calls),
    "final_answer": answer, "steps": steps, "tool_calls": calls, "files_produced": produced,
    "messages": messages, "workspace": str(ws),
}
dest = ROOT / "eval_data" / "runs" / f"{case['id']}.json"
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(out, indent=1, default=str))
print(f"{case['id']}: {out['stop_reason']} steps={out['n_steps']} tools={out['n_tool_calls']} "
      f"errors={out['n_tool_errors']} wall={out['wall_s']}s -> {dest.relative_to(ROOT)}")
