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

"""Try Statement for Craft Grammar."""


from overrides import overrides

from ._base_processor import BaseProcessor
from ._statement import CallStack, Grammar, Statement


class TryStatement(Statement):
    """Process a 'try' statement in the grammar.

    For example:
    >>> from snapcraft_legacy import ProjectOptions
    >>> from ._processor import GrammarProcessor
    >>> def checker(primitive):
    ...     return 'invalid' not in primitive
    >>> options = ProjectOptions()
    >>> processor = GrammarProcessor(None, options, checker)
    >>> clause = TryStatement(body=['invalid'], processor=processor)
    >>> clause.add_else(['valid'])
    >>> clause.process()
    {'valid'}
    """

    def __init__(
        self,
        *,
        body: Grammar,
        processor: BaseProcessor,
        call_stack: CallStack | None = None,
    ) -> None:
        """Create a TryStatement instance.

        :param body: The body of the clause.
        :param processor: GrammarProcessor to use for processing
                                         this statement.
        :param call_stack: Call stack leading to this statement.
        """
        super().__init__(
            body=body,
            processor=processor,
            call_stack=call_stack,
            check_primitives=True,
        )

    @overrides
    def check(self) -> bool:
        return self._validate_primitives(self._process_body())

    def __eq__(self, other: object) -> bool:
        return False

    def __str__(self) -> str:
        return "try"
