"""MkDocs plugin implementation."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from mkdocs.config import base, config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File, Files
from mkdocs.structure.pages import Page

from .render import DEFAULT_COLOR, badge_html, badges_html, filter_html, parse_options

log = logging.getLogger("mkdocs.plugins.badges")

_SHORTCODE_RE = re.compile(r"{%\s*(badge|badges)\s+(.+?)\s*%}")
_FILTER_START_RE = re.compile(r"<!--\s*mkdocs-badges:filter\s+(.+?)\s*-->")
_FILTER_END_RE = re.compile(r"<!--\s*mkdocs-badges:end\s*-->")
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


class BadgesConfig(base.Config):
    definitions = config_options.Type(dict, default={})
    group_labels = config_options.Type(dict, default={})
    default_color = config_options.Type(str, default=DEFAULT_COLOR)
    style = config_options.Choice(("rounded", "square", "pill"), default="rounded")
    page_badges = config_options.Type(bool, default=True)


class BadgesPlugin(BasePlugin[BadgesConfig]):
    """Render badge shortcodes and ship their Material-friendly assets."""

    def on_startup(self, *, command: str, dirty: bool = False) -> None:
        self._page_badges: dict[str, list[str]] = {}

    def on_config(self, config: base.Config) -> base.Config:
        # ``on_startup`` is not invoked by every programmatic MkDocs build.
        self._page_badges = {}
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
        if badge_ids:
            self._page_badges[_normalise_url(page.url)] = badge_ids
            if self.config.page_badges:
                rendered = badges_html(
                    badge_ids,
                    self.config.definitions,
                    self.config.default_color,
                    self.config.style,
                    block=True,
                )
                markdown = _insert_after_title(markdown, rendered)
        return _replace_shortcodes(
            markdown,
            self.config.definitions,
            self.config.default_color,
            self.config.style,
        )

    def on_page_content(
        self,
        html: str,
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

        starts = len(_FILTER_START_RE.findall(html))
        ends = len(_FILTER_END_RE.findall(html))
        if starts != ends:
            log.warning(
                "Page %s has %d badge filter start marker(s) and %d end marker(s)",
                page.file.src_uri,
                starts,
                ends,
            )
        html = _FILTER_START_RE.sub(replace_start, html)
        return _FILTER_END_RE.sub("</div></div>", html)

    def on_post_build(self, *, config: base.Config) -> None:
        output = Path(config.site_dir) / "assets/javascripts/mkdocs-badges-data.js"
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(self._page_badges, ensure_ascii=False, sort_keys=True)
        output.write_text(f"window.MKDOCS_BADGES_DATA={payload};\n", encoding="utf-8")


def _normalise_badges(value: Any) -> list[str]:
    if isinstance(value, str):
        values = re.split(r"[\s,]+", value)
    elif isinstance(value, (list, tuple)):
        values = [str(item) for item in value]
    else:
        return []
    return list(dict.fromkeys(item.strip() for item in values if item.strip()))


def _normalise_url(url: str) -> str:
    if url in {".", "./", "/"}:
        return ""
    url = url.lstrip("./")
    if url.endswith("index.html"):
        url = url[: -len("index.html")]
    elif url.endswith(".html"):
        url = f"{url[:-5]}/"
    return url


def _insert_after_title(markdown: str, rendered: str) -> str:
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        if re.match(r"^#\s+\S", line):
            lines[index + 1 : index + 1] = ["", rendered, ""]
            return "\n".join(lines)
    return f"{rendered}\n\n{markdown}"


def _replace_shortcodes(
    markdown: str,
    definitions: dict[str, dict[str, Any]],
    default_color: str,
    style: str,
) -> str:
    """Replace badge shortcodes outside fenced code blocks."""
    in_fence = False
    fence_char = ""
    fence_size = 0
    output: list[str] = []

    def replace(match: re.Match[str]) -> str:
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

    for line in markdown.splitlines(keepends=True):
        fence = _FENCE_RE.match(line)
        if fence:
            marker = fence.group(1)
            if not in_fence:
                in_fence = True
                fence_char, fence_size = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_size:
                in_fence = False
        output.append(line if in_fence or fence else _SHORTCODE_RE.sub(replace, line))
    return "".join(output)
