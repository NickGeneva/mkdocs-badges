from mkdocs_badges.render import (
    badge_html,
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
