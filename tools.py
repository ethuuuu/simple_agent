"""
tools.py - every action the agent can take, as plain Python functions.

How it works:
  * Each tool is a normal function with type hints and a docstring.
  * `schema()` turns the function signature into the JSON "tool definition"
    the model needs, so adding a tool = writing one function and adding it
    to the TOOLS list at the bottom. No framework, no decorators.
  * Every path is resolved INSIDE the workspace folder (see `_safe`), so the
    model can never read or write files elsewhere on your Mac.

Tool groups:
  files        read_file, write_file, list_dir
  code         run_python                (offline, workspace-only sandbox)
  documents    read_document             (PDF / scans / images / docx -> text, with OCR)
  vision       look_at                   (ask the multimodal model about an image/drawing)
  spreadsheet  read_spreadsheet, make_xlsx
  deliverables make_docx, make_pptx
  knowledge    kb_search, kb_reindex     (see kb.py)
"""
import base64
import inspect
import io
import os
import subprocess
import sys
from pathlib import Path

import pymupdf as fitz  # PyMuPDF: opens PDFs and images, renders pages to pictures
import pandas as pd
import pytesseract  # wrapper around the on-device `tesseract` OCR engine
from docx import Document
from openpyxl import Workbook
from PIL import Image
from pptx import Presentation

import kb
import llm

# The ONLY folder tools may touch. Override with WORKSPACE=/some/dir.
WS = Path(os.getenv("WORKSPACE", Path(__file__).parent / "workspace")).resolve()
WS.mkdir(parents=True, exist_ok=True)

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".webp"}


def _safe(path: str) -> Path:
    """Resolve `path` relative to the workspace and refuse anything outside it
    (blocks tricks like '../../etc/passwd' or absolute paths)."""
    p = (WS / path).resolve()
    if not p.is_relative_to(WS):
        raise ValueError(f"path escapes workspace: {path}")
    return p


# ---------------------------------------------------------------- files

def read_file(path: str) -> str:
    """Read a UTF-8 text file from the workspace (code, markdown, csv, notes)."""
    return _safe(path).read_text(errors="replace")


def write_file(path: str, content: str) -> str:
    """Create or overwrite a text file in the workspace. Parent folders are created."""
    p = _safe(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"wrote {len(content)} chars to {path}"


def list_dir(path: str = ".") -> str:
    """List files and folders under a workspace directory (recursive, max 200 entries)."""
    root = _safe(path)
    items = sorted(str(p.relative_to(WS)) + ("/" if p.is_dir() else "") for p in root.rglob("*"))
    return "\n".join(items[:200]) or "(empty)"


# ---------------------------------------------------------------- code execution

# macOS built-in sandbox profile: allow everything EXCEPT network access and
# writing files outside the workspace / temp dirs. Keeps confidential data from
# being sent anywhere by generated code.
# shortcut: sandbox-exec is deprecated by Apple but still works; move to a
# container or VM before running untrusted inputs in production.
_SANDBOX = """(version 1)(allow default)(deny network*)
(deny file-write*)
(allow file-write* (subpath "{ws}") (subpath "/private/var/folders") (subpath "/private/tmp") (literal "/dev/null"))"""


def run_python(code: str, timeout: int = 60) -> str:
    """Run Python code in an offline sandbox with the workspace as the working
    directory. pandas, numpy, openpyxl, python-docx and python-pptx are available.
    Use print() to show results. Use this for every calculation."""
    cmd = [sys.executable, "-B", "-c", code]
    if sys.platform == "darwin":
        cmd = ["sandbox-exec", "-p", _SANDBOX.format(ws=WS)] + cmd
    try:
        r = subprocess.run(cmd, cwd=WS, capture_output=True, text=True, timeout=timeout,
                           env={"PATH": "/usr/bin:/bin", "HOME": str(WS), "MPLBACKEND": "Agg"})
    except subprocess.TimeoutExpired:
        return f"ERROR: timed out after {timeout}s"
    return f"exit={r.returncode}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"


# ---------------------------------------------------------------- documents + OCR

def _ocr(img: Image.Image) -> str:
    return pytesseract.image_to_string(img)


def _page_image(page, dpi=200) -> Image.Image:
    """Render one PDF page to a PIL image (for OCR or vision)."""
    pix = page.get_pixmap(dpi=dpi)
    return Image.open(io.BytesIO(pix.tobytes("png")))


def extract_text(p: Path) -> list[tuple[int, str]]:
    """Return [(page_number, text), ...] for any supported file.
    Digital PDFs use their embedded text; scanned pages (little/no text) are
    OCR'd with tesseract. Also used by kb.py to index the knowledge base."""
    ext = p.suffix.lower()
    if ext == ".pdf":
        out = []
        for i, page in enumerate(fitz.open(p), 1):
            text = page.get_text()
            if len(text.strip()) < 50:  # probably a scan -> OCR it
                text = _ocr(_page_image(page))
            out.append((i, text))
        return out
    if ext in IMAGE_EXT:
        return [(1, _ocr(Image.open(p)))]
    if ext == ".docx":
        return [(1, "\n".join(par.text for par in Document(p).paragraphs))]
    if ext in {".xlsx", ".xls", ".csv"}:
        return [(1, read_spreadsheet(str(p.relative_to(WS))))]
    return [(1, p.read_text(errors="replace"))]


def read_document(path: str) -> str:
    """Extract text from a PDF (digital or scanned), image, Word or text file
    using on-device OCR. For handwriting, drawings or photos where OCR is poor,
    use look_at instead."""
    return "\n\n".join(f"--- page {n} ---\n{t}" for n, t in extract_text(_safe(path)))


def look_at(path: str, question: str, page: int = 1) -> str:
    """Ask the vision model a question about an image or a PDF page: handwritten
    notes, engineering drawings, photographs, charts, stamps, signatures."""
    p = _safe(path)
    img = _page_image(fitz.open(p)[page - 1]) if p.suffix.lower() == ".pdf" else Image.open(p)
    img = img.convert("RGB")
    img.thumbnail((1536, 1536))  # downscale: keeps memory + prompt size sane on 32GB
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=90)
    b64 = base64.b64encode(buf.getvalue()).decode()
    # A separate one-shot model call with the image attached, OpenAI image format.
    msg = llm.chat([{"role": "user", "content": [
        {"type": "text", "text": question + "\nTranscribe exactly what you see; say 'unclear' rather than guess."},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
    ]}])
    return msg.content or ""


