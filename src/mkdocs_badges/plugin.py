"""MkDocs plugin implementation."""

from __future__ import annotations

import fnmatch
import html
import json
import logging
import posixpath
import re
from pathlib import Path, PurePosixPath
from typing import Any

from mkdocs.config import base, config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page
from mkdocs.utils import get_relative_url
from mkdocs.utils.meta import get_data

from .render import (
    DEFAULT_COLOR,
    badge_html,
    badges_html,
    filter_html,
    parse_options,
    resolve_badge,
)

log = logging.getLogger("mkdocs.plugins.badges")

_SHORTCODE_RE = re.compile(r"{%\s*(badge|badges)\s+(.+?)\s*%}")
_AUTOSUMMARY_INLINE_RE = re.compile(r"{%\s*autosummary\s+(.+?)\s*%}")
_AUTOSUMMARY_START_RE = re.compile(r"^\s*{%\s*autosummary\s*%}\s*$")
_AUTOSUMMARY_END_RE = re.compile(r"^\s*{%\s*endautosummary\s*%}\s*$")
_FILTER_START_RE = re.compile(r"<!--\s*mkdocs-badges:filter\s+(.+?)\s*-->")
_FILTER_END_RE = re.compile(r"<!--\s*mkdocs-badges:end\s*-->")
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_HEADING_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
_PARAGRAPH_RE = re.compile(r"(?:^|\n\s*\n)(?![#>`*\-])([^\n][^\n]*(?:\n(?!\s*\n)[^\n]+)*)")


class BadgesConfig(base.Config):
    definitions = config_options.Type(dict, default={})
    group_labels = config_options.Type(dict, default={})
    default_color = config_options.Type(str, default=DEFAULT_COLOR)
    style = config_options.Choice(("rounded", "square", "pill"), default="rounded")
    page_badges = config_options.Type(bool, default=True)
    selectable_text = config_options.Type(bool, default=False)
    autosummary_root = config_options.Type(str, default="modules/generated")
    catalog_path = config_options.Type(str, default="assets/mkdocs-badges/catalog.json")


