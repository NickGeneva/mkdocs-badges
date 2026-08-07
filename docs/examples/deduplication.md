---
title: Explicit page badge list
summary: Frontmatter metadata with a manually positioned equivalent badge list.
badges: [stability:stable, area:core, platform:python]
---

# Explicit page badge list

{% badges platform:python stability:stable area:core %}

This page mirrors generated API documentation such as the Earth2Studio model
pages: its badges are declared in frontmatter for filtering and repeated as an
explicit list so the author controls their position. MkDocs Badges recognizes
that the two declarations are equivalent and renders only this one list.

```markdown
---
badges: [stability:stable, area:core, platform:python]
---

# Explicit page badge list

{% badges platform:python stability:stable area:core %}
```

The declaration order may differ. Deduplication compares badge identifiers, so
the page retains the order chosen by the explicit list.