# ---------------------------------------------------------------- spreadsheets

def read_spreadsheet(path: str, sheet: str = "", max_rows: int = 100) -> str:
    """Show the contents of an .xlsx/.xls/.csv file as a text table (every sheet
    unless `sheet` is given). For analysis, load it with pandas in run_python."""
    p = _safe(path)
    if p.suffix.lower() == ".csv":
        frames = {"csv": pd.read_csv(p)}
    else:
        frames = pd.read_excel(p, sheet_name=sheet or None)  # None = all sheets
        if sheet:
            frames = {sheet: frames}
    return "\n\n".join(f"## sheet: {name} ({len(df)} rows)\n{df.head(max_rows).to_string()}"
                       for name, df in frames.items())


def make_xlsx(path: str, sheets: dict) -> str:
    """Create an Excel file. `sheets` maps sheet name -> list of rows, each row a
    list of cell values. Strings starting with '=' become live Excel formulas,
    e.g. {"Calc": [["Load kN", "Factor", "Design"], [12.5, 1.5, "=A2*B2"]]}."""
    wb = Workbook()
    wb.remove(wb.active)
    for name, rows in sheets.items():
        ws = wb.create_sheet(str(name)[:31])  # Excel's 31-char sheet name limit
        for row in rows:
            ws.append(row)
    p = _safe(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    wb.save(p)
    return f"saved {path}"


# ---------------------------------------------------------------- deliverables

def make_docx(path: str, title: str, body: str) -> str:
    """Create a Word document (reports, approval notes, memos). `body` uses simple
    markdown: '# ' / '## ' headings, '- ' bullets, '| a | b |' table rows,
    blank-line separated paragraphs."""
    doc = Document()
    doc.add_heading(title, 0)
    table_rows = []

    def flush_table():  # turn collected '| a | b |' lines into a real Word table
        rows = [r for r in table_rows if not set(r.replace("|", "").strip()) <= set("-: ")]
        if rows:
            cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
            t = doc.add_table(rows=len(cells), cols=max(map(len, cells)), style="Table Grid")
            for i, row in enumerate(cells):
                for j, val in enumerate(row):
                    t.cell(i, j).text = val
        table_rows.clear()

    for line in body.splitlines():
        s = line.strip().replace("**", "")  # models love **bold**; Word would show the asterisks
        if s.startswith("|"):
            table_rows.append(s)
            continue
        flush_table()
        if s.startswith("## "):
            doc.add_heading(s[3:], 2)
        elif s.startswith("# "):
            doc.add_heading(s[2:], 1)
        elif s.startswith(("- ", "* ")):
            doc.add_paragraph(s[2:], style="List Bullet")
        elif s:
            doc.add_paragraph(s)
    flush_table()
    p = _safe(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    doc.save(p)
    return f"saved {path}"


def make_pptx(path: str, title: str, slides: list) -> str:
    """Create a PowerPoint deck. `slides` is a list of {"title": str, "bullets": [str, ...]}."""
    prs = Presentation()
    s = prs.slides.add_slide(prs.slide_layouts[0])  # title slide
    s.shapes.title.text = title
    for sl in slides:
        s = prs.slides.add_slide(prs.slide_layouts[1])  # "title and content" layout
        s.shapes.title.text = sl.get("title", "")
        s.placeholders[1].text_frame.text = "\n".join(sl.get("bullets", []))
    p = _safe(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    prs.save(p)
    return f"saved {path}"


# ---------------------------------------------------------------- knowledge base

def kb_search(query: str, k: int = 5) -> str:
    """Search the organisation's manuals, SOPs and past correspondence (files in
    workspace/kb/). Returns the best matching passages with [file p.N] citations.
    Always cite these sources in your answer."""
    return kb.search(query, k)


def kb_reindex() -> str:
    """Rebuild the knowledge-base index after files were added to workspace/kb/."""
    return kb.build()


# ---------------------------------------------------------------- registry

TOOLS = [read_file, write_file, list_dir, run_python, read_document, look_at,
         read_spreadsheet, make_xlsx, make_docx, make_pptx, kb_search, kb_reindex]
BY_NAME = {f.__name__: f for f in TOOLS}
_JSON_TYPES = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "object"}


def schema(fn) -> dict:
    """Build the OpenAI tool definition from a function's signature + docstring."""
    props, required = {}, []
    for name, prm in inspect.signature(fn).parameters.items():
        props[name] = {"type": _JSON_TYPES.get(prm.annotation, "string")}
        if prm.default is inspect.Parameter.empty:
            required.append(name)
    return {"type": "function", "function": {
        "name": fn.__name__,
        "description": inspect.getdoc(fn),
        "parameters": {"type": "object", "properties": props, "required": required},
    }}


SCHEMAS = [schema(f) for f in TOOLS]
