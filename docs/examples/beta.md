---
badges:
  - stability:beta
  - area:core
  - platform:python
signature: (records, *, validate=True)
summary: Process a collection with an API approaching stability.
---

# Beta processor

`beta_processor` validates and transforms a collection of records. The main
interface is settled, but edge-case behavior may still change.

## Example

```python
result = beta_processor(records, validate=True)
```

## Maturity

- Appropriate for controlled production trials.
- Migration notes accompany any breaking beta changes.
- Expected to become stable after broader validation.
