"""
test_smoke.py - checks every tool WITHOUT needing the model running.
Run:  uv run test_smoke.py      (prints OK at the end)
"""
import os
import tempfile

os.environ["WORKSPACE"] = tempfile.mkdtemp()  # isolated scratch workspace
import tools  # noqa: E402  (must import after WORKSPACE is set)

# 1. paths cannot escape the workspace
for bad in ["../x", "/etc/passwd"]:
    try:
        tools.read_file(bad)
        raise AssertionError("escape allowed: " + bad)
    except ValueError:
        pass

# 2. file round trip
tools.write_file("a/b.txt", "hello")
assert tools.read_file("a/b.txt") == "hello"
assert "a/b.txt" in tools.list_dir()

# 3. sandboxed python: runs, times out, no network, can't write outside workspace
assert "4" in tools.run_python("print(2+2)")
assert "timed out" in tools.run_python("while True: pass", timeout=2)
assert "exit=0" not in tools.run_python("import urllib.request; urllib.request.urlopen('http://example.com', timeout=3)")
assert "exit=0" not in tools.run_python("open('/Users/Shared/should_not_exist.txt','w')")
assert "exit=0" in tools.run_python("open('inside.txt','w').write('ok')")

# 4. deliverables open again
tools.make_xlsx("out/c.xlsx", {"Calc": [["a", "b", "sum"], [1, 2, "=A2+B2"]]})
assert "sum" in tools.read_spreadsheet("out/c.xlsx")
tools.make_docx("out/n.docx", "Approval Note", "# Scope\n- item\n\n| k | v |\n|---|---|\n| x | 1 |")
assert "Scope" in tools.read_document("out/n.docx")
tools.make_pptx("out/d.pptx", "Deck", [{"title": "S1", "bullets": ["a", "b"]}])
assert os.path.getsize(tools._safe("out/d.pptx")) > 0

# 5. knowledge base: index + cited search
tools.write_file("kb/sop-17.txt", "SOP-17: Torque flange bolts M20 to 210 Nm in a star pattern.")
assert "indexed" in tools.kb_reindex()
hit = tools.kb_search("flange bolt torque")
assert "sop-17.txt p.1" in hit and "210 Nm" in hit

# 6. OCR on a rendered image
from PIL import Image, ImageDraw  # noqa: E402
img = Image.new("RGB", (600, 120), "white")
ImageDraw.Draw(img).text((10, 40), "PRESSURE 12 BAR", fill="black", font_size=40)
img.save(tools._safe("scan.png"))
assert "PRESSURE" in tools.read_document("scan.png").upper()

# 7. every tool has a valid schema
assert all(s["function"]["description"] for s in tools.SCHEMAS)
print("OK -", len(tools.SCHEMAS), "tools")
