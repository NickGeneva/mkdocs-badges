# Manual table filtering

This table is ordinary Markdown. The filter resolves each link to its real
MkDocs output page, reads that page's badge metadata, and filters the rows.

<!-- mkdocs-badges:filter stability:stable stability:beta stability:experimental stability:deprecated area:core area:math area:utils mode=or toggle=true -->

| API | Purpose |
| --- | --- |
| [Stable transform](stable.md) | Production-ready field transformation |
| [Beta processor](beta.md) | Validated record processing |
| [Experimental helper](experimental.md) | Spectral transformation research |
| [Deprecated formatter](deprecated.md) | Legacy compatibility formatting |

<!-- mkdocs-badges:end -->

Try selecting `Stable` and `Beta`, then add `Core`. The first selection broadens
within Stability; the second narrows across Area.
