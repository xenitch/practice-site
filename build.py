#!/usr/bin/env python3
"""Сборка сайта «Сообщества совместной практики»: content/ + templates/ -> docs/."""
from pathlib import Path, PurePosixPath
import shutil

import frontmatter
import markdown
from jinja2 import Environment, FileSystemLoader

SITE = {
    "name": "Сообщества совместной практики",
    "domain": "xenitch.ru",
    "author": "Ксения Костюченко",
    "telegram": "https://t.me/xenitch",
    "description": "Живые группы совместной практики и исследование того, почему практика повторяется.",
}


def page_url(rel: PurePosixPath) -> str:
    parts = rel.parent.parts if rel.name == "index.md" else rel.parent.parts + (rel.stem,)
    return "/" + "/".join(parts) + "/" if parts else "/"


def render_md(text: str) -> str:
    return markdown.markdown(text, extensions=["extra"])


def load_page(path: Path, content_dir: Path) -> dict:
    post = frontmatter.load(path)
    rel = PurePosixPath(path.relative_to(content_dir).as_posix())
    url = page_url(rel)
    return {
        "url": url,
        "meta": post.metadata,
        "content": render_md(post.content),
        "is_article": url.startswith("/research/") and url != "/research/",
    }


def build(root: Path) -> None:
    content_dir, out = root / "content", root / "docs"
    env = Environment(loader=FileSystemLoader(root / "templates"), autoescape=False)
    pages = [load_page(p, content_dir) for p in sorted(content_dir.rglob("*.md"))]
    articles = sorted((p for p in pages if p["is_article"]),
                      key=lambda p: str(p["meta"].get("date", "")), reverse=True)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(root / "static", out / "static")
    (out / "CNAME").write_text(SITE["domain"], encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    for page in pages:
        tpl = page["meta"].get("template") or ("article.html" if page["is_article"] else "page.html")
        html = env.get_template(tpl).render(site=SITE, page=page, articles=articles)
        dest = out / page["url"].strip("/") / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")


if __name__ == "__main__":
    build(Path(__file__).parent)
    print("Собрано в docs/")
