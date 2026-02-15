import os
import sys

sys.path.insert(0, os.path.abspath('../'))

project = 'AstraGeek'
copyright = '2026, Ilia Bespyatyy, Maksim Ramenskiy'
author = 'Ilia Bespyatyy, Maksim Ramenskiy'
release = '0.2.0'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.githubpages',
    'sphinx.ext.napoleon',            # поддержка Google/NumPy docstrings (на будущее)
    'sphinx.ext.intersphinx',         # ссылки на документацию numpy, python
    'sphinx_autodoc_typehints',       # красивые типы
]

# --- autodoc настройки ---
autodoc_member_order = 'bysource'               # порядок как в исходнике
autodoc_typehints = 'description'                # типы в описание, НЕ в сигнатуру
autodoc_typehints_format = 'short'               # short: NDArray вместо numpy.ndarray[...]
add_module_names = False                         # angular_distance вместо src.helpers.geometry.geometry.angular_distance

# --- sphinx-autodoc-typehints ---
typehints_fully_qualified = False                # NDArray вместо numpy.typing.NDArray
simplify_optional_unions = True                  # Optional[X] вместо Union[X, None]

# --- intersphinx: ссылки на внешние проекты ---
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
    'numpy': ('https://numpy.org/doc/stable/', None),
    'matplotlib': ('https://matplotlib.org/stable/', None),
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'furo'
html_static_path = ['_static']