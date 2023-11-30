#
# Copyright 2021 Canonical Ltd.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path("..").absolute()))

import craft_grammar  # noqa: E402

# -- Project information -----------------------------------------------------

project = "Craft Store"
copyright = "2021, Canonical Ltd."
author = "Canonical Ltd."

# The full version, including alpha/beta/rc tags
release = craft_grammar.__version__


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # "sphinx_toolbox.more_autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_design",
    "sphinx_copybutton",
    "sphinx-pydantic",
    "sphinx_toolbox",
    "sphinx.ext.autodoc",  # Must be loaded after more_autodoc
    "sphinx_autodoc_typehints",  # must be loaded after napoleon
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# region Options for HTML output
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output
html_theme = "furo"
html_static_path = ["_static"]
html_css_files = [
    "css/custom.css",
]

# Do (not) include module names.
add_module_names = True

# endregion
# region Options for extensions
# Intersphinx extension
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# sphinx_autodoc_typehints
set_type_checking_flag = True
typehints_fully_qualified = False
always_document_param_types = True
typehints_document_rtype = True

# Enable support for google-style instance attributes.
napoleon_use_ivar = True

# Type hints configuration
set_type_checking_flag = True
typehints_fully_qualified = False
always_document_param_types = True

# Github config
github_username = "canonical"
github_repository = "craft-grammar"

# endregion


# def run_apidoc(_):
#     import os
#     import sys
#
#     from sphinx.ext.apidoc import main
#
#     sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
#     cur_dir = os.path.abspath(os.path.dirname(__file__))
#     module = os.path.join(cur_dir, "..", "craft_grammar")
#     main(["-e", "-o", cur_dir, module, "--no-toc", "--force"])


# def setup(app):
#     app.connect("builder-inited", run_apidoc)
