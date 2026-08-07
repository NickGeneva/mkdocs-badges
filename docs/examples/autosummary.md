# Autosummary filtering

This table is generated from the front matter of the target Markdown pages. It
is the MkDocs-native counterpart to a Sphinx autosummary table.

<!-- mkdocs-badges:filter area:core area:math area:utils stability:stable stability:beta stability:experimental stability:deprecated mode=or order=fixed toggle=true hidden=area -->

{% autosummary %}
examples/stable.md
examples/beta.md
examples/experimental.md
examples/deprecated.md
{% endautosummary %}

<!-- mkdocs-badges:end -->

The Area chips start hidden. Open the Area eye to reveal them, or use the Area
filter buttons while the chips remain hidden. Filtering and chip visibility are
independent states.

## Share a filtered view

Selecting or clearing filter badges updates the page URL without reloading. Copy
the address from the browser to share the current result set. For example, this
URL opens the table with the Stable and Core filters already selected:

[Open a pre-filtered autosummary](?badge=stability%3Astable&badge=area%3Acore)

The plugin uses one repeated `badge` query parameter per selection and preserves
other query parameters and any URL fragment.
