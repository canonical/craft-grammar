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

"""Craft Grammar's Processor implementation."""

import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from ._compound import CompoundStatement
from ._on import OnStatement
from ._statement import CallStack, Grammar, Statement
from ._to import ToStatement
from ._try import TryStatement
from .errors import GrammarSyntaxError

_ON_TO_CLAUSE_PATTERN = re.compile(r"(\Aon\s+\S+)\s+(to\s+\S+\Z)")
_ON_CLAUSE_PATTERN = re.compile(r"\Aon\s+")
_TO_CLAUSE_PATTERN = re.compile(r"\Ato\s+")
_TRY_CLAUSE_PATTERN = re.compile(r"\Atry\Z")
_ELSE_CLAUSE_PATTERN = re.compile(r"\Aelse\Z")
_ELSE_FAIL_PATTERN = re.compile(r"\Aelse\s+fail\Z")


class GrammarProcessor:  # pylint: disable=too-few-public-methods
    """The GrammarProcessor extracts desired primitives from grammar."""

    def __init__(
        self,
        *,
        checker: Callable[[Any], bool],
        arch: str,
        target_arch: str,
        transformer: Optional[Callable[[List[Statement], str, str], str]] = None,
    ) -> None:
        """Create a new GrammarProcessor.

        :param checker: callable accepting a single primitive,
                        returning true if it is valid.
        :param arch: the architecture the system is on.
        :param target_arch: the architecture the system is to build for.
        :param transformer: callable accepting a call stack, single
                            primitive and arch, and returning a
                            transformed primitive.
        """
        self.arch = arch
        self.target_arch = target_arch
        self.checker = checker

        if transformer:
            self._transformer = transformer
        else:
            # By default, no transformation
            self._transformer = lambda s, p, o: p

    def process(
        self, *, grammar: Grammar, call_stack: Optional[CallStack] = None
    ) -> List[Any]:
        """Process grammar and extract desired primitives.

        :param grammar: Unprocessed grammar.
        :param call_stack: Call stack of statements leading to now.

        :return: Primitives selected
        """
        if call_stack is None:
            call_stack = []

        primitives: List[Any] = []
        statements = _StatementCollection()
        statement: Optional[Statement] = None

        for section in grammar:
            if isinstance(section, str):
                # If the section is just a string, it's either "else fail" or a
                # primitive name.
                if _ELSE_FAIL_PATTERN.match(section):
                    _handle_else(statement, None)
                else:
                    # Processing a string primitive indicates the previous section
                    # is finalized (if any), process it first before this primitive.
                    self._process_statement(
                        statement=statement,
                        statements=statements,
                        primitives=primitives,
                    )
                    statement = None

                    primitive = self._transformer(call_stack, section, self.target_arch)
                    primitives.append(primitive)
            elif isinstance(section, dict):
                statement, finalized_statement = self._parse_section_dictionary(
                    call_stack=call_stack,
                    section=section,
                    statement=statement,
                )

                # Process any finalized statement (if any).
                if finalized_statement is not None:
                    self._process_statement(
                        statement=finalized_statement,
                        statements=statements,
                        primitives=primitives,
                    )

                # If this section does not belong to a statement, it is
                # a primitive to be recorded.
                if statement is None:
                    primitives.append(section)

            elif isinstance(section, (int | float | bool | list)):
                # If the section is a number, boolean, or list, it's a primitive.
                primitives.append(section)
            else:
                # jsonschema should never let us get here.
                raise GrammarSyntaxError(
                    "expected grammar section to be either of type 'str' or "
                    f"type 'dict', but got {type(section)!r}"
                )

        # Process the final statement (if any).
        self._process_statement(
            statement=statement,
            statements=statements,
            primitives=primitives,
        )

        return primitives

    @staticmethod
    def _process_statement(
        *,
        statement: Optional[Statement],
        statements: "_StatementCollection",
        primitives: List[Any],
    ):
        if statement is None:
            return

        statements.add(statement)
        processed_primitives = statement.process()
        primitives.extend(processed_primitives)

    def _parse_section_dictionary(
        self,
        *,
        section: Dict[str, Any],
        statement: Optional[Statement],
        call_stack: CallStack,
    ) -> Tuple[Optional[Statement], Optional[Statement]]:
        finalized_statement: Optional[Statement] = None
        for key, value in section.items():
            # Grammar is always written as a list of selectors but the value
            # can be a list or a string. In the latter case we wrap it so no
            # special care needs to be taken when fetching the result from the
            # primitive.
            if not isinstance(value, list):
                value = [value]

            on_to_clause_match = _ON_TO_CLAUSE_PATTERN.match(key)
            on_clause_match = _ON_CLAUSE_PATTERN.match(key)
            if on_to_clause_match:
                # We've come across the beginning of a compound statement
                # with both 'on' and 'to'.
                finalized_statement = statement

                # First, extract each statement's part of the string
                on_statement, to_statement = on_to_clause_match.groups()

                # Now create a list of statements, in order
                compound_statements = [
                    OnStatement(
                        on_statement=on_statement,
                        # body is not used here
                        body=value,
                        processor=self,
                        call_stack=call_stack,
                    ),
                    ToStatement(
                        to_statement=to_statement,
                        # body is not used here
                        body=value,
                        processor=self,
                        call_stack=call_stack,
                    ),
                ]

                # Now our statement is a compound statement
                statement = CompoundStatement(
                    statements=compound_statements,
                    body=value,
                    processor=self,
                    call_stack=call_stack,
                )

            elif on_clause_match:
                # We've come across the beginning of an 'on' statement.
                # That means any previous statement we found is complete.
                finalized_statement = statement

                statement = OnStatement(
                    on_statement=key,
                    body=value,
                    processor=self,
                    call_stack=call_stack,
                )

            # TODO remove support for to without on (this statement)
            elif _TO_CLAUSE_PATTERN.match(key):
                # We've come across the beginning of a 'to' statement.
                # That means any previous statement we found is complete.
                finalized_statement = statement

                statement = ToStatement(
                    to_statement=key,
                    body=value,
                    processor=self,
                    call_stack=call_stack,
                )

            elif _TRY_CLAUSE_PATTERN.match(key):
                # We've come across the beginning of a 'try' statement.
                # That means any previous statement we found is complete.
                finalized_statement = statement

                statement = TryStatement(
                    body=value, processor=self, call_stack=call_stack
                )

            elif _ELSE_CLAUSE_PATTERN.match(key):
                _handle_else(statement, value)
            else:
                # Since this section is a dictionary, if there are no
                # markers to indicate the start or change of statement,
                # the current statement is complete and this section
                # is a primitive to be collected.
                finalized_statement = statement
                statement = None

        return statement, finalized_statement


def _handle_else(statement: Optional[Statement], else_body: Optional[Grammar]):
    """Add else body to current statement.

    :param statement: The currently-active statement. If None it will be
                      ignored.
    :param else_body: The body of the else clause to add.

    :raises GrammarSyntaxError: If there isn't a currently-active
                                     statement.
    """
    if statement is None:
        raise GrammarSyntaxError(
            "'else' doesn't seem to correspond to an 'on' or 'try'"
        )

    statement.add_else(else_body)


class _StatementCollection:  # pylint: disable=too-few-public-methods
    """Unique collection of statements to run at a later time."""

    def __init__(self) -> None:
        self._statements: List[Statement] = []

    def add(self, statement: Optional[Statement]) -> None:
        """Add new statement to collection.

        :param statement: New statement.

        :raises GrammarSyntaxError: If statement is already in collection.
        """
        if not statement:
            return

        if statement in self._statements:
            raise GrammarSyntaxError(
                f"found duplicate {str(statement)!r} statements. These should be merged."
            )

        self._statements.append(statement)
