import json
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
description: Production-ready operations. Additional implementation details should not appear.
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
    assert (
        "Production-ready operations."
        in soup.select_one("table.mkdocs-badges-autosummary").get_text()
    )
    assert "Additional implementation details" not in output
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
    assert '"selectable_text": false' in data
    assert (tmp_path / "site/assets/stylesheets/mkdocs-badges.css").is_file()
    assert (tmp_path / "site/assets/javascripts/mkdocs-badges.js").is_file()


def test_equivalent_manual_badge_list_suppresses_page_badges(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(
        """---
badges: [region:global, class:mrf, year:2026]
---
# AIFS2

{% badges year:2026 region:global class:mrf %}
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
                "plugins": ["badges"],
            }
        ),
        encoding="utf-8",
    )
    build(load_config(config_file=str(config_file)))

    soup = BeautifulSoup((tmp_path / "site/index.html").read_text(encoding="utf-8"), "html.parser")
    lists = soup.select(".mkdocs-badge-list")
    assert len(lists) == 1
    assert [badge["data-badge-id"] for badge in lists[0].select(".mkdocs-badge")] == [
        "year:2026",
        "region:global",
        "class:mrf",
    ]


def test_inline_autosummary_and_glob(tmp_path: Path):
    docs = tmp_path / "docs"
    (docs / "api").mkdir(parents=True)
    (docs / "index.md").write_text(
        "# Index\n\n{% autosummary *.md badges=false headers=true signatures=long %}\n",
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
                "plugins": [
                    {
                        "badges": {
                            "selectable_text": True,
                            "autosummary_root": "api",
                        }
                    }
                ],
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
    assert row["data-render-badges"] == "false"
    assert soup.select_one("thead th").get_text() == "API"
    data = (tmp_path / "site/assets/javascripts/mkdocs-badges-data.js").read_text()
    assert '"selectable_text": true' in data


def test_hidden_classifier_is_indexed_without_rendering(tmp_path: Path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text(
        """---
title: Catalog item
summary: A catalog entry.
badges: [provider:nvidia]
---
# Catalog item

{% badge provider:nvidia %}
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
                "plugins": [
                    {
                        "badges": {
                            "definitions": {"provider:nvidia": {"label": "NVIDIA", "hidden": True}}
                        }
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    build(load_config(config_file=str(config_file)))

    output = (tmp_path / "site/index.html").read_text(encoding="utf-8")
    assert 'data-badge-id="provider:nvidia"' not in output
    data = (tmp_path / "site/assets/javascripts/mkdocs-badges-data.js").read_text()
    assert '"provider:nvidia"' in data
    assert '"hidden": true' in data
    catalog = json.loads(
        (tmp_path / "site/assets/mkdocs-badges/catalog.json").read_text(encoding="utf-8")
    )
    assert catalog["catalog"][0]["classifiers"] == ["provider:nvidia"]
    assert catalog["definitions"]["provider:nvidia"]["hidden"] is True
    assert catalog["definitions"]["provider:nvidia"]["name"] == "NVIDIA"


def test_badge_can_be_hidden_from_autosummary_but_visible_on_api_page(tmp_path: Path):
    docs = tmp_path / "docs"
    api = docs / "api"
    api.mkdir(parents=True)
    (docs / "index.md").write_text(
        "# Catalog\n\n{% autosummary %}\n/api/item.md\n{% endautosummary %}\n",
        encoding="utf-8",
    )
    (api / "item.md").write_text(
        "---\ntitle: Item\nsummary: API item.\n"
        "badges: [provider:nvidia, task:medium-range]\n---\n# Item\n",
        encoding="utf-8",
    )
    config_file = tmp_path / "mkdocs.yml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "site_name": "Test",
                "docs_dir": str(docs),
                "site_dir": str(tmp_path / "site"),
                "plugins": [
                    {
                        "badges": {
                            "definitions": {
                                "provider:nvidia": {
                                    "label": "NV",
                                    "name": "NVIDIA",
                                    "hide_in": ["autosummary"],
                                },
                                "task:medium-range": {
                                    "label": "MRF",
                                    "name": "Medium Range Forecast",
                                },
                            }
                        }
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    build(load_config(config_file=str(config_file)))

    catalog_page = BeautifulSoup(
        (tmp_path / "site/index.html").read_text(encoding="utf-8"), "html.parser"
    )
    api_page = BeautifulSoup(
        (tmp_path / "site/api/item/index.html").read_text(encoding="utf-8"), "html.parser"
    )
    row = catalog_page.select_one("table.mkdocs-badges-autosummary tbody tr")
    assert row["data-badge-ids"] == "provider:nvidia,task:medium-range"
    assert row["data-render-badges"] == "true"
    assert [badge.get_text(strip=True) for badge in row.select(".mkdocs-badge")] == ["MRF"]
    assert "Medium Range Forecast" not in row.get_text()
    assert not row.select_one('[data-badge-id="provider:nvidia"]')
    assert api_page.select_one('[data-badge-id="provider:nvidia"]')
    catalog = json.loads(
        (tmp_path / "site/assets/mkdocs-badges/catalog.json").read_text(encoding="utf-8")
    )
    definition = catalog["definitions"]["provider:nvidia"]
    assert definition["name"] == "NVIDIA"
    assert definition["hide_in"] == ["autosummary"]


def test_autosummary_resolves_python_api_symbols(tmp_path: Path):
    docs = tmp_path / "docs"
    generated = docs / "modules/generated/perturbation/1"
    generated.mkdir(parents=True)
    (docs / "index.md").write_text(
        """# Perturbations

{% autosummary %}
perturbation.Brown
perturbation.BredVector
{% endautosummary %}
""",
        encoding="utf-8",
    )
    (generated / "perturbation_Brown.md").write_text(
        """---
title: perturbation.Brown
symbol: earth2studio.perturbation.Brown
summary: Lat/Lon 2D brown noise.
---
# `perturbation.Brown`
""",
        encoding="utf-8",
    )
    (generated / "perturbation_BredVector.md").write_text(
        """---
title: perturbation.BredVector
summary: Bred vector perturbation.
---
# `perturbation.BredVector`
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
                "plugins": ["badges"],
            }
        ),
        encoding="utf-8",
    )
    build(load_config(config_file=str(config_file)))

    soup = BeautifulSoup((tmp_path / "site/index.html").read_text(), "html.parser")
    links = soup.select("table.mkdocs-badges-autosummary a")
    assert [link.get_text(strip=True) for link in links] == [
        "perturbation.Brown",
        "perturbation.BredVector",
    ]
    assert links[0]["href"] == "modules/generated/perturbation/1/perturbation_Brown/"
    catalog = json.loads(
        (tmp_path / "site/assets/mkdocs-badges/catalog.json").read_text(encoding="utf-8")
    )
    brown = next(item for item in catalog["catalog"] if item["title"] == "perturbation.Brown")
    assert brown["symbol"] == "earth2studio.perturbation.Brown"
