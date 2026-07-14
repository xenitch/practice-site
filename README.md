# xenitch.ru — Сообщества совместной практики

Статический сайт. Сборка: `python build.py` (venv: `.venv`), результат в `docs/`,
его раздаёт GitHub Pages (ветка `main`, папка `/docs`). Публикация = commit + push.

## Как добавить статью

1. Положить `content/research/{slug}.md` с frontmatter:
   `title`, `subtitle` (опционально), `date` (ГГГГ-ММ-ДД), `description`.
2. `.venv/bin/python build.py && .venv/bin/pytest tests/ -q`
3. Проверить локально: `cd docs && python3 -m http.server 8899`
4. `git add -A && git commit && git push` — сайт обновится за ~1 мин.

Через Claude Code: «добавь статью X на сайт» — все шаги выполняются автоматически.

## Восстановление окружения с нуля

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python build.py
```
