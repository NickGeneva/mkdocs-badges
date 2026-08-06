# API object filtering

This example mirrors member-level filtering in the Sphinx autodoc demo. Each
object carries its own badges, so filtering does not depend on another page.

<!-- mkdocs-badges:filter stability:stable stability:beta stability:experimental stability:deprecated area:core area:math area:utils mode=or toggle=true -->

<div class="doc-object doc-function mkdocs-badge-demo-object" data-badge-ids="stability:stable,area:core" markdown>
## `transform(field, scale=1)`

{% badges stability:stable area:core %}

Scale a field using the production implementation.
</div>

<div class="doc-object doc-function mkdocs-badge-demo-object" data-badge-ids="stability:beta,area:core" markdown>
## `process(records, validate=True)`

{% badges stability:beta area:core %}

Validate and process a record collection.
</div>

<div class="doc-object doc-function mkdocs-badge-demo-object" data-badge-ids="stability:experimental,area:math" markdown>
## `spectral_transform(field)`

{% badges stability:experimental area:math %}

Evaluate the experimental spectral implementation.
</div>

<div class="doc-object doc-function mkdocs-badge-demo-object" data-badge-ids="stability:deprecated,area:utils" markdown>
## `format_legacy(value)`

{% badges stability:deprecated area:utils %}

Format a value through the compatibility layer.
</div>

<!-- mkdocs-badges:end -->
