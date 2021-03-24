# flake8: noqa
# pylint: skip-file
# Configuration file for the Sphinx documentation builder.

#
# -- Path setup --------------------------------------------------------------
#

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))


#
# -- Project information -----------------------------------------------------
#

project = "Extract Management 2.0"
copyright = "2020, Riverside Healthcare"
author = "Riverside Healthcare"

version = "2.0.0"
release = version

#
# -- General configuration ---------------------------------------------------
#

extensions = [
    "sphinx.ext.extlinks",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "sphinx_copybutton",
    "sphinx_inline_tabs",
    "sphinx_panels",
    "myst_parser",
    "autoapi.extension",
]

autoapi_type = "python"
autoapi_dirs = ["../em_web", "../em_scheduler", "../em_runner"]

autoapi_options = [
    "members",
    "inherited-members",
    "private-members",
    "special-members",
    "show-inheritance",
    "show-inheritiance-diagram",
    "show-module-summary",
]

autoapi_keep_files = False
autoapi_python_class_content = "both"
autoapi_ignore = ["*config*", "*flask_simpleldap*"]

templates_path = ["_templates"]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", "venv"]

pygments_style = "colorful"

#
# -- Options for HTML output -------------------------------------------------
#

html_theme = "furo"
html_title = "Extract Management 2.0"
html_logo = "images/icon-512x512.png"
html_favicon = "images/favicon.ico"

html_theme_options = {
    "sidebar_hide_name": True,
}

html_static_path = ["_static"]
html_css_files = ["custom.css"]