class BadgesPlugin(BasePlugin[BadgesConfig]):
    """Render badges, page summaries, and interactive Material filters."""

    def on_startup(self, *, command: str, dirty: bool = False) -> None:
        self._pages: dict[str, dict[str, Any]] = {}

    def on_config(self, config: base.Config) -> base.Config:
        self._pages = {}
        css = "assets/stylesheets/mkdocs-badges.css"
        data = "assets/javascripts/mkdocs-badges-data.js"
        js = "assets/javascripts/mkdocs-badges.js"
        if css not in config.extra_css:
            config.extra_css.append(css)
        for asset in (data, js):
            if asset not in config.extra_javascript:
                config.extra_javascript.append(asset)
        return config

    def on_files(self, files: Files, *, config: base.Config) -> Files:
        package_root = Path(__file__).parent
        for path in (
            "assets/stylesheets/mkdocs-badges.css",
            "assets/javascripts/mkdocs-badges.js",
        ):
            if path not in files:
                files.append(
                    File(
                        path,
                        str(package_root),
                        config.site_dir,
                        config.use_directory_urls,
                    )
                )

        # Build the complete page catalogue before Markdown rendering. This makes
        # autosummary output deterministic and avoids build-order-dependent links.
        for file in files.documentation_pages():
            try:
                source = Path(file.abs_src_path).read_text(encoding="utf-8")
            except OSError:
                continue
            body, metadata = get_data(source)
            self._pages[file.src_uri] = _page_record(file, body, metadata)
        return files

    def on_page_markdown(
        self,
        markdown: str,
        *,
        page: Page,
        config: base.Config,
        files: Files,
    ) -> str:
        badge_ids = _normalise_badges(page.meta.get("badges", []))
        record = self._pages.setdefault(
            page.file.src_uri,
            _page_record(page.file, markdown, page.meta),
        )
        record.update(
            {
                "title": str(page.meta.get("title") or page.title or record["title"]),
                "summary": str(
                    page.meta.get("summary") or page.meta.get("description") or record["summary"]
                ),
                "badges": badge_ids,
                "url": page.url,
                "dest_uri": page.file.dest_uri,
            }
        )

        has_equivalent_badge_list = _contains_equivalent_badges_shortcode(markdown, badge_ids)
        markdown = _replace_markup(
            markdown,
            page.url,
            self._pages,
            self.config.definitions,
            self.config.default_color,
            self.config.style,
            autosummary_root=self.config.autosummary_root,
        )
        if badge_ids and self.config.page_badges and not has_equivalent_badge_list:
            rendered = badges_html(
                badge_ids,
                self.config.definitions,
                self.config.default_color,
                self.config.style,
                block=True,
            )
            if rendered:
                markdown = _insert_after_title(markdown, rendered)
        return markdown

    def on_page_content(
        self,
        html_content: str,
        *,
        page: Page,
        config: base.Config,
        files: Files,
    ) -> str:
        def replace_start(match: re.Match[str]) -> str:
            badge_ids, options = parse_options(match.group(1))
            return filter_html(
                badge_ids,
                self.config.definitions,
                self.config.group_labels,
                self.config.default_color,
                self.config.style,
                options,
            )

        starts = len(_FILTER_START_RE.findall(html_content))
        ends = len(_FILTER_END_RE.findall(html_content))
        if starts != ends:
            log.warning(
                "Page %s has %d badge filter start marker(s) and %d end marker(s)",
                page.file.src_uri,
                starts,
                ends,
            )
        html_content = _FILTER_START_RE.sub(replace_start, html_content)
        return _FILTER_END_RE.sub("</div></div>", html_content)

    def on_post_build(self, *, config: base.Config) -> None:
        output = Path(config.site_dir) / "assets/javascripts/mkdocs-badges-data.js"
        output.parent.mkdir(parents=True, exist_ok=True)

        payload = _runtime_payload(
            self._pages,
            self.config.definitions,
            self.config.default_color,
            self.config.style,
            self.config.selectable_text,
        )
        output.write_text(
            "// Generated by mkdocs-badges.\n"
            f"window.MKDOCS_BADGES={json.dumps(payload, ensure_ascii=False, sort_keys=True)};\n",
            encoding="utf-8",
        )
        _write_catalog_json(config.site_dir, self.config.catalog_path, payload)


def _runtime_payload(
    pages: dict[str, dict[str, Any]],
    configured_definitions: dict[str, dict[str, Any]],
    default_color: str,
    style: str,
    selectable_text: bool,
) -> dict[str, Any]:
    """Build browser state and a richer reusable documentation catalog."""
    page_index: dict[str, list[str]] = {}
    seen_badges: set[str] = set(configured_definitions)
    catalog: list[dict[str, Any]] = []
    for src_uri, record in pages.items():
        badges = list(record.get("badges", []))
        seen_badges.update(badges)
        if badges:
            for alias in _page_aliases(src_uri, record):
                page_index[alias] = badges
        catalog.append(
            {
                "source": src_uri,
                "url": str(record.get("url", "")),
                "title": str(record.get("title", "")),
                "summary": str(record.get("summary", "")),
                "signature": str(record.get("signature", "")),
                "symbol": str(record.get("symbol", "")),
                "classifiers": badges,
            }
        )

    definitions: dict[str, dict[str, Any]] = {}
    for badge_id in sorted(seen_badges):
        definition = resolve_badge(badge_id, configured_definitions, default_color)
        definitions[badge_id] = {
            "label": definition.label,
            "color": definition.color,
            "text_color": definition.text_color,
            "group": definition.group,
            "icon": definition.icon,
            "tooltip": definition.tooltip,
            "hidden": definition.hidden,
        }
    return {
        "pages": page_index,
        "catalog": catalog,
        "definitions": definitions,
        "style": style,
        "selectable_text": selectable_text,
    }


