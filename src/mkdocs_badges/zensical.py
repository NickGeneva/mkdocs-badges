"""Native Zensical integration implemented as a Python Markdown extension."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from markdown import Extension, Markdown
from markdown.postprocessors import Postprocessor
from markdown.preprocessors import Preprocessor
from mkdocs.structure.files import File
from mkdocs.utils.meta import get_data
from zensical.extensions.context import ContextPreprocessor

from .plugin import (
    _FILTER_END_RE,
    _FILTER_START_RE,
    _contains_equivalent_badges_shortcode,
    _first_sentence,
    _insert_after_title,
    _normalise_badges,
    _page_record,
    _replace_markup,
    _runtime_payload,
    _write_catalog_json,
)
from .render import DEFAULT_COLOR, badges_html, filter_html, parse_options

log = logging.getLogger("zensical.extensions.mkdocs_badges")

_CATALOG_CACHE: dict[tuple[Any, ...], dict[str, dict[str, Any]]] = {}
_EMBEDDED_RUNTIME_RE = re.compile(
    r"<script data-mkdocs-badges-(?:bootstrap|runtime)>.*?</script>", re.DOTALL
)
_PAGE_RUNTIME_MARKER = "<!-- mkdocs-badges:page-runtime -->"


def _project_path(config: dict[str, Any], key: str, fallback: str) -> Path:
    path = Path(str(config.get(key, fallback)))
    if path.is_absolute():
        return path
    return Path(str(config.get("root_dir", Path.cwd()))) / path


def _catalog(context: ContextPreprocessor) -> dict[str, dict[str, Any]]:
    config = context.config
    docs_dir = _project_path(config, "docs_dir", "docs")
    site_dir = _project_path(config, "site_dir", "site")
    use_directory_urls = bool(config.get("use_directory_urls", True))
    sources = sorted(docs_dir.rglob("*.md"))
    fingerprint = tuple(
        (path.relative_to(docs_dir).as_posix(), path.stat().st_mtime_ns, path.stat().st_size)
        for path in sources
    )
    key = (str(docs_dir.resolve()), str(site_dir.resolve()), use_directory_urls, fingerprint)
    if key in _CATALOG_CACHE:
        return _CATALOG_CACHE[key]

    pages: dict[str, dict[str, Any]] = {}
    for path in sources:
        src_uri = path.relative_to(docs_dir).as_posix()
        body, metadata = get_data(path.read_text(encoding="utf-8"))
        file = File(src_uri, str(docs_dir), str(site_dir), use_directory_urls)
        pages[src_uri] = _page_record(file, body, metadata)
        pages[src_uri]["_source"] = body
    _CATALOG_CACHE.clear()
    _CATALOG_CACHE[key] = pages
    return pages


class BadgesPreprocessor(Preprocessor):
    """Expand badge syntax before Python Markdown renders the page."""

    def __init__(self, md: Markdown, extension: ZensicalBadgesExtension):
        super().__init__(md)
        self.extension = extension

    def run(self, lines: list[str]) -> list[str]:
        context = ContextPreprocessor.from_markdown(self.md)
        if context is None:
            return lines

        markdown = "\n".join(lines)
        options = self.extension.options(context)
        pages = _catalog(context)
        page = context.page
        src_uri = str(page.path).replace("\\", "/").lstrip("./")
        expected_source = str(pages.get(src_uri, {}).get("_source", ""))
        is_top_level = bool(expected_source) and markdown.strip() == expected_source.strip()
        badge_ids = _normalise_badges(page.meta.get("badges", []))
        if src_uri in pages:
            pages[src_uri].update(
                {
                    "title": str(page.meta.get("title") or pages[src_uri]["title"]),
                    "summary": _first_sentence(
                        page.meta.get("summary")
                        or page.meta.get("description")
                        or pages[src_uri]["summary"]
                    ),
                    "badges": badge_ids,
                    "url": page.url,
                }
            )

        has_equivalent = _contains_equivalent_badges_shortcode(markdown, badge_ids)
        markdown = _replace_markup(
            markdown,
            src_uri,
            pages,
            options["definitions"],
            options["default_color"],
            options["style"],
            source_links=True,
            autosummary_root=options["autosummary_root"],
        )
        if is_top_level and badge_ids and options["page_badges"] and not has_equivalent:
            rendered = badges_html(
                badge_ids,
                options["definitions"],
                options["default_color"],
                options["style"],
                block=True,
            )
            if rendered:
                markdown = _insert_after_title(markdown, rendered)
        if is_top_level:
            markdown = f"{markdown}\n{_PAGE_RUNTIME_MARKER}"
        return markdown.splitlines()


class BadgesPostprocessor(Postprocessor):
    """Render filter wrappers and install the self-contained browser runtime."""

    def __init__(self, md: Markdown, extension: ZensicalBadgesExtension):
        super().__init__(md)
        self.extension = extension

    def run(self, text: str) -> str:
        context = ContextPreprocessor.from_markdown(self.md)
        if context is None:
            return text
        is_top_level = _PAGE_RUNTIME_MARKER in text
        text = text.replace(_PAGE_RUNTIME_MARKER, "")
        options = self.extension.options(context)

        def replace_start(match: Any) -> str:
            badge_ids, filter_options = parse_options(match.group(1))
            return filter_html(
                badge_ids,
                options["definitions"],
                options["group_labels"],
                options["default_color"],
                options["style"],
                filter_options,
            )

        starts = len(_FILTER_START_RE.findall(text))
        ends = len(_FILTER_END_RE.findall(text))
        if starts != ends:
            log.warning(
                "Page %s has %d badge filter start marker(s) and %d end marker(s)",
                context.page.path,
                starts,
                ends,
            )
        text = _FILTER_START_RE.sub(replace_start, text)
        text = _FILTER_END_RE.sub("</div></div>", text)
        if not is_top_level:
            return text
        text = _EMBEDDED_RUNTIME_RE.sub("", text)
        return f"{text}\n{self.extension.browser_runtime(context, options)}"


class ZensicalBadgesExtension(Extension):
    """Provide full mkdocs-badges behavior in Zensical."""

    config = {
        "definitions": [{}, "Badge definitions keyed by badge identifier"],
        "group_labels": [{}, "Labels and tooltips keyed by badge group"],
        "default_color": [DEFAULT_COLOR, "Fallback badge color"],
        "style": ["rounded", "Badge shape: rounded, square, or pill"],
        "page_badges": [True, "Render frontmatter badges beneath the first heading"],
        "selectable_text": [False, "Allow badge and filter text selection"],
        "autosummary_root": [
            "modules/generated",
            "Docs-root directory for autosummary entries",
        ],
        "catalog_path": [
            "assets/mkdocs-badges/catalog.json",
            "Relative output path for reusable catalog JSON",
        ],
    }

    def __init__(self, **kwargs: Any):
        self._explicit = set(kwargs)
        super().__init__(**kwargs)

    def options(self, context: ContextPreprocessor) -> dict[str, Any]:
        plugin = context.config.get("plugins", {}).get("badges", {}).get("config", {})
        values: dict[str, Any] = {}
        for name in self.config:
            values[name] = (
                self.getConfig(name)
                if name in self._explicit
                else plugin.get(name, self.getConfig(name))
            )
        if values["style"] not in {"rounded", "square", "pill"}:
            values["style"] = "rounded"
        return values

    def browser_runtime(self, context: ContextPreprocessor, options: dict[str, Any]) -> str:
        pages = _catalog(context)
        payload = _runtime_payload(
            pages,
            options["definitions"],
            options["default_color"],
            options["style"],
            bool(options["selectable_text"]),
        )
        _write_catalog_json(
            _project_path(context.config, "site_dir", "site"),
            str(options["catalog_path"]),
            payload,
        )
        package = Path(__file__).parent
        css = (package / "assets/stylesheets/mkdocs-badges.css").read_text(encoding="utf-8")
        javascript = (package / "assets/javascripts/mkdocs-badges.js").read_text(encoding="utf-8")
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True).replace("</", "<\\/")
        css_json = json.dumps(css, ensure_ascii=False).replace("</", "<\\/")
        return (
            "<script data-mkdocs-badges-bootstrap>"
            "(()=>{let s=document.querySelector('style[data-mkdocs-badges]');"
            "if(!s){s=document.createElement('style');s.dataset.mkdocsBadges='';"
            f"s.textContent={css_json};"
            "document.head.appendChild(s);}})();"
            f"window.MKDOCS_BADGES={payload_json};</script>"
            "<script data-mkdocs-badges-runtime>"
            f"{javascript}</script>"
        )

    def extendMarkdown(self, md: Markdown) -> None:
        if ContextPreprocessor.from_markdown(md) is None:
            return
        md.registerExtension(self)
        md.preprocessors.register(BadgesPreprocessor(md, self), "mkdocs_badges", 27)
        md.postprocessors.register(BadgesPostprocessor(md, self), "mkdocs_badges", 15)


def makeExtension(**kwargs: Any) -> ZensicalBadgesExtension:
    """Load the extension through Python Markdown."""
    return ZensicalBadgesExtension(**kwargs)
