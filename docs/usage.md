# Usage

## Zensical setup (default)

Add the Python Markdown extension to `zensical.toml`. All badge configuration
lives directly beneath the extension:

```toml
[project.markdown_extensions."mkdocs_badges.zensical"]
style = "square"
page_badges = true
selectable_text = false
autosummary_root = "modules/generated"
catalog_path = "assets/mkdocs-badges/catalog.json"

[project.markdown_extensions."mkdocs_badges.zensical".definitions."stability:stable"]
label = "Stable"
color = "#198754"
text_color = "#fff"

[project.markdown_extensions."mkdocs_badges.zensical".definitions."provider:nvidia"]
label = "NV"
name = "NVIDIA"
tooltip = "NVIDIA provider"
hide_in = ["autosummary"]
```

Run `zensical serve` while authoring and `zensical build --clean` for production.
The extension embeds its small CSS, JavaScript, and page badge index so no
manual asset configuration is necessary.

## MkDocs compatibility

Existing MkDocs projects can continue to configure `plugins: [badges]` in
`mkdocs.yml`. The Markdown syntax and rendered behavior are identical on both
backends.

## Page badges

Add `badges` to a page's YAML front matter:

```yaml
---
badges: [stability:stable, area:core]
---
```

The plugin displays these badges beneath the first H1 by default. Set
`page_badges: false` in the plugin configuration to index them without rendering
them at the page title.

A definition can set `hidden = true` (`hidden: true` in YAML) to use a badge as
a classifier without displaying its chip. Hidden classifiers remain in page
metadata, autosummary row `data-badge-ids`, filtering state, and generated
catalog data, but are omitted from page titles, shortcodes, tables, linked-list
annotations, and filter controls.

For scope-specific visibility, use `hide_in` with any combination of `page`,
`autosummary`, and `filter`. For example, `hide_in = ["autosummary"]` keeps a
provider classifier on its full API page and in catalog/filter metadata while
omitting its chip from autosummary rows. Visibility never removes the classifier
from `data-badge-ids` or catalog data, so it can still match filters and power
custom catalogs.

Use `name` for the full human-readable identity while keeping `label` compact:

```toml
[project.markdown_extensions."mkdocs_badges.zensical".definitions."task:medium-range"]
label = "MRF"
name = "Medium Range Forecast"
tooltip = "Medium Range Forecast"
```

Page and autosummary chips use `label`. Filter controls and catalog consumers
use `name`, falling back to `tooltip` and then `label`. `display_name` is
accepted as an alias for `name`.

Badge and filter-control text is non-selectable by default, which prevents the
browser's text-selection highlight from appearing during interaction. Set
`selectable_text: true` if readers should be able to select and copy that text:

```yaml
plugins:
  - badges:
      selectable_text: true
```

## Inline and block badges

```markdown
Inline {% badge stability:stable %}

Custom label {% badge stability:stable label="Production ready" %}

{% badges stability:stable area:core %}
```

## Autosummary tables

Generate a two-column API summary from existing Markdown pages. Titles,
descriptions, badges, and final HTML links come from each page's front matter
and documentation metadata. Like Sphinx autosummary, descriptions are limited
to the first sentence of `summary`, `description`, or the first body paragraph.
Badges always render on their own line beneath the linked API name:

```markdown
{% autosummary %}
api/transform.md
api/regrid.md
{% endautosummary %}
```

The compact form supports paths, globs, and options:

```markdown
{% autosummary api/*.md headers=true title="Object" description="Summary" signatures=long %}
```

Entries can also be Python API symbols, so one RST-style object list can drive
both API-page generation and the rendered table:

```markdown
{% autosummary %}
perturbation.Brown
perturbation.BredVector
perturbation.CorrelatedSphericalGaussian
{% endautosummary %}
```

Generated pages should declare their canonical import name in front matter:

```yaml
title: perturbation.Brown
symbol: earth2studio.perturbation.Brown
summary: Lat/Lon 2D brown noise.
```

Resolution first checks `symbol`, `api_name`, `object`, or `import_path`
metadata, then a dotted page title, and finally a generated filename such as
`perturbation_Brown.md`. Both full and package-relative symbols are accepted.
Bare object names are intentionally not inferred, and an ambiguous match is
omitted with a build warning instead of linking to the wrong page. Existing
page paths and globs continue to work unchanged.

Set `badges=false` to omit badges. Signatures are hidden by default; use
`signatures=short` for `(…)` or `signatures=long` for the full front-matter
`signature`. Set `headers=true` to add an explicit header row.

`autosummary_root` defaults to `modules/generated`, so an entry can use
`models/px/AIFS2ENS.md` instead of the complete docs-root path. If the rooted
entry does not exist, the original docs-root-relative entry is tried, preserving
ordinary paths such as `api/transform.md`. This option is available in both
`zensical.toml` and the MkDocs `badges` plugin configuration. Set it to an empty
string to disable the root, or begin an entry with `/` to bypass it for that row.

## Filters

A filter uses HTML comments so the enclosed content remains ordinary Markdown:

```markdown
<!-- mkdocs-badges:filter stability:stable area:core mode=or -->

- [An API page](api/page.md)

<!-- mkdocs-badges:end -->
```

Filters understand generated autosummary tables, linked Markdown lists, ordinary
table rows, and mkdocstrings `.doc-object` elements. Put a badge shortcode in a
mkdocstrings object's rendered docstring to label that object.

Grouped filters use OR within a group and AND across groups. For example,
selecting both `stability:stable` and `stability:beta`, plus `area:core`, means
“stable or beta, and core.”

Filter selections are reflected in the URL as repeated `badge` query
parameters. Opening that URL restores the filtered view, making it possible to
bookmark or share a specific result set:

```text
https://docs.example.com/api/?badge=stability%3Astable&badge=area%3Acore
```

The URL is updated without a page reload. Unrelated query parameters and the
fragment identifier are preserved, and clearing the filter removes the `badge`
parameters.

## Catalog data

Every build writes `assets/mkdocs-badges/catalog.json` by default. It contains a
`catalog` array with each page's source path, output URL, canonical symbol,
title, first-sentence summary, signature, and complete `classifiers` list, plus all badge
`definitions`, including their `name`, `hidden`, and `hide_in` state. This
provides a stable input for
custom card, tile, or cross-API catalog interfaces without coupling them to the
autosummary table markup.

Set `catalog_path` to another site-relative path, or to an empty string to
disable the standalone JSON file. The same catalog is also available at runtime
as `window.MKDOCS_BADGES.catalog`.

Options are placed after the badge IDs:

```markdown
<!-- mkdocs-badges:filter area:core stability:stable mode=or order=fixed toggle=true hidden="area" -->
```

- `mode=and|or`: matching for ungrouped filters
- `order=fixed`: canonical badge display order
- `toggle=true`: group chip visibility controls
- `hidden="group1 group2"`: initially hidden chip groups
