# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2017, 2022 Canonical Ltd.
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

"""Statement definition for Craft Grammar."""

from abc import ABCMeta, abstractmethod
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Sequence, Union

from . import errors

Grammar = Sequence[Union[str, Dict[str, Any]]]
"""Grammar type."""
CallStack = List["Statement"]
"""CallStack type."""

if TYPE_CHECKING:
    from . import GrammarProcessor


class Statement(metaclass=ABCMeta):
    """Base class for all grammar statements."""

    def __init__(
        self,
        *,
        body: Grammar,
        processor: "GrammarProcessor",
        call_stack: Optional[CallStack],
        check_primitives: bool = False
    ) -> None:
        """Create an Statement instance.

        :param body: The body of the clause.
        :param processor: GrammarProcessor to use for processing
                        this statement.
        :param call_stack: call stack leading to this statement.
        :param arch: the architecture the system is on.
        :param check_primitives: whether or not the primitives should be
                                 checked for validity as part of
                                 evaluating the elses.
        """
        if call_stack:
            self.__call_stack = call_stack
        else:
            self.__call_stack = []

        self._body = body
        self._processor = processor
        self._check_primitives = check_primitives
        self._else_bodies: List[Optional[Grammar]] = []

        self.__processed_body: Optional[List[str]] = None
        self.__processed_else: Optional[List[str]] = None

    def add_else(self, else_body: Optional[Grammar]) -> None:
        """Add an 'else' clause to the statement.

        :param list else_body: The body of an 'else' clause.

        The 'else' clauses will be processed in the order they are added.
        """
        self._else_bodies.append(else_body)

    def process(self) -> List[str]:
        """Process this statement.

        :return: Primitives as determined by evaluating the statement or its
                 else clauses.
        """
        if self.check():
            primitives = self._process_body()
        else:
            primitives = self._process_else()

        return primitives

    def _process_body(self) -> List[str]:
        """Process the main body of this statement.

        :return: Primitives as determined by processing the main body.
        """
        if self.__processed_body is None:
            self.__processed_body = self._processor.process(
                grammar=self._body, call_stack=self._call_stack(include_self=True)
            )

        return self.__processed_body

    def _process_else(self) -> List[str]:
        """Process the else clauses of this statement in order.

        :return: Primitives as determined by processing the else clauses.
        """
        if self.__processed_else is not None:
            return self.__processed_else

        self.__processed_else = []
        for else_body in self._else_bodies:
            if not else_body:
                # Handle the 'else fail' case.
                raise errors.UnsatisfiedStatementError(str(self))

            processed_else = self._processor.process(
                grammar=else_body, call_stack=self._call_stack()
            )
            if processed_else:
                self.__processed_else = processed_else
                if not self._check_primitives or self._validate_primitives(
                    processed_else
                ):
                    break

        return self.__processed_else

    def _validate_primitives(self, primitives: Iterable[str]) -> bool:
        """Ensure that all primitives are valid.

        :param primitives: Iterable container of primitives.

        :return: Whether or not all primitives are valid.
        :rtype: bool
        """
        for primitive in primitives:
            if not self._processor.checker(primitive):
                return False
        return True

    def _call_stack(self, *, include_self=False) -> CallStack:
        """Return call stack when processing this statement.

        :param bool include_self: Whether or not this statement should be
                                  included in the stack.
        """
        call_stack = self.__call_stack
        if include_self:
            call_stack += [self]

        return call_stack

    def __repr__(self):
        return "{self.__str__()!r}"

    @abstractmethod
    def check(self) -> bool:
        """Check if a statement main body should be processed.

        :return: True if main body should be processed, False if elses should
                 be processed.
        """

    @abstractmethod
    def __eq__(self, other) -> bool:
        """Return if a statement is equal to another."""

    @abstractmethod
    def __str__(self) -> str:
        """Return the string representation of the statement."""
