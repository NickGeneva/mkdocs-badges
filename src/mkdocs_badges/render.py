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
EYE_OPEN_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z"/>'
    '<circle cx="12" cy="12" r="3"/></svg>'
)
EYE_CLOSED_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
    '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8 '
    'a18.45 18.45 0 0 1 5.06-5.94"/>'
    '<path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8 '
    'a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>'
    "</svg>"
)
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
    name: str
    hidden: bool
    hide_in: tuple[str, ...]

    def visible_in(self, context: str) -> bool:
        """Return whether this badge has visual markup in a render context."""
        return not self.hidden and context.lower() not in self.hide_in


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _as_contexts(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        values = re.split(r"[\s,]+", value)
    elif isinstance(value, Sequence):
        values = [str(item) for item in value]
    else:
        return ()
    return tuple(dict.fromkeys(item.strip().lower() for item in values if item.strip()))


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
    tooltip = str(values.get("tooltip", ""))
    display_name = values.get("name") or values.get("display_name") or tooltip or label
    return BadgeDefinition(
        badge_id=badge_id,
        group=group,
        label=str(label),
        color=_safe_color(values.get("color", default_color), DEFAULT_COLOR),
        text_color=_safe_color(values.get("text_color", "#fff"), "#fff"),
        icon=str(values.get("icon", "")),
        tooltip=tooltip,
        name=str(display_name),
        hidden=_as_bool(values.get("hidden", False)),
        hide_in=_as_contexts(values.get("hide_in", ())),
    )


def badge_html(
    badge_id: str,
    definitions: Mapping[str, Mapping[str, Any]],
    default_color: str,
    style: str,
    label_override: str | None = None,
    *,
    context: str = "page",
) -> str:
    """Render one badge. Configuration icons may intentionally contain HTML."""
    badge = resolve_badge(badge_id, definitions, default_color)
    if not badge.visible_in(context):
        return ""
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
    extra_class: str = "",
    context: str = "page",
) -> str:
    tag = "div" if block else "span"
    classes = "mkdocs-badge-list"
    if extra_class:
        classes = f"{classes} {extra_class}"
    items = "".join(
        badge_html(badge_id, definitions, default_color, style, context=context)
        for badge_id in badge_ids
        if badge_id
    )
    return f'<{tag} class="{classes}">{items}</{tag}>' if items else ""


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
    label_source = str(options.get("labels", "auto")).lower()
    if label_source not in {"auto", "label", "name"}:
        label_source = "auto"
    visible_ids = [
        badge_id
        for badge_id in badge_ids
        if resolve_badge(badge_id, definitions, default_color).visible_in("filter")
    ]
    parsed = [(badge_id, *parse_badge_id(badge_id)) for badge_id in visible_ids]
    grouped = bool(parsed) and all(group for _, group, _ in parsed)
    attrs = {
        "class": "mkdocs-badge-filter",
        "data-filter-mode": mode,
        "data-grouped": str(grouped).lower(),
        "data-badge-order": ",".join(visible_ids) if fixed else "",
        "data-group-visibility-toggle": str(toggle).lower(),
        "data-groups-hidden": ",".join(hidden),
        "data-filter-label-source": label_source,
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
                    f'title="Hide {html.escape(config["label"], quote=True)} badges" '
                    f'aria-label="Toggle {html.escape(config["label"], quote=True)} badges" '
                    'aria-pressed="false">'
                    f'<span class="mkdocs-badge-filter__eye-open">{EYE_OPEN_SVG}</span>'
                    f'<span class="mkdocs-badge-filter__eye-closed">{EYE_CLOSED_SVG}</span>'
                    "</button>"
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
                _filter_button(
                    badge_id,
                    definitions,
                    default_color,
                    style,
                    label_source=label_source,
                )
                for badge_id in members
            )
            result.append("</div>")
        result.append(
            '<button type="button" class="mkdocs-badge-filter__clear" hidden>Clear filters</button>'
        )
    else:
        result.append('<span class="mkdocs-badge-filter__group">Filter by</span>')
        result.append(
            '<button type="button" class="mkdocs-badge-filter__all" '
            'data-badge-id="__all__" aria-pressed="true">All</button>'
        )
        result.extend(
            _filter_button(
                badge_id,
                definitions,
                default_color,
                style,
                label_source=label_source,
            )
            for badge_id in visible_ids
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
    *,
    label_source: str = "name",
) -> str:
    definition = resolve_badge(badge_id, definitions, default_color)
    display_label = definition.label if label_source == "label" else definition.name
    badge = badge_html(
        badge_id,
        definitions,
        default_color,
        style,
        display_label,
        context="filter",
    )
    return (
        '<button type="button" class="mkdocs-badge-filter__button" '
        f'data-badge-id="{html.escape(badge_id, quote=True)}" aria-pressed="false">'
        f"{badge}</button>"
    )
