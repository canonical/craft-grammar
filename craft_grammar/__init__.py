# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2022 Canonical Ltd.
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
"""Enhance project definitions with advanced grammar."""

from . import errors
from ._compound import CompoundStatement
from ._on import OnStatement
from ._processor import GrammarProcessor
from ._statement import CallStack, Grammar, Statement
from ._to import ToStatement
from ._try import TryStatement
from .create import create_grammar_model

try:
    from ._version import __version__
except ImportError:  # pragma: no cover
    from importlib.metadata import version, PackageNotFoundError

    try:
        __version__ = version("craft-grammar")
    except PackageNotFoundError:
        __version__ = "dev"

__all__ = [
    "__version__",
    "errors",
    "CallStack",
    "CompoundStatement",
    "Grammar",
    "GrammarProcessor",
    "OnStatement",
    "Statement",
    "ToStatement",
    "TryStatement",
    "create_grammar_model",
]
