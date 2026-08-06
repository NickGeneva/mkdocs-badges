"""Configuration resolution and safe HTML rendering."""

from __future__ import annotations

import html
import re
import shlex
from collections import OrderedDict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

DEFAULT_COLOR = "#6c757d"
DEFAULT_DEFINITIONS: dict[str, dict[str, str]] = {
    "stable": {"label": "Stable", "color": "#198754", "text_color": "#fff"},
    "beta": {"label": "Beta", "color": "#0dcaf0", "text_color": "#000"},
    "experimental": {
        "label": "Experimental",
        "color": "#ffc107",
        "text_color": "#000",
    },
    "deprecated": {
        "label": "Deprecated",
        "color": "#dc3545",
        "text_color": "#fff",
    },
    "new": {"label": "New", "color": "#0d6efd", "text_color": "#fff"},
}

_COLOR_RE = re.compile(
    r"^(?:#[0-9a-fA-F]{3,8}|[a-zA-Z]+|(?:rgb|rgba|hsl|hsla)\([0-9.,%\s]+\)|var\(--[\w-]+\))$"
)


def parse_badge_id(badge_id: str) -> tuple[str, str]:
    """Split ``group:name`` into a group and name."""
    if ":" in badge_id:
        group, name = badge_id.split(":", 1)
        return group.strip(), name.strip()
    return "", badge_id.strip()


def _safe_color(value: Any, fallback: str) -> str:
    value = str(value).strip()
    return value if _COLOR_RE.fullmatch(value) else fallback


@dataclass(frozen=True)
class BadgeDefinition:
    badge_id: str
    group: str
    label: str
    color: str
    text_color: str
    icon: str
    tooltip: str


def resolve_badge(
    badge_id: str,
    definitions: Mapping[str, Mapping[str, Any]],
    default_color: str = DEFAULT_COLOR,
) -> BadgeDefinition:
    """Resolve exact, bare-name, built-in, and generated definitions in order."""
    group, name = parse_badge_id(badge_id)
    values: dict[str, Any] = {}
    values.update(DEFAULT_DEFINITIONS.get(name, {}))
    values.update(DEFAULT_DEFINITIONS.get(badge_id, {}))
    values.update(definitions.get(name, {}))
    values.update(definitions.get(badge_id, {}))
    label = values.get("label")
    if label is None:
        label = name.replace("_", " ").replace("-", " ").title()
    return BadgeDefinition(
        badge_id=badge_id,
        group=group,
        label=str(label),
        color=_safe_color(values.get("color", default_color), DEFAULT_COLOR),
        text_color=_safe_color(values.get("text_color", "#fff"), "#fff"),
        icon=str(values.get("icon", "")),
        tooltip=str(values.get("tooltip", "")),
    )


def badge_html(
    badge_id: str,
    definitions: Mapping[str, Mapping[str, Any]],
    default_color: str,
    style: str,
    label_override: str | None = None,
) -> str:
    """Render one badge. Configuration icons may intentionally contain HTML."""
    badge = resolve_badge(badge_id, definitions, default_color)
    label = badge.label if label_override is None else label_override
    content = ""
    if badge.icon:
        content += f'<span class="mkdocs-badge__icon">{badge.icon}</span>'
    if label:
        content += f'<span class="mkdocs-badge__label">{html.escape(label)}</span>'
    attrs = {
        "class": f"mkdocs-badge mkdocs-badge--{style}",
        "data-badge-id": badge.badge_id,
        "data-badge-group": badge.group,
        "style": f"--badge-color:{badge.color};--badge-text-color:{badge.text_color}",
    }
    if badge.tooltip:
        attrs["title"] = badge.tooltip
    rendered_attrs = " ".join(
        f'{key}="{html.escape(value, quote=True)}"' for key, value in attrs.items()
    )
    return f"<span {rendered_attrs}>{content}</span>"


def badges_html(
    badge_ids: Sequence[str],
    definitions: Mapping[str, Mapping[str, Any]],
    default_color: str,
    style: str,
    *,
    block: bool = False,
) -> str:
    tag = "div" if block else "span"
    items = "".join(
        badge_html(badge_id, definitions, default_color, style)
        for badge_id in badge_ids
        if badge_id
    )
    return f'<{tag} class="mkdocs-badge-list">{items}</{tag}>'


