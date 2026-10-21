"""What a stranger gets from `pip install serve-return`.

The first wheel built for PyPI carried four nested copies of stale build
output and a top-level `tests` package, because the line that limits
discovery to `serve_return` sat under package-data, where setuptools
reads it as data for a package named "include". Nothing failed: the
package imported fine from the repository. This pins the two lines that
decide what ships.
"""

from __future__ import annotations

import tomllib
from pathlib import Path

PYPROJECT = Path(__file__).resolve().parents[1] / "pyproject.toml"


def test_only_the_package_is_discovered_and_the_model_ships_with_it():
    cfg = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["tool"]["setuptools"]
    assert cfg["packages"]["find"]["include"] == ["serve_return*"]
    assert cfg["package-data"] == {"serve_return": ["models/*.json", "models/NOTICE.md"]}


def test_the_model_ships_with_its_own_licence_and_says_so_in_the_metadata():
    """The weights are trained on CHILDES, which TalkBank shares under CC
    BY-NC-SA 3.0. The code is MIT; the model file is not, and the package
    metadata and the notice beside the file both say so."""
    meta = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
    assert "CC BY-NC-SA 3.0" in meta["license"]["text"] and "MIT" in meta["license"]["text"]
    notice = (PYPROJECT.parent / "serve_return" / "models" / "NOTICE.md").read_text(encoding="utf-8")
    assert "CC BY-NC-SA 3.0" in notice and "10.21415/T5101R" in notice and "MacWhinney" in notice


def test_the_shipped_model_is_where_package_data_says():
    model = PYPROJECT.parent / "serve_return" / "models" / "childes_roles.json"
    assert model.is_file() and model.stat().st_size > 100_000
