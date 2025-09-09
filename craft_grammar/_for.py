# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2025 Canonical Ltd.
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

"""For Statement for Craft Grammar."""

import re
from typing import cast

from overrides import overrides

from ._base_processor import BaseProcessor
from ._statement import CallStack, Grammar, Statement
from .errors import ForStatementSyntaxError, GrammarSyntaxError

# captures the selector 'platform1' from 'for platform1'
_SELECTOR_PATTERN = re.compile(r"\Afor\s+(.+)\Z")

# matches any whitespace in the selector
_WHITESPACE_PATTERN = re.compile(r"\A.*\s.*\Z")

# matches any comma in the selector
_COMMA_PATTERN = re.compile(r"\A.*,.*\Z")


class ForStatement(Statement):
    """Process a 'for' statement in the grammar."""

    def __init__(
        self,
        *,
        for_statement: str,
        body: Grammar,
        processor: BaseProcessor,
        call_stack: CallStack | None = None,
    ) -> None:
        """Create a ForStatement instance.

        :param for_statement: The 'for <selectors>' part of the clause.
        :param body: The body of the clause.
        :param processor: GrammarProcessor to use for processing
                                         this statement.
        :param call_stack: Call stack leading to this statement.
        """
        super().__init__(body=body, processor=processor, call_stack=call_stack)

        self.selectors = _extract_for_clause_selectors(for_statement)

    @overrides
    def check(self) -> bool:
        return (
            self._processor.platforms is not None
            and (len(self.selectors) == 1)
            and (self.selectors.issubset(self._processor.platforms))
        )

    @overrides
    def add_else(
        self,
        else_body: Grammar | None,  # noqa: ARG002 (unused-argument)
    ) -> None:
        """Raise an error for 'else' usage.

        The 'for' statement doesn't support 'else'.

        :raises GrammarSyntaxError: When called.
        """
        raise GrammarSyntaxError("'else' is not supported for 'for'")

    def __eq__(self, other: object) -> bool:
        if type(other) is type(self):
            return self.selectors == cast(ForStatement, other).selectors

        return False

    def __str__(self) -> str:
        return f"for {', '.join(sorted(self.selectors))}"


def _extract_for_clause_selectors(for_statement: str) -> set[str]:
    """Extract the selectors within a 'for' clause.

    For example:
    >>> _extract_for_clause_selectors("for my-platform") == {"my-platform"}
    True

    :param for_statement: The 'for <selector>' part of the 'for' clause.

    :return: Selectors found within the 'for' clause. Only one selector is allowed,
    so a single element set is returned.

    :raises ForStatementSyntaxError: If the use of 'for' can't be determined.
    """
    match = _SELECTOR_PATTERN.match(for_statement)
    if match is None:
        raise ForStatementSyntaxError(for_statement, message="selector is missing")

    try:
        selector_group = match.group(1)
    except IndexError as index_error:
        raise ForStatementSyntaxError(for_statement) from index_error

    # This could be part of the _SELECTOR_PATTERN, but that would require us
    # to provide a very generic error when we can try to be more helpful.
    if _WHITESPACE_PATTERN.match(selector_group):
        raise ForStatementSyntaxError(
            for_statement,
            message="spaces are not allowed in the selector",
        )

    # Raise a friendly error for commas since other grammar statements allow commas.
    if _COMMA_PATTERN.match(selector_group):
        raise ForStatementSyntaxError(
            for_statement,
            message="multiple selectors are not allowed",
        )

    return {selector_group.strip()}
