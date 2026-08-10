import subprocess
import sys
from pathlib import Path

from bs4 import BeautifulSoup


def test_zensical_site_feature_parity(tmp_path: Path):
    docs = tmp_path / "docs"
    api = docs / "api"
    api.mkdir(parents=True)
    (api / "stable.md").write_text(
        """---
title: Stable API
summary: Production-ready operations. Additional implementation details should not appear.
badges: [stability:stable, area:core]
---
# Stable API
""",
        encoding="utf-8",
    )
    (api / "experimental.md").write_text(
        """---
title: Experimental API
summary: An API that may change.
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

<!-- mkdocs-badges:filter stability:stable area:core mode=or toggle=true -->

{% autosummary %}
api/stable.md
api/experimental.md
{% endautosummary %}

<!-- mkdocs-badges:end -->
""",
        encoding="utf-8",
    )
    (tmp_path / "zensical.toml").write_text(
        """[project]
site_name = "Test"
docs_dir = "docs"
site_dir = "site"

[project.markdown_extensions."mkdocs_badges.zensical"]
style = "square"

[project.markdown_extensions."mkdocs_badges.zensical".group_labels.stability]
label = "Stability"

[project.markdown_extensions."mkdocs_badges.zensical".group_labels.area]
label = "Area"

[project.markdown_extensions."mkdocs_badges.zensical".definitions."stability:stable"]
label = "Stable"
color = "#198754"
text_color = "#fff"

[project.markdown_extensions."mkdocs_badges.zensical".definitions."stability:experimental"]
label = "Experimental"
color = "#ffc107"
text_color = "#000"

[project.markdown_extensions."mkdocs_badges.zensical".definitions."area:core"]
label = "Core"
color = "#6f42c1"
text_color = "#fff"

[project.markdown_extensions."mkdocs_badges.zensical".definitions."area:utils"]
label = "Utils"
color = "#fd7e14"
text_color = "#fff"
""",
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "-m", "zensical", "build", "--clean"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    output = (tmp_path / "site/index.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(output, "html.parser")
    assert len(soup.select(".mkdocs-badge")) == 9
    assert soup.select_one(".mkdocs-badge-filter[data-grouped='true']")
    assert len(soup.select("table.mkdocs-badges-autosummary tbody tr")) == 2
    assert soup.select_one("a[href='api/stable/']")
    assert (
        "Production-ready operations."
        in soup.select_one("table.mkdocs-badges-autosummary").get_text()
    )
    assert "Additional implementation details" not in output
    assert len(soup.select("script[data-mkdocs-badges-bootstrap]")) == 1
    assert len(soup.select("script[data-mkdocs-badges-runtime]")) == 1
    assert '"api/stable/": ["stability:stable", "area:core"]' in output
    assert "{% autosummary" not in output
    assert "mkdocs-badges--no-text-selection" in output


def test_zensical_deduplicates_explicit_page_badges(tmp_path: Path):
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
    (tmp_path / "zensical.toml").write_text(
        """[project]
site_name = "Test"

[project.markdown_extensions."mkdocs_badges.zensical"]
style = "square"
""",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "zensical", "build", "--clean"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    soup = BeautifulSoup((tmp_path / "site/index.html").read_text(encoding="utf-8"), "html.parser")
    assert len(soup.select(".mkdocs-badge-list")) == 1
    assert len(soup.select(".mkdocs-badge")) == 3
