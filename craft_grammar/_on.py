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

"""On Statement for Craft Grammar."""

import re
from typing import cast

from overrides import overrides

from ._base_processor import BaseProcessor
from ._statement import CallStack, Grammar, Statement
from .errors import OnStatementSyntaxError

_SELECTOR_PATTERN = re.compile(r"\Aon\s+([^,\s](?:,?[^,]+)*)\Z")
_WHITESPACE_PATTERN = re.compile(r"\A.*\s.*\Z")


class OnStatement(Statement):
    """Process an 'on' statement in the grammar."""

    def __init__(
        self,
        *,
        on_statement: str,
        body: Grammar,
        processor: BaseProcessor,
        call_stack: CallStack | None = None,
    ) -> None:
        """Create an OnStatement instance.

        :param on_statement: The 'on <selectors>' part of the clause.
        :param body: The body of the clause.
        :param processor: GrammarProcessor to use for processing
                                         this statement.
        :param call_stack: Call stack leading to this statement.
        :param arch: the architecture the system is on.
        """
        super().__init__(body=body, processor=processor, call_stack=call_stack)

        self.selectors = _extract_on_clause_selectors(on_statement)

    @overrides
    def check(self) -> bool:
        # The only selector currently supported is the host arch. Since
        # selectors are matched with an AND, not OR, there should only be one
        # selector.
        return (len(self.selectors) == 1) and (self._processor.arch in self.selectors)

    def __eq__(self, other: object) -> bool:
        if type(other) is type(self):
            return self.selectors == cast(OnStatement, other).selectors

        return False

    def __str__(self) -> str:
        return f"on {','.join(sorted(self.selectors))}"


def _extract_on_clause_selectors(on_statement: str) -> set[str]:
    """Extract the list of selectors within an on clause.

    :param str on_statement: The 'on <selector>' part of the 'on' clause.

    :return: Selectors found within the 'on' clause.

    For example:
    >>> _extract_on_clause_selectors('on amd64,i386') == {'amd64', 'i386'}
    True
    """
    match = _SELECTOR_PATTERN.match(on_statement)
    if match is None:
        raise OnStatementSyntaxError(on_statement, message="selectors are missing")

    try:
        selector_group = match.group(1)
    except IndexError as index_error:
        raise OnStatementSyntaxError(on_statement) from index_error

    # This could be part of the _SELECTOR_PATTERN, but that would require us
    # to provide a very generic error when we can try to be more helpful.
    if _WHITESPACE_PATTERN.match(selector_group):
        raise OnStatementSyntaxError(
            on_statement,
            message="spaces are not allowed in the selectors",
        )

    return {selector.strip() for selector in selector_group.split(",")}
