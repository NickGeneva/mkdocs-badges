# mkdocs-badges

Material-friendly status badges and interactive filters for MkDocs.

{% badges stability:stable area:core platform:python %}

The plugin is a Markdown-native translation of `sphinx-badges`: page front
matter replaces Sphinx's document environment, shortcodes replace roles and
directives, and a build-generated badge index connects filtered links to pages.

## Quick example

This sentence contains an inline {% badge stability:experimental %} badge.

<!-- mkdocs-badges:filter stability:stable stability:beta stability:experimental stability:deprecated area:core area:math area:utils mode=or order=fixed toggle=true hidden=area -->

{% autosummary %}
examples/stable.md
examples/beta.md
examples/experimental.md
examples/deprecated.md
{% endautosummary %}

<!-- mkdocs-badges:end -->

Use the controls above to filter the generated summary table. The eye icon next
to each group hides or reveals that group's chips without changing the filter.