def _write_catalog_json(site_dir: str | Path, catalog_path: str, payload: dict[str, Any]) -> None:
    """Write the reusable catalog JSON when a safe relative path is configured."""
    if not catalog_path:
        return
    relative = PurePosixPath(catalog_path.replace("\\", "/"))
    if relative.is_absolute() or ".." in relative.parts:
        log.warning("Ignoring unsafe badges catalog path %r", catalog_path)
        return
    output = Path(site_dir).joinpath(*relative.parts)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {"catalog": payload["catalog"], "definitions": payload["definitions"]},
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def _page_record(file: File, body: str, metadata: dict[str, Any]) -> dict[str, Any]:
    title_match = _HEADING_RE.search(body)
    fallback_title = PurePosixPath(file.src_uri).stem.replace("-", " ").title()
    title = metadata.get("title") or (title_match.group(1) if title_match else fallback_title)
    summary = _first_sentence(
        metadata.get("summary") or metadata.get("description") or _first_paragraph(body)
    )
    symbol = next(
        (
            str(metadata[key]).strip()
            for key in ("symbol", "api_name", "object", "import_path")
            if metadata.get(key)
        ),
        "",
    )
    if not symbol and "." in str(title) and " " not in str(title):
        symbol = str(title).strip("` ")
    return {
        "title": str(title),
        "summary": str(summary),
        "signature": str(metadata.get("signature", "")),
        "symbol": symbol,
        "badges": _normalise_badges(metadata.get("badges", [])),
        "url": file.url,
        "dest_uri": file.dest_uri,
    }


def _first_paragraph(body: str) -> str:
    without_title = _HEADING_RE.sub("", body, count=1)
    match = _PARAGRAPH_RE.search(without_title)
    if not match:
        return ""
    return " ".join(match.group(1).split())


def _first_sentence(value: Any) -> str:
    """Return a compact autosummary description matching Sphinx's convention."""
    text = " ".join(str(value).split())
    if not text:
        return ""

    # Avoid splitting common abbreviations and decimal/version numbers while
    # keeping the implementation dependency-free.
    abbreviations = {
        "e.g.",
        "i.e.",
        "etc.",
        "mr.",
        "mrs.",
        "ms.",
        "dr.",
        "prof.",
        "sr.",
        "jr.",
        "vs.",
    }
    for index, character in enumerate(text):
        if character not in ".!?":
            continue
        if index + 1 < len(text) and not text[index + 1].isspace():
            continue
        token = text[: index + 1].rsplit(" ", 1)[-1].lower()
        if token in abbreviations:
            continue
        if character == "." and index and index + 1 < len(text):
            if text[index - 1].isdigit() and text[index + 1].isdigit():
                continue
        return text[: index + 1]
    return text


def _normalise_badges(value: Any) -> list[str]:
    if isinstance(value, str):
        values = re.split(r"[\s,]+", value)
    elif isinstance(value, (list, tuple)):
        values = [str(item) for item in value]
    else:
        return []
    return list(dict.fromkeys(item.strip() for item in values if item.strip()))


def _normalise_url(url: str) -> str:
    url = url.split("#", 1)[0].split("?", 1)[0].replace("\\", "/")
    while url.startswith("./"):
        url = url[2:]
    url = url.lstrip("/")
    if url.endswith("/index.html"):
        url = url[: -len("index.html")]
    elif url == "index.html":
        url = ""
    elif url.endswith(".html"):
        url = f"{url[:-5]}/"
    return url


def _page_aliases(src_uri: str, record: dict[str, Any]) -> set[str]:
    src = src_uri.replace("\\", "/")
    aliases = {
        _normalise_url(str(record.get("url", ""))),
        _normalise_url(str(record.get("dest_uri", ""))),
        _normalise_url(src),
        _normalise_url(str(PurePosixPath(src).with_suffix(""))),
    }
    return aliases


