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
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx_autodoc_typehints',
    'sphinx_click',
    'sphinx_copybutton'
]

copybutton_prompt_text = r"\$ |>>> "
copybutton_prompt_is_regexp = True

sphinx_click_mock_imports = []

# --- copybutton ---
copybutton_prompt_text = r"\$ |>>> "
copybutton_prompt_is_regexp = True

# --- autodoc ---
autodoc_member_order = 'bysource'
autodoc_typehints = 'description'
autodoc_typehints_format = 'short'
add_module_names = False

# --- sphinx-autodoc-typehints ---
typehints_fully_qualified = False
simplify_optional_unions = True

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

autodoc_default_options = {
    'members': True,
    'undoc-members': True,
    'show-inheritance': True,
}