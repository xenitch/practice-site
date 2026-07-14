#!/usr/bin/env python3
"""Сборка сайта «Сообщества совместной практики»: content/ + templates/ -> docs/."""
from pathlib import Path, PurePosixPath

import frontmatter
import markdown

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
