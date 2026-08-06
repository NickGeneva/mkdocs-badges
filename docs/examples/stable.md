---
badges:
  - stability:stable
  - area:core
  - platform:python
signature: (field, scale=1)
summary: Apply a production-ready transform to a field.
---

# Stable transform

`stable_transform` is the production-ready path for scaling a field while
preserving its shape and metadata.

## Example

```python
result = stable_transform(field, scale=2)
```

## Behavior

- Preserves the input grid and coordinates.
- Accepts scalar integer or floating-point scale values.
- Covered by the compatibility policy for future releases.

This page is tagged through front matter. Its title, signature, summary, final
HTML URL, and badges are consumed automatically by `{% autosummary %}` tables.
