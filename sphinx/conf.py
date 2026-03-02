# sphinx/conf.py
import sys
from pathlib import Path

"""# Patch for sphinx-click: in Sphinx >= 9.0 mock moved to submodule
import sphinx_click.ext as _sc_ext  # noqa: E402
from sphinx.ext.autodoc.mock import mock as _mock_class  # noqa: E402

_sc_ext.mock = _mock_class"""

from sphinx_pyproject import SphinxConfig  # noqa: E402

html_theme = "furo"

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
config = SphinxConfig(str(ROOT / "pyproject.toml"), globalns=globals())
