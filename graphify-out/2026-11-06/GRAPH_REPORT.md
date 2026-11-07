# Graph Report - simple_agent  (2026-11-06)

## Corpus Check
- 15 files · ~4,774 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 20 file(s) not represented in the graph (top: .pyc 16, (none) 3, .lock 1)

## Summary
- 113 nodes · 175 edges · 9 communities (5 shown, 4 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 27 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- record.py
- Agent Loop
- Knowledge Base Search
- File & Office Tools
- tools.py
- Sandbox & Torque Workflow
- Graphify Integration
- Project Package
- convert_flow

## God Nodes (most connected - your core abstractions)
1. `_safe()` - 14 edges
2. `extract_text()` - 10 edges
3. `build()` - 8 edges
4. `search()` - 8 edges
5. `look_at()` - 8 edges
6. `run()` - 6 edges
7. `run_python()` - 6 edges
8. `_page_image()` - 6 edges
9. `M20 Torque Approval Task Plan` - 6 edges
10. `run_tool()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `M20 Torque Approval Task Plan` --references--> `kb_search()`  [INFERRED]
  workspace/plan.md → tools.py
- `M20 Torque Approval Task Plan` --references--> `run_python()`  [INFERRED]
  workspace/plan.md → tools.py
- `What this is` --references--> `run_tool()`  [INFERRED]
  AGENTS.md → agent.py
- `workspace/kb_index.json (KB index cache)` --shares_data_with--> `build()`  [INFERRED]
  README.md → kb.py
- `oMLX Local Model Server (OpenAI-compatible)` --references--> `chat()`  [INFERRED]
  README.md → llm.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Knowledge-Base Indexing and Retrieval** — readme_bm25_kb_search, readme_kb_index_json, kb_build, kb_search, tools_kb_search [INFERRED 0.85]
- **SOP-17 Torque Approval Workflow** — workspace_plan_torque_task_plan, tools_kb_search, workspace_kb_sop_17_flange_bolting, workspace_kb_sop_17_star_pattern_passes, workspace_plan_torque_note_docx [INFERRED 0.85]

## Communities (9 total, 4 thin omitted)

### Community 1 - "Agent Loop"
Cohesion: 0.14
Nodes (8): main(), run(), run_tool(), chat(), oMLX Local Model Server (OpenAI-compatible), Sovereign Agent Workbench, test_smoke.py offline tool tests, 12 Agent Tools (files, sandboxed Python, OCR, vision, spreadsheets, Office, KB search)

### Community 2 - "Knowledge Base Search"
Cohesion: 0.18
Nodes (7): build(), _paths(), search(), _tokens(), workspace/kb_index.json (KB index cache), kb_reindex(), kb_search()

### Community 3 - "File & Office Tools"
Cohesion: 0.10
Nodes (11): Commands, Rules, Testing the harness (eval data collection), What this is, list_dir(), make_docx(), make_pptx(), make_xlsx() (+3 more)

### Community 4 - "tools.py"
Cohesion: 0.12
Nodes (7): extract_text(), look_at(), _ocr(), _page_image(), read_document(), read_spreadsheet(), schema()

### Community 5 - "Sandbox & Torque Workflow"
Cohesion: 0.28
Nodes (6): run_python(), SOP-17 Flange Bolting, M20 Flange Bolt Torque 210 Nm, Star Pattern Tightening in 3 Passes (30%/70%/100%), out/torque_note.docx Approval Note, M20 Torque Approval Task Plan

## Knowledge Gaps
- **5 isolated node(s):** `simple-agent`, `test_smoke.py offline tool tests`, `out/torque_note.docx Approval Note`, `graphify Knowledge Graph (graphify-out/)`, `graphify Usage Rules (CLAUDE.md)`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 46 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_safe()` connect `File & Office Tools` to `tools.py`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `_safe()` (e.g. with `Rules` and `What this is`) actually correct?**
  _`_safe()` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `simple-agent`, `test_smoke.py offline tool tests`, `out/torque_note.docx Approval Note` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Agent Loop` be split into smaller, more focused modules?**
  _Cohesion score 0.13725490196078433 - nodes in this community are weakly interconnected._
- **Why does `run_python()` connect `Sandbox & Torque Workflow` to `File & Office Tools`, `tools.py`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Should `File & Office Tools` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Should `tools.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._