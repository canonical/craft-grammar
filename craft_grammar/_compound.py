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

from typing import cast

from overrides import overrides

from ._base_processor import BaseProcessor
from ._statement import CallStack, Grammar, Statement


class CompoundStatement(Statement):
    """Multiple statements that need to be treated as a group."""

    def __init__(
        self,
        *,
        statements: list[Statement],
        body: Grammar,
        processor: BaseProcessor,
        call_stack: CallStack | None = None,
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
        return all(statement.check() for statement in self.statements)

    def __eq__(self, other: object) -> bool:
        if type(other) is type(self):
            return self.statements == cast(CompoundStatement, other).statements

        return False

    def __str__(self) -> str:
        representation = ""
        for statement in self.statements:
            representation += f"{statement!s} "

        return representation.strip()
