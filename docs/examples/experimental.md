---
badges:
  - stability:experimental
  - area:math
  - platform:python
signature: (field, method="spectral")
summary: Try a spectral helper whose behavior may change between releases.
---

# Experimental helper

`experimental_helper` explores a faster spectral transformation path. Its
interface and numerical behavior may change as the implementation matures.

## Example

```python
result = experimental_helper(field, method="spectral")
```

## What “experimental” means

- Useful for evaluation and prototypes.
- Not yet covered by compatibility guarantees.
- Feedback may directly influence the final interface.

The badges above are also used by every page list and autosummary that links to
this page.
