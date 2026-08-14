# mkdocs-badges

Zensical-first status badges, autosummaries, and interactive content filters,
with a compatible MkDocs plugin for existing projects. This is the Markdown
counterpart of [sphinx-badges](https://github.com/NickGeneva/sphinx-badges).

Attach coloured badges to pages or any inline Markdown, then filter linked pages,
tables, lists, and mkdocstrings API objects by badge group. The plugin supports
Zensical's modern and classic variants, Material light/dark palettes, responsive
layouts, print output, and instant navigation.

## Installation

```bash
pip install mkdocs-badges
```

Add the native Python Markdown extension to `zensical.toml`:

```toml
[project.markdown_extensions."mkdocs_badges.zensical"]
style = "rounded"
selectable_text = false
autosummary_root = "modules/generated"
catalog_path = "assets/mkdocs-badges/catalog.json"

[project.markdown_extensions."mkdocs_badges.zensical".group_labels.stability]
label = "Stability"
tooltip = "API stability level"

[project.markdown_extensions."mkdocs_badges.zensical".definitions."stability:stable"]
label = "Stable"
color = "#198754"
text_color = "#fff"

[project.markdown_extensions."mkdocs_badges.zensical".definitions."provider:nvidia"]
label = "NV"
name = "NVIDIA"
hide_in = ["autosummary"]
```

`stable`, `beta`, `experimental`, `deprecated`, and `new` have built-in colours,
so configuration is optional. `style` can be `rounded`, `square`, or `pill`.
Badge text selection is disabled by default to avoid selection highlights while
interacting; set `selectable_text: true` to allow selecting and copying it.

Preview and build with Zensical:

```bash
zensical serve
zensical build --clean
```

### MkDocs compatibility

The existing MkDocs plugin remains supported. Configure the same options under
`plugins.badges` in `mkdocs.yml` and use the same Markdown syntax:

```yaml
plugins:
  - search
  - badges:
      style: rounded
      selectable_text: false
      autosummary_root: modules/generated
      catalog_path: assets/mkdocs-badges/catalog.json
      definitions:
        stability:stable:
          label: Stable
          color: "#198754"
          text_color: "#fff"
        provider:nvidia:
          label: NV
          name: NVIDIA
          hide_in: [autosummary]
```

## Usage

Tag a page in its front matter. Its badges are shown below the first H1 and made
available to filters that link to that page:

```markdown
---
badges:
  - stability:stable
  - area:core
---

# Fast transform
```

Use a badge inline or render several together:

```markdown
This API is {% badge stability:stable %}.

{% badges stability:stable area:core %}

Override visible text with {% badge stability:stable label="Production ready" %}.
```

Generate an autosummary-style table directly from MkDocs pages:

```markdown
{% autosummary %}
api/stable.md
api/experimental.md
{% endautosummary %}
```

The list may instead contain Python API symbols, matching Sphinx autosummary:

```markdown
{% autosummary %}
perturbation.Brown
perturbation.BredVector
{% endautosummary %}
```

Give each generated page a canonical `symbol` in its front matter (for example,
`symbol: earth2studio.perturbation.Brown`). Package-relative symbols are also
recognized, so the same autosummary block can be the single list consumed by a
separate API-page generator and by mkdocs-badges when it renders the table.

Each row uses the target page's `title`, `summary` or `description`, and `badges`
metadata. Badges render on their own line beneath the API name. Paths and globs
are supported, and links are resolved through the active documentation engine so
they point at the actual generated HTML page. `autosummary_root` defaults to
`modules/generated`, allowing shorter entries beneath that directory while
falling back to the original docs-root path when needed. Set it to an empty
string to disable the root, or prefix an entry with `/` to bypass it. Signatures
are optional with `signatures=short|long`.

Set `hidden = true` on a badge definition to keep it as a classifier without
rendering a visual chip. Hidden classifiers still participate in indexing and
filter matching. Use `hide_in: [page, autosummary, filter]` to suppress visual
chips only in selected contexts. A compact `label` can be paired with a full
human-readable `name`; filter controls and catalog interfaces prefer `name`,
then `tooltip`, then `label`. Filters containing autosummary tables automatically
use compact `label` values instead; override this with `labels=label|name` on
the filter marker. Builds also produce
`assets/mkdocs-badges/catalog.json` with
page symbols, titles, summaries, URLs, signatures, and complete classifier lists for
custom card or tile catalogs; configure or disable this with `catalog_path`.

Wrap an autosummary, Markdown list, ordinary table, or mkdocstrings output in
filter markers:

```markdown
<!-- mkdocs-badges:filter stability:stable stability:experimental area:core mode=or -->

{% autosummary api/*.md %}

<!-- mkdocs-badges:end -->
```

When every ID has a `group:name` prefix, selections are ORed within each group
and ANDed across groups. For a flat list, `mode=and` (the default) or `mode=or`
controls matching.

Filter options mirror the useful parts of `sphinx-badges`:

- `mode=and|or` sets flat-filter matching.
- `order=fixed` displays chips in the order listed by the filter.
- `toggle=true` adds an open/closed eye control for each group.
- `hidden="area platform"` starts those groups with their chips hidden.

Shortcodes inside fenced code blocks are left untouched. Badge labels, tooltip
attributes, and inline label overrides are escaped; configured `icon` values may
contain trusted HTML so Material icons or Font Awesome markup can be used.

## How filtering finds badges

The extension records page-level `badges` metadata and every real output URL during
the build. Autosummary rows are rendered with their badges immediately; linked
list items and ordinary table rows are annotated in the browser. A mkdocstrings
`.doc-object` is filtered from badge shortcodes rendered inside that object. This
keeps the authoring model native to MkDocs: front matter labels pages, while
shortcodes label finer-grained API members.

## Development

```bash
uv sync --extra test --extra docs
uv run pytest
uv run zensical build --clean
uv run mkdocs build --strict
```

## Licence

MIT