def _symbol_aliases(src_uri: str, record: dict[str, Any]) -> set[str]:
    """Return explicit and inferred Python API names for a generated page."""
    candidates = {
        str(record.get("symbol", "")).strip("` "),
        str(record.get("title", "")).strip("` "),
        PurePosixPath(src_uri).stem.replace("_", "."),
    }
    aliases: set[str] = set()
    for candidate in candidates:
        if not candidate or "." not in candidate or " " in candidate:
            continue
        parts = candidate.split(".")
        aliases.add(candidate)
        # Permit package-relative symbols while retaining at least one module
        # component. Bare object names are intentionally excluded because they
        # are commonly ambiguous in large API catalogs.
        aliases.update(".".join(parts[index:]) for index in range(1, len(parts) - 1))
    return aliases


def _symbol_matches(entry: str, pages: dict[str, dict[str, Any]]) -> list[str]:
    """Resolve a Python symbol only when it identifies one generated page."""
    matches = [
        src_uri for src_uri, record in pages.items() if entry in _symbol_aliases(src_uri, record)
    ]
    if len(matches) > 1:
        log.warning(
            "Autosummary API symbol %r is ambiguous; matched %s",
            entry,
            ", ".join(matches),
        )
        return []
    return matches


def _insert_after_title(markdown: str, rendered: str) -> str:
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        if re.match(r"^#\s+\S", line):
            lines[index + 1 : index + 1] = ["", rendered, ""]
            return "\n".join(lines)
    return f"{rendered}\n\n{markdown}"


def _contains_equivalent_badges_shortcode(markdown: str, badge_ids: list[str]) -> bool:
    """Return whether the page explicitly renders the same badges as one list."""
    expected = sorted(badge_ids)
    for match in _SHORTCODE_RE.finditer(markdown):
        if match.group(1) != "badges":
            continue
        rendered_ids, _ = parse_options(match.group(2))
        if sorted(rendered_ids) == expected:
            return True
    return False


def _replace_markup(
    markdown: str,
    current_url: str,
    pages: dict[str, dict[str, Any]],
    definitions: dict[str, dict[str, Any]],
    default_color: str,
    style: str,
    *,
    source_links: bool = False,
    autosummary_root: str = "modules/generated",
) -> str:
    """Replace plugin markup outside fenced code blocks."""
    in_fence = False
    fence_char = ""
    fence_size = 0
    summary_lines: list[str] | None = None
    output: list[str] = []

    def replace_badge(match: re.Match[str]) -> str:
        kind, raw = match.groups()
        ids, options = parse_options(raw)
        if not ids:
            return match.group(0)
        if kind == "badge":
            label = options.get("label")
            return badge_html(
                ids[0],
                definitions,
                default_color,
                style,
                str(label) if label is not None else None,
            )
        return badges_html(ids, definitions, default_color, style)

    def replace_summary(match: re.Match[str]) -> str:
        entries, options = parse_options(match.group(1))
        return _autosummary_html(
            entries,
            options,
            current_url,
            pages,
            definitions,
            default_color,
            style,
            source_links=source_links,
            autosummary_root=autosummary_root,
        )

    for line in markdown.splitlines(keepends=True):
        fence = _FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_char, fence_size = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_size:
                in_fence = False
            output.append(line)
            continue

        if in_fence:
            output.append(line)
            continue

        if summary_lines is not None:
            if _AUTOSUMMARY_END_RE.match(line):
                entries = [item.strip() for item in summary_lines if item.strip()]
                output.append(
                    _autosummary_html(
                        entries,
                        {},
                        current_url,
                        pages,
                        definitions,
                        default_color,
                        style,
                        source_links=source_links,
                        autosummary_root=autosummary_root,
                    )
                    + "\n"
                )
                summary_lines = None
            elif line.strip() and not line.lstrip().startswith("#"):
                summary_lines.append(line.strip())
            continue

        if _AUTOSUMMARY_START_RE.match(line):
            summary_lines = []
            continue

        line = _AUTOSUMMARY_INLINE_RE.sub(replace_summary, line)
        output.append(_SHORTCODE_RE.sub(replace_badge, line))

    if summary_lines is not None:
        log.warning("Unclosed autosummary block")
        output.extend(["{% autosummary %}\n", *summary_lines])
    return "".join(output)


