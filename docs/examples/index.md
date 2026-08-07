# Interactive examples

These examples mirror the three workflows demonstrated by `sphinx-badges`, but
use native MkDocs pages and HTML instead of Sphinx nodes or autosummary.

## Try the filters

Select multiple stability badges to broaden the result. Then select an Area
badge to narrow it. The rule is **OR within a group, AND across groups**.

<!-- mkdocs-badges:filter stability:stable stability:beta stability:experimental stability:deprecated area:core area:math area:utils mode=or order=fixed toggle=true -->

{% autosummary %}
examples/stable.md
examples/beta.md
examples/experimental.md
examples/deprecated.md
{% endautosummary %}

<!-- mkdocs-badges:end -->

The eye beside each group only hides or reveals that group's badge chips. It
does not change which rows match the active filters.

## Focused demonstrations

- [Manual table filtering](manual.md) shows that no generated table is required.
- [Autosummary filtering](autosummary.md) demonstrates paths, globs, signatures,
  summaries, and final MkDocs URLs.
- [API object filtering](api-objects.md) demonstrates member-level badges like
  the Sphinx autodoc example.
- [Explicit page badge list](deduplication.md) mirrors generated API pages that
  use frontmatter metadata and a manually positioned equivalent list without
  rendering duplicate badges.
