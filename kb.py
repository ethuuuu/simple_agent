"""
kb.py - local knowledge base over the organisation's own documents.

Drop manuals, SOPs, past correspondence (PDF, scans, docx, txt, md, xlsx...)
into workspace/kb/ and call build(). Each file is turned into text (with OCR
for scans, via tools.extract_text), cut into ~800-character chunks, and saved
to workspace/kb_index.json together with its file name + page number.

Search uses BM25 keyword ranking: fully offline, no embedding model needed,
and very good at the exact part numbers / clause ids / jargon industrial
documents are full of.
# shortcut: keyword search only; add embeddings (an omlx embedding model)
# for synonym/paraphrase matching once the KB grows past a few thousand pages.
"""
import json
import re

from rank_bm25 import BM25Okapi

CHUNK = 800  # characters per chunk: small enough to fit several in the prompt


def _paths():
    from tools import WS  # imported lazily: tools.py imports this module
    return WS / "kb", WS / "kb_index.json"


def _tokens(text):
    return re.findall(r"\w+", text.lower())


def build() -> str:
    """(Re)index every file under workspace/kb/."""
    from tools import extract_text
    kb_dir, index_file = _paths()
    kb_dir.mkdir(exist_ok=True)
    chunks, errors = [], []
    for f in sorted(p for p in kb_dir.rglob("*") if p.is_file() and not p.name.startswith(".")):
        try:
            for page, text in extract_text(f):
                for i in range(0, len(text), CHUNK - 100):  # 100-char overlap so sentences aren't lost at edges
                    piece = text[i:i + CHUNK].strip()
                    if piece:
                        chunks.append({"file": str(f.relative_to(kb_dir)), "page": page, "text": piece})
        except Exception as e:  # one bad file must not kill the whole index
            errors.append(f"{f.name}: {e}")
    index_file.write_text(json.dumps(chunks))
    return f"indexed {len(chunks)} chunks" + (f"; failed: {errors}" if errors else "")


def search(query: str, k: int = 5) -> str:
    """Return the top-k chunks for `query`, each tagged with its source."""
    _, index_file = _paths()
    if not index_file.exists():
        build()
    chunks = json.loads(index_file.read_text())
    if not chunks:
        return "knowledge base is empty - add files to workspace/kb/ and run kb_reindex"
    docs = [_tokens(c["text"]) for c in chunks]
    q = _tokens(query)
    scores = BM25Okapi(docs).get_scores(q)
    best = sorted(range(len(chunks)), key=lambda i: scores[i], reverse=True)[:k]
    # keep only chunks sharing at least one word with the query (BM25 scores can
    # go negative on tiny corpora, so a "score > 0" test would drop real hits)
    return "\n\n".join(f"[{chunks[i]['file']} p.{chunks[i]['page']}]\n{chunks[i]['text']}"
                       for i in best if set(q) & set(docs[i])) or "no matches"