def group_config(group: str, labels: Mapping[str, Any]) -> dict[str, str]:
    raw = labels.get(group)
    fallback = group.replace("_", " ").replace("-", " ").title()
    if isinstance(raw, str):
        return {"label": raw, "tooltip": ""}
    if isinstance(raw, Mapping):
        return {
            "label": str(raw.get("label", fallback)),
            "tooltip": str(raw.get("tooltip", "")),
        }
    return {"label": fallback, "tooltip": ""}


def parse_options(raw: str) -> tuple[list[str], dict[str, str | bool]]:
    """Parse a shortcode body into positional IDs and key/value options."""
    tokens = shlex.split(raw)
    ids: list[str] = []
    options: dict[str, str | bool] = {}
    for token in tokens:
        if "=" in token:
            key, value = token.split("=", 1)
            options[key.replace("-", "_")] = value
        else:
            ids.append(token)
    return ids, options


def filter_html(
    badge_ids: Sequence[str],
    definitions: Mapping[str, Mapping[str, Any]],
    group_labels: Mapping[str, Any],
    default_color: str,
    style: str,
    options: Mapping[str, str | bool],
) -> str:
    """Render filter controls and the opening content container."""
    mode = str(options.get("mode", "and")).lower()
    mode = mode if mode in {"and", "or"} else "and"
    fixed = str(options.get("order", "")).lower() == "fixed"
    toggle = str(options.get("toggle", "false")).lower() in {"1", "true", "yes"}
    hidden = str(options.get("hidden", "")).replace(",", " ").split()
    parsed = [(badge_id, *parse_badge_id(badge_id)) for badge_id in badge_ids]
    grouped = bool(parsed) and all(group for _, group, _ in parsed)
    attrs = {
        "class": "mkdocs-badge-filter",
        "data-filter-mode": mode,
        "data-grouped": str(grouped).lower(),
        "data-badge-order": ",".join(badge_ids) if fixed else "",
        "data-groups-hidden": ",".join(hidden),
    }
    attr_html = " ".join(
        f'{key}="{html.escape(value, quote=True)}"' for key, value in attrs.items() if value
    )
    result = [f"<div {attr_html}>", '<div class="mkdocs-badge-filter__controls">']
    if grouped:
        groups: OrderedDict[str, list[str]] = OrderedDict()
        for badge_id, group, _ in parsed:
            groups.setdefault(group, []).append(badge_id)
        for group, members in groups.items():
            config = group_config(group, group_labels)
            escaped_group = html.escape(group, quote=True)
            result.append(
                f'<div class="mkdocs-badge-filter__row" data-badge-group="{escaped_group}">'
            )
            if toggle:
                result.append(
                    '<button type="button" class="mkdocs-badge-filter__toggle" '
                    f'data-badge-group="{html.escape(group, quote=True)}" '
                    f'aria-label="Toggle {html.escape(config["label"], quote=True)} badges" '
                    'aria-pressed="false"><span aria-hidden="true">◉</span></button>'
                )
            title = (
                f' title="{html.escape(config["tooltip"], quote=True)}"'
                if config["tooltip"]
                else ""
            )
            result.append(
                f'<span class="mkdocs-badge-filter__group"{title}>'
                f"{html.escape(config['label'])}</span>"
            )
            result.extend(
                _filter_button(badge_id, definitions, default_color, style) for badge_id in members
            )
            result.append("</div>")
        result.append(
            '<button type="button" class="mkdocs-badge-filter__clear" hidden>Clear filters</button>'
        )
    else:
        result.append('<span class="mkdocs-badge-filter__group">Filter by</span>')
        result.extend(
            _filter_button(badge_id, definitions, default_color, style) for badge_id in badge_ids
        )
        result.append(
            '<button type="button" class="mkdocs-badge-filter__clear" hidden>Clear filters</button>'
        )
    result.extend(["</div>", '<div class="mkdocs-badge-filter__content">'])
    return "".join(result)


def _filter_button(
    badge_id: str,
    definitions: Mapping[str, Mapping[str, Any]],
    default_color: str,
    style: str,
) -> str:
    badge = badge_html(badge_id, definitions, default_color, style)
    return (
        '<button type="button" class="mkdocs-badge-filter__button" '
        f'data-badge-id="{html.escape(badge_id, quote=True)}" aria-pressed="false">'
        f"{badge}</button>"
    )
