# sphinx/conf.py
import sys
from pathlib import Path

from sphinx_pyproject import SphinxConfig

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
config = SphinxConfig(str(ROOT / "pyproject.toml"), globalns=globals())
