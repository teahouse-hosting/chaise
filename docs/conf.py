# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Chaise"
copyright = "2024, Jamie Bliss, Piper Thunstrom"
author = "Jamie Bliss, Piper Thunstrom"
release = "0.0.1"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinxext.opengraph",
    "sphinx_inline_tabs",
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.httpdomain",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]


intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "couchdb": ("https://docs.couchdb.org/en/stable", None),
    # httpx
    "attrs": ("https://www.attrs.org/en/stable", None),
    "pydantic": ("https://docs.pydantic.dev/latest", None),
    "cattrs": ("https://catt.rs/en/stable", None),
}


autodoc_default_flags = ["members", "undoc-members", "show-inheritance"]

viewcode_line_numbers = True
