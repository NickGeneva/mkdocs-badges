# mkdocs-badges

Material-friendly status badges and interactive filters for MkDocs.

{% badges stability:stable area:core platform:python %}

The plugin is a Markdown-native translation of `sphinx-badges`: page front
matter replaces Sphinx's document environment, shortcodes replace roles and
directives, and a build-generated badge index connects filtered links to pages.

## Quick example

This sentence contains an inline {% badge stability:experimental %} badge.

<!-- mkdocs-badges:filter stability:stable stability:experimental area:core area:utils mode=or order=fixed toggle=true hidden=area -->

- [Stable transform](examples/stable.md)
- [Experimental helper](examples/experimental.md)

<!-- mkdocs-badges:end -->

Use the controls above to filter the linked pages. Reveal the Area chips with
the group visibility control.
