# sphinx/conf.py
import sys
from pathlib import Path

import sphinx.ext.autodoc as _autodoc

# Patch for sphinx-click: import mock in Sphinx >= 9.0
import sphinx.ext.autodoc.mock as _mock_module

if not hasattr(_autodoc, "mock"):
    _autodoc.mock = _mock_module.mock

from sphinx_pyproject import SphinxConfig

html_theme = "furo"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
config = SphinxConfig(str(ROOT / "pyproject.toml"), globalns=globals())
