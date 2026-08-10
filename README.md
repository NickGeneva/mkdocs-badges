# mkdocs-badges

Material-friendly status badges and interactive content filters for
[MkDocs](https://www.mkdocs.org/). This is the MkDocs counterpart of
[sphinx-badges](https://github.com/NickGeneva/sphinx-badges).

Attach coloured badges to pages or any inline Markdown, then filter linked pages,
tables, lists, and mkdocstrings API objects by badge group. The plugin supports
Material's light/dark palettes, responsive layouts, print output, and instant
navigation.

## Installation

```bash
pip install mkdocs-badges
```

Add the plugin to `mkdocs.yml`:

```yaml
plugins:
  - search
  - badges:
      style: rounded
      selectable_text: false
      group_labels:
        stability:
          label: Stability
          tooltip: API stability level
        area: Area
      definitions:
        stability:stable:
          label: Stable
          color: "#198754"
          text_color: "#fff"
        stability:experimental:
          label: Experimental
          color: "#ffc107"
          text_color: "#000"
          icon: 🧪
        area:core:
          label: Core
          color: "#6f42c1"
          text_color: "#fff"
```

`stable`, `beta`, `experimental`, `deprecated`, and `new` have built-in colours,
so configuration is optional. `style` can be `rounded`, `square`, or `pill`.
Badge text selection is disabled by default to avoid selection highlights while
interacting; set `selectable_text: true` to allow selecting and copying it.

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

Each row uses the target page's `title`, `summary` or `description`, and `badges`
metadata. Badges render on their own line beneath the API name. Paths and globs
are supported, and links are resolved through MkDocs so they point at the actual
generated HTML page. Signatures are optional with `signatures=short|long`.

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

The plugin records page-level `badges` metadata and every real output URL during
the build. Autosummary rows are rendered with their badges immediately; linked
list items and ordinary table rows are annotated in the browser. A mkdocstrings
`.doc-object` is filtered from badge shortcodes rendered inside that object. This
keeps the authoring model native to MkDocs: front matter labels pages, while
shortcodes label finer-grained API members.

## Development

```bash
uv sync --extra test --extra docs
uv run pytest
uv run mkdocs build --strict
```

## Licence

MIT