def _autosummary_html(
    entries: list[str],
    options: dict[str, str | bool],
    current_url: str,
    pages: dict[str, dict[str, Any]],
    definitions: dict[str, dict[str, Any]],
    default_color: str,
    style: str,
    *,
    source_links: bool = False,
    autosummary_root: str = "modules/generated",
) -> str:
    selected: list[tuple[str, dict[str, Any]]] = []
    for entry in entries:
        raw_pattern = entry.replace("\\", "/")
        docs_root_relative = raw_pattern.startswith("/")
        pattern = raw_pattern.lstrip("/")
        while pattern.startswith("./"):
            pattern = pattern[2:]
        root = autosummary_root.replace("\\", "/").strip("/")
        already_rooted = pattern == root or pattern.startswith(f"{root}/")
        patterns = [posixpath.normpath(pattern)]
        if root and root != "." and not docs_root_relative and not already_rooted:
            patterns.insert(0, posixpath.normpath(posixpath.join(root, pattern)))
        matches: list[str] = []
        for candidate in patterns:
            matches = [key for key in pages if fnmatch.fnmatch(key, candidate)]
            if not matches and not candidate.endswith(".md"):
                matches = [key for key in pages if key == f"{candidate}.md"]
            if matches:
                break
        if not matches and "/" not in raw_pattern and not raw_pattern.endswith(".md"):
            matches = _symbol_matches(raw_pattern.strip("` "), pages)
        if not matches:
            log.warning("Autosummary entry %r did not match a documentation page", entry)
            continue
        for key in matches:
            if all(existing != key for existing, _ in selected):
                selected.append((key, pages[key]))

    title = str(options.get("title", "API"))
    description = str(options.get("description", "Description"))
    headers = str(options.get("headers", "false")).lower() in {"1", "true", "yes"}
    signatures = str(options.get("signatures", "none")).lower()
    show_badges = str(options.get("badges", "true")).lower() not in {"0", "false", "no"}
    rows: list[str] = []
    for src_uri, record in selected:
        target_url = str(record["url"])
        if source_links:
            # Zensical resolves Markdown links after extensions run. Give it a
            # path relative to the current Markdown source so it performs that
            # conversion exactly once. Passing an already output-relative URL
            # causes nested pages to climb one directory too far.
            current_parent = PurePosixPath(current_url).parent.as_posix()
            href = posixpath.relpath(src_uri.lstrip("./"), current_parent)
        else:
            href = get_relative_url(target_url, current_url)
        badge_ids = list(record.get("badges", []))
        badge_markup = (
            badges_html(
                badge_ids,
                definitions,
                default_color,
                style,
                extra_class="mkdocs-badge-list--summary",
            )
            if show_badges
            else ""
        )
        signature = str(record.get("signature", ""))
        if signatures == "long":
            displayed_signature = signature
        elif signatures == "short" and signature:
            displayed_signature = "(…)"
        else:
            displayed_signature = ""
        name = f"{record['title']}{displayed_signature}"
        rows.append(
            f'<tr data-page-src="{html.escape(src_uri, quote=True)}" '
            f'data-page-url="{html.escape(target_url, quote=True)}" '
            f'data-badge-ids="{html.escape(",".join(badge_ids), quote=True)}">'
            f'<td><a href="{html.escape(href, quote=True)}"><code>{html.escape(name)}</code></a>'
            f"{badge_markup}</td><td>{html.escape(str(record['summary']))}</td></tr>"
        )
    heading = (
        f"<thead><tr><th>{html.escape(title)}</th><th>{html.escape(description)}</th></tr></thead>"
        if headers
        else ""
    )
    return (
        f'<table class="mkdocs-badges-autosummary">{heading}<tbody>{"".join(rows)}</tbody></table>'
    )
