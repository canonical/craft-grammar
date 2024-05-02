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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Errors for Craft Grammar."""


class CraftGrammarError(Exception):
    """Base class error for craft-grammar."""


class GrammarSyntaxError(CraftGrammarError):
    """Error raised on grammar syntax errors."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Invalid grammar syntax: {message}.")


class OnStatementSyntaxError(GrammarSyntaxError):
    """Error raised on on statement syntax errors."""

    def __init__(self, on_statement: str, *, message: str | None = None) -> None:
        components = [f"{on_statement!r} is not a valid 'on' clause"]
        if message:
            components.append(message)
        super().__init__(message=": ".join(components))


class ToStatementSyntaxError(GrammarSyntaxError):
    """Error raised on to statement syntax errors."""

    def __init__(self, to_statement: str, *, message: str | None = None) -> None:
        components = [f"{to_statement!r} is not a valid 'to' clause"]
        if message:
            components.append(message)
        super().__init__(message=": ".join(components))


class UnsatisfiedStatementError(CraftGrammarError):
    """Error raised when a statement cannot be satisfied."""

    def __init__(self, statement: str) -> None:
        super().__init__(f"Unable to satisfy {statement!r}, failure forced.")
