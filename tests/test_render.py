from mkdocs_badges.render import (
    badge_html,
    badges_html,
    filter_html,
    parse_badge_id,
    parse_options,
    resolve_badge,
)


def test_grouped_badge_inherits_bare_default():
    badge = resolve_badge("stability:stable", {}, "#aaa")
    assert badge.group == "stability"
    assert badge.label == "Stable"
    assert badge.color == "#198754"


def test_exact_definition_wins_and_label_is_escaped():
    definitions = {
        "stable": {"label": "Base", "color": "red"},
        "stability:stable": {"label": "Exact", "color": "green"},
    }
    rendered = badge_html("stability:stable", definitions, "#aaa", "pill", "<unsafe>")
    assert "--badge-color:green" in rendered
    assert "&lt;unsafe&gt;" in rendered
    assert "mkdocs-badge--pill" in rendered


def test_invalid_color_falls_back():
    badge = resolve_badge("custom", {"custom": {"color": "url(evil)"}}, "#abc")
    assert badge.color == "#6c757d"


def test_hidden_badge_remains_defined_but_has_no_visual_markup():
    definitions = {"provider:nvidia": {"label": "NVIDIA", "hidden": True}}
    definition = resolve_badge("provider:nvidia", definitions)
    assert definition.hidden is True
    assert badge_html("provider:nvidia", definitions, "#aaa", "pill") == ""
    assert badges_html(["provider:nvidia"], definitions, "#aaa", "pill") == ""


def test_hide_in_only_suppresses_selected_render_contexts():
    definitions = {
        "provider:nvidia": {
            "label": "NV",
            "name": "NVIDIA",
            "tooltip": "NVIDIA provider",
            "hide_in": ["autosummary"],
        }
    }
    definition = resolve_badge("provider:nvidia", definitions)
    assert definition.name == "NVIDIA"
    assert definition.hide_in == ("autosummary",)
    assert "NV" in badge_html("provider:nvidia", definitions, "#aaa", "pill")
    assert (
        badge_html(
            "provider:nvidia",
            definitions,
            "#aaa",
            "pill",
            context="autosummary",
        )
        == ""
    )


def test_filter_uses_full_name_and_respects_filter_visibility():
    definitions = {
        "task:medium-range": {
            "label": "MRF",
            "name": "Medium Range Forecast",
        },
        "provider:nvidia": {"label": "NV", "hide_in": ["filter"]},
    }
    rendered = filter_html(
        ["task:medium-range", "provider:nvidia"],
        definitions,
        {},
        "#aaa",
        "rounded",
        {},
    )
    assert "Medium Range Forecast" in rendered
    assert "MRF" not in rendered
    assert "provider:nvidia" not in rendered


def test_parse_options_supports_quoted_values():
    ids, options = parse_options('stable area:core mode=or label="Release candidate"')
    assert ids == ["stable", "area:core"]
    assert options == {"mode": "or", "label": "Release candidate"}


def test_parse_badge_id_only_splits_first_colon():
    assert parse_badge_id("area:api:v2") == ("area", "api:v2")


def test_grouped_filter_renders_rows_and_options():
    rendered = filter_html(
        ["area:core", "stability:stable"],
        {},
        {"area": {"label": "Area", "tooltip": "Functional area"}},
        "#aaa",
        "rounded",
        {"mode": "or", "order": "fixed", "toggle": "true", "hidden": "area"},
    )
    assert 'data-grouped="true"' in rendered
    assert 'data-filter-mode="or"' in rendered
    assert 'data-badge-order="area:core,stability:stable"' in rendered
    assert 'data-groups-hidden="area"' in rendered
    assert "Functional area" in rendered
    assert rendered.count("mkdocs-badge-filter__toggle") == 2
