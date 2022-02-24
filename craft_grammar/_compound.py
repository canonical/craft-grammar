# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2018, 2022 Canonical Ltd.
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

"""Compound Statement for Craft Grammar."""

from typing import TYPE_CHECKING, List, Optional

from overrides import overrides

from ._statement import CallStack, Grammar, Statement

if TYPE_CHECKING:
    from ._processor import GrammarProcessor


class CompoundStatement(Statement):
    """Multiple statements that need to be treated as a group."""

    def __init__(
        self,
        *,
        statements: List[Statement],
        body: Grammar,
        processor: "GrammarProcessor",
        call_stack: Optional[CallStack] = None,
    ) -> None:
        """Create an CompoundStatement instance.

        :param statements: List of compound statements
        :param body: The body of the clause.
        :param processor: GrammarProcessor to use for processing this statement.
        :param call_stack: Call stack leading to this statement.
        """
        super().__init__(body=body, processor=processor, call_stack=call_stack)

        self.statements = statements

    @overrides
    def check(self) -> bool:
        for statement in self.statements:
            if not statement.check():
                return False

        return True

    def __eq__(self, other) -> bool:
        if type(other) is type(self):
            return self.statements == other.statements

        return False

    def __str__(self) -> str:
        representation = ""
        for statement in self.statements:
            representation += f"{statement!s} "

        return representation.strip()
