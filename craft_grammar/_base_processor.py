# Copyright 2024 Canonical Ltd.
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
"""Base abstraction for a grammar processor."""

import abc
from collections.abc import Callable, Collection
from typing import Any

from craft_grammar.errors import PlatformNameError

from ._types import Grammar


class BaseProcessor(abc.ABC):
    """Base abstraction for a grammar processor."""

    checker: Callable[[Any], bool]

    def __init__(
        self,
        arch: str,
        target_arch: str,
        platforms: Collection[str] | None = None,
        *,
        valid_platforms: Collection[str] | None = None,
        valid_architectures: Collection[str] | None = None,
    ) -> None:
        self.arch = arch
        self.target_arch = target_arch
        if platforms and "any" in platforms:
            raise PlatformNameError("any")
        self.platforms = None if platforms is None else {"any"} | set(platforms)
        self.valid_platforms = valid_platforms
        self.valid_architectures = valid_architectures

    @abc.abstractmethod
    def process(
        self,
        *,
        grammar: Grammar,
        call_stack: Any | None = None,  # noqa: ANN401 (any-type)
    ) -> list[Any]:
        """Process grammar and extract desired primitives.

        :param grammar: Unprocessed grammar.
        :param call_stack: Call stack of statements leading to now.

        :return: Primitives selected
        """
