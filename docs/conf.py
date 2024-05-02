# Copyright 2023-2024 Canonical Ltd.
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

import datetime

project = "Craft Grammar"
author = "Canonical Group Ltd"

copyright = "2022-%s, %s" % (datetime.date.today().year, author)

# region Configuration for canonical-sphinx
ogp_site_url = "https://canonical-craft-grammar.readthedocs-hosted.com/"
ogp_site_name = project
ogp_image = "https://assets.ubuntu.com/v1/253da317-image-document-ubuntudocs.svg"

html_context = {
    "product_page": "github.com/canonical/craft-grammar",
    "github_url": "https://github.com/canonical/craft-grammar",
}

extensions = [
    "canonical_sphinx",
]
# endregion

extensions.extend(
    [
        "sphinx.ext.autodoc",
    ]
)

# region Options for extensions

# Type hints configuration
set_type_checking_flag = True
typehints_fully_qualified = False
always_document_param_types = True
typehints_document_rtype = True

# Github config
github_username = "canonical"
github_repository = "craft-application"

# endregion


def run_apidoc(_):
    import os
    import sys

    from sphinx.ext.apidoc import main

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    cur_dir = os.path.abspath(os.path.dirname(__file__))
    module = os.path.join(cur_dir, "..", "craft_grammar")
    main(["-e", "-o", cur_dir, module, "--no-toc", "--force"])


def setup(app):
    app.connect("builder-inited", run_apidoc)
