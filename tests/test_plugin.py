from pathlib import Path

import yaml
from bs4 import BeautifulSoup
from mkdocs.commands.build import build
from mkdocs.config import load_config


def test_material_site_build(tmp_path: Path):
    docs = tmp_path / "docs"
    examples = docs / "examples"
    examples.mkdir(parents=True)
    (examples / "stable.md").write_text(
        """---
title: Stable API
description: Production-ready operations.
signature: (value)
badges: [stability:stable, area:core]
---
# Stable API
""",
        encoding="utf-8",
    )
    (examples / "experimental.md").write_text(
        """---
title: Experimental API
description: An API that may change.
badges: [stability:experimental, area:utils]
---
# Experimental API
""",
        encoding="utf-8",
    )
    (docs / "index.md").write_text(
        """---
badges: [stability:stable, area:core]
---
# Home

Inline {% badge stability:stable label="Ready" %}.

<!-- mkdocs-badges:filter stability:stable stability:experimental area:core area:utils mode=or order=fixed toggle=true hidden=area -->

{% autosummary %}
examples/stable.md
examples/experimental.md
{% endautosummary %}

<!-- mkdocs-badges:end -->

```markdown
{% badge stable %}
```
""",
        encoding="utf-8",
    )
    config_file = tmp_path / "mkdocs.yml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "site_name": "Test",
                "docs_dir": str(docs),
                "site_dir": str(tmp_path / "site"),
                "theme": {"name": "material"},
                "plugins": [
                    {"badges": {"group_labels": {"stability": "Stability", "area": "Area"}}}
                ],
            }
        ),
        encoding="utf-8",
    )
    build(load_config(config_file=str(config_file)))

    output = (tmp_path / "site/index.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(output, "html.parser")
    assert len(soup.select(".mkdocs-badge")) == 11
    assert soup.select_one(".mkdocs-badge-filter[data-grouped='true']")
    assert len(soup.select("table.mkdocs-badges-autosummary tbody tr")) == 2
    assert soup.select_one("a[href='examples/stable/']")
    assert soup.select_one("code").get_text() == "Stable API"
    assert not soup.select_one("table.mkdocs-badges-autosummary thead")
    summary_badges = soup.select_one("table.mkdocs-badges-autosummary td .mkdocs-badge-list")
    assert "mkdocs-badge-list--summary" in summary_badges["class"]
    assert soup.select_one(".mkdocs-badge-filter__eye-open svg")
    assert soup.select_one(".mkdocs-badge-filter__eye-closed svg")
    assert "{% badge stable %}" in output
    data = (tmp_path / "site/assets/javascripts/mkdocs-badges-data.js").read_text()
    assert "window.MKDOCS_BADGES=" in data
    assert '"examples/stable/": ["stability:stable", "area:core"]' in data
    assert '"definitions"' in data
    assert (tmp_path / "site/assets/stylesheets/mkdocs-badges.css").is_file()
    assert (tmp_path / "site/assets/javascripts/mkdocs-badges.js").is_file()


def test_inline_autosummary_and_glob(tmp_path: Path):
    docs = tmp_path / "docs"
    (docs / "api").mkdir(parents=True)
    (docs / "index.md").write_text(
        "# Index\n\n{% autosummary api/*.md badges=false headers=true signatures=long %}\n",
        encoding="utf-8",
    )
    (docs / "api/item.md").write_text(
        "---\ntitle: Item\nsummary: Short description.\nbadges: [stable]\n---\n# Item\n",
        encoding="utf-8",
    )
    config_file = tmp_path / "mkdocs.yml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "site_name": "Test",
                "docs_dir": str(docs),
                "site_dir": str(tmp_path / "site"),
                "plugins": ["badges"],
            }
        ),
        encoding="utf-8",
    )
    build(load_config(config_file=str(config_file)))
    soup = BeautifulSoup((tmp_path / "site/index.html").read_text(encoding="utf-8"), "html.parser")
    row = soup.select_one("table.mkdocs-badges-autosummary tbody tr")
    assert row.select_one("a")["href"] == "api/item/"
    assert row.select_one("td:nth-child(2)").get_text() == "Short description."
    assert not row.select_one(".mkdocs-badge")
    assert soup.select_one("thead th").get_text() == "API"
