from pathlib import Path

import yaml
from bs4 import BeautifulSoup
from mkdocs.commands.build import build
from mkdocs.config import load_config


def test_material_site_build(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(
        """---
badges: [stability:stable, area:core]
---
# Home

Inline {% badge stability:stable label="Ready" %}.

<!-- mkdocs-badges:filter stability:stable area:core mode=or order=fixed toggle=true hidden=area -->

- [Home](./)

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
    config = load_config(config_file=str(config_file))
    build(config)

    output = (tmp_path / "site/index.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(output, "html.parser")
    # Two page badges, one inline badge, and two filter-button badges. The linked
    # page badges are cloned into the list item by JavaScript in the browser.
    assert len(soup.select(".mkdocs-badge")) == 5
    assert soup.select_one(".mkdocs-badge-filter[data-grouped='true']")
    assert "{% badge stable %}" in output
    data = (tmp_path / "site/assets/javascripts/mkdocs-badges-data.js").read_text()
    assert '"": ["stability:stable", "area:core"]' in data
    assert (tmp_path / "site/assets/stylesheets/mkdocs-badges.css").is_file()
    assert (tmp_path / "site/assets/javascripts/mkdocs-badges.js").is_file()
