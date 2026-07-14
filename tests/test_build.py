from pathlib import Path, PurePosixPath
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from build import page_url, render_md, load_page


def test_page_url_root_index():
    assert page_url(PurePosixPath("index.md")) == "/"

def test_page_url_section_index():
    assert page_url(PurePosixPath("research/index.md")) == "/research/"

def test_page_url_article():
    assert page_url(PurePosixPath("research/inklings.md")) == "/research/inklings/"

def test_render_md_paragraph_and_table():
    html = render_md("Привет — «мир»\n\n| а | б |\n|---|---|\n| 1 | 2 |")
    assert "<p>" in html and "<table>" in html

def test_load_page(tmp_path):
    (tmp_path / "research").mkdir(parents=True)
    f = tmp_path / "research" / "test.md"
    f.write_text("---\ntitle: Тест\ndate: 2026-07-14\n---\nТело.", encoding="utf-8")
    page = load_page(f, tmp_path)
    assert page["url"] == "/research/test/"
    assert page["meta"]["title"] == "Тест"
    assert "<p>Тело.</p>" in page["content"]
    assert page["is_article"] is True

def test_load_page_index_not_article(tmp_path):
    f = tmp_path / "index.md"
    f.write_text("---\ntitle: Главная\n---\nТекст.", encoding="utf-8")
    page = load_page(f, tmp_path)
    assert page["is_article"] is False
