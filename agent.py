"""
agent.py - the agent loop + a simple terminal chat.

The whole "agentic" idea in a nutshell:
    1. send the conversation + list of tools to the model
    2. if the model asks to call tools -> run them, append the results, go to 1
    3. if the model replies with plain text -> that's the answer for this turn
This lets the model plan, act, look at results, fix mistakes and keep going
until the task is actually done, instead of answering once and stopping.

Run:   uv run agent.py                 (interactive)
       uv run agent.py "your task"     (one task, then exit)
"""
import json
import sys
from datetime import date

import llm
import tools

MAX_STEPS = 30          # safety cap on tool calls per task
MAX_TOOL_OUTPUT = 8000  # characters; long outputs are cut to protect the context window

SYSTEM = f"""You are a careful engineering assistant running fully offline on a
confidential workstation. Today is {date.today()}. All files live in the workspace;
use relative paths. Write deliverables to out/.

How to work:
1. For any multi-step task, first write a short numbered plan to plan.md (write_file).
2. Execute it step by step with tools. After each step check the result; if
   something failed, fix it and retry. Update plan.md as steps complete.
3. Ground answers in the organisation's documents: use kb_search and cite the
   sources as [file p.N]. If the knowledge base has no answer, say so.
4. Never do arithmetic in your head. Use run_python, and show the formula,
   inputs, units and intermediate steps in the deliverable.
5. For scanned PDFs use read_document; for handwriting, drawings and photos use
   look_at. Flag anything unclear instead of guessing.
6. Produce real files (make_docx / make_pptx / make_xlsx / write_file) when
   asked for a report, approval note, deck, spreadsheet or code, then verify
   them (e.g. read_spreadsheet or read_document on the output).
7. Finish with a brief summary: what you did, files created, open issues."""


def run_tool(call) -> str:
    """Execute one tool call from the model; errors go back to the model as text
    so it can see what went wrong and correct itself."""
    try:
        fn = tools.BY_NAME[call.function.name]
        args = json.loads(call.function.arguments or "{}")
        return str(fn(**args))[:MAX_TOOL_OUTPUT]
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def run(messages: list) -> str:
    """Keep calling the model + tools until it gives a final text answer."""
    for _ in range(MAX_STEPS):
        msg = llm.chat(messages, tools.SCHEMAS)
        messages.append(msg.model_dump(exclude_none=True))  # keep the assistant turn in history
        if not msg.tool_calls:
            return msg.content or ""
        for call in msg.tool_calls:
            print(f"  -> {call.function.name}({call.function.arguments[:150]})", flush=True)
            result = run_tool(call)
            print(f"     {result[:200]!r}", flush=True)
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})
    return f"(stopped after {MAX_STEPS} steps - say 'continue' to keep going)"


def main():
    messages = [{"role": "system", "content": SYSTEM}]
    task = " ".join(sys.argv[1:])
    if task:  # one-shot mode
        messages.append({"role": "user", "content": task})
        print(run(messages))
        return
    print(f"Workbench ready (model: {llm.MODEL}, workspace: {tools.WS}). Ctrl-D to quit.")
    while True:
        try:
            user = input("\nyou> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if user:
            messages.append({"role": "user", "content": user})
            print("\nagent>", run(messages))


if __name__ == "__main__":
    main()
