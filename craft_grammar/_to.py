# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2017, 2018, 2022 Canonical Ltd.
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

"""To Statement for Craft Grammar."""

import re
from typing import cast

from overrides import overrides

from ._base_processor import BaseProcessor
from ._statement import CallStack, Grammar, Statement
from .errors import ToStatementSyntaxError

_SELECTOR_PATTERN = re.compile(r"\Ato\s+([^,\s](?:,?[^,]+)*)\Z")
_WHITESPACE_PATTERN = re.compile(r"\A.*\s.*\Z")


class ToStatement(Statement):
    """Process a 'to' statement in the grammar."""

    def __init__(
        self,
        *,
        to_statement: str,
        body: Grammar,
        processor: BaseProcessor,
        call_stack: CallStack | None = None,
    ) -> None:
        """Create a ToStatement instance.

        :param to_statement: The 'to <selectors>' part of the clause.
        :param list body: The body of the clause.
        :param GrammarProcessor process: GrammarProcessor to use for processing
                                         this statement.
        :param list call_stack: Call stack leading to this statement.
        :param target_arch: the architecture the system is to build for.
        """
        super().__init__(body=body, processor=processor, call_stack=call_stack)

        self.selectors = _extract_to_clause_selectors(to_statement)

    @overrides
    def check(self) -> bool:
        # The only selector currently supported is the target arch. Since
        # selectors are matched with an AND, not OR, there should only be one
        # selector.
        return (len(self.selectors) == 1) and (
            self._processor.target_arch in self.selectors
        )

    def __eq__(self, other: object) -> bool:
        if type(other) is type(self):
            return self.selectors == cast(ToStatement, other).selectors

        return False

    def __str__(self) -> str:
        return f"to {', '.join(sorted(self.selectors))}"


def _extract_to_clause_selectors(to_statement: str) -> set[str]:
    """Extract the list of selectors within a to clause.

    :param to_statement: The 'to <selector>' part of the 'to' clause.

    :return: Selectors found within the 'to' clause.

    For example:
    >>> _extract_to_clause_selectors('to amd64,i386') == {'amd64', 'i386'}
    True
    """
    match = _SELECTOR_PATTERN.match(to_statement)
    if match is None:
        raise ToStatementSyntaxError(to_statement, message="selectors are missing")

    try:
        selector_group = match.group(1)
    except IndexError as index_error:
        raise ToStatementSyntaxError(to_statement) from index_error

    # This could be part of the _SELECTOR_PATTERN, but that would require us
    # to provide a very generic error when we can try to be more helpful.
    if _WHITESPACE_PATTERN.match(selector_group):
        raise ToStatementSyntaxError(
            to_statement,
            message="spaces are not allowed in the selectors",
        )

    return {selector.strip() for selector in selector_group.split(",")}
