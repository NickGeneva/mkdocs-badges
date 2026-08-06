---
badges:
  - stability:deprecated
  - area:utils
  - platform:python
signature: (value)
summary: Format a value through the legacy compatibility path.
---

# Deprecated formatter

`deprecated_formatter` remains available for compatibility with older projects.
New code should use [`stable_transform`](stable.md) instead.

## Example

```python
text = deprecated_formatter(value)
```

## Migration

Replace formatter calls with the stable transformation API before the next
major release. The deprecated badge makes this status visible in every generated
summary and interactive filter.
