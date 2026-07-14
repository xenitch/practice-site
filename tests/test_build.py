from pathlib import Path, PurePosixPath
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from build import page_url, render_md, load_page, build


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


def make_site(tmp_path):
    (tmp_path / "content" / "research").mkdir(parents=True)
    (tmp_path / "templates").mkdir()
    (tmp_path / "static").mkdir()
    (tmp_path / "static" / "style.css").write_text("body{}", encoding="utf-8")
    (tmp_path / "templates" / "base.html").write_text(
        "<title>{{ page.meta.title }} — {{ site.name }}</title>{% block content %}{% endblock %}",
        encoding="utf-8")
    for name, extra in [("page.html", ""), ("article.html", ""),
                        ("research.html", "{% for a in articles %}<a href='{{ a.url }}'>{{ a.meta.title }}</a>{% endfor %}")]:
        (tmp_path / "templates" / name).write_text(
            "{% extends 'base.html' %}{% block content %}{{ page.content }}" + extra + "{% endblock %}",
            encoding="utf-8")
    c = tmp_path / "content"
    (c / "index.md").write_text("---\ntitle: Главная\n---\nПривет.", encoding="utf-8")
    (c / "research" / "index.md").write_text(
        "---\ntitle: Исследование\ntemplate: research.html\n---\nРамка.", encoding="utf-8")
    (c / "research" / "old.md").write_text(
        "---\ntitle: Старая\ndate: 2026-01-01\n---\nТекст.", encoding="utf-8")
    (c / "research" / "new.md").write_text(
        "---\ntitle: Новая\ndate: 2026-07-01\n---\nТекст.", encoding="utf-8")
    return tmp_path

def test_build_outputs(tmp_path):
    root = make_site(tmp_path)
    build(root)
    docs = root / "docs"
    assert (docs / "index.html").exists()
    assert (docs / "research" / "index.html").exists()
    assert (docs / "research" / "old" / "index.html").exists()
    assert (docs / "CNAME").read_text() == "xenitch.ru"
    assert (docs / ".nojekyll").exists()
    assert (docs / "static" / "style.css").exists()

def test_build_research_lists_articles_new_first(tmp_path):
    root = make_site(tmp_path)
    build(root)
    html = (root / "docs" / "research" / "index.html").read_text(encoding="utf-8")
    assert html.index("Новая") < html.index("Старая")
    assert "/research/new/" in html

def test_build_is_idempotent_and_cleans(tmp_path):
    root = make_site(tmp_path)
    build(root)
    (root / "docs" / "stale.html").write_text("x", encoding="utf-8")
    build(root)
    assert not (root / "docs" / "stale.html").exists()
