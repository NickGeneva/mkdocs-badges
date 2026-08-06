# Usage

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

## Inline and block badges

```markdown
Inline {% badge stability:stable %}

Custom label {% badge stability:stable label="Production ready" %}

{% badges stability:stable area:core %}
```

## Filters

A filter uses HTML comments so the enclosed content remains ordinary Markdown:

```markdown
<!-- mkdocs-badges:filter stability:stable area:core mode=or -->

- [An API page](api/page.md)

<!-- mkdocs-badges:end -->
```

Filters understand linked Markdown lists, table rows, and mkdocstrings
`.doc-object` elements. Put a badge shortcode in a mkdocstrings object's rendered
docstring to label that object.

Grouped filters use OR within a group and AND across groups. For example,
selecting both `stability:stable` and `stability:beta`, plus `area:core`, means
“stable or beta, and core.”

Options are placed after the badge IDs:

```markdown
<!-- mkdocs-badges:filter area:core stability:stable mode=or order=fixed toggle=true hidden="area" -->
```

- `mode=and|or`: matching for ungrouped filters
- `order=fixed`: canonical badge display order
- `toggle=true`: group chip visibility controls
- `hidden="group1 group2"`: initially hidden chip groups
