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

"""Pydantic models for grammar."""

import abc
import re
from typing import Any, Generic, List, TypeVar, get_args, get_origin

from overrides import overrides
from pydantic import BaseConfig, PydanticTypeError
from pydantic.validators import find_validators

_on_pattern = re.compile(r"^on\s+(.+)\s*$")
_to_pattern = re.compile(r"^to\s+(.+)\s*$")
_compound_pattern = re.compile(r"^on\s+(.+)\s+to\s+(.+)\s*$")

_ELSE_FAIL = "else fail"
_ELSE = "else"
_TRY = "try"


T = TypeVar("T")


class _GrammarBase(abc.ABC):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    @abc.abstractmethod
    def validate(cls, entry):
        """Ensure the given entry is valid type or grammar."""

    @classmethod
    def _grammar_append(cls, entry: List, item: Any) -> None:
        if item == _ELSE_FAIL:
            _mark_and_append(entry, item)
        else:
            key, value = tuple(item.items())[0]
            _mark_and_append(entry, {key: cls.validate(value)})


def _format_type_error(type_: type, entry: Any) -> str:
    """Format a type error message."""
    origin = get_origin(type_)
    args = get_args(type_)

    # handle primitive types which origin is None
    if not origin:
        origin = type_

    if issubclass(origin, list):
        if args:
            return f"value must be a list of {args[0].__name__}: {entry!r}"
        return f"value must be a list: {entry!r}"

    if issubclass(origin, dict):
        if len(args) == 2:
            return f"value must be a dict of {args[0].__name__} and {args[1].__name__}: {entry!r}"
        return f"value must be a dict: {entry!r}"

    return f"value must be a {type_.__name__}: {entry!r}"


class GrammarGeneratorMetaClass(type):
    """Grammar generator metaclass.

    Allows to use GrammarGenerator[T] to define a grammar-aware type.
    """

    # Define __getitem__ method to be able to use index
    def __getitem__(cls, type_):

        # pylint: disable=too-many-branches
        class GrammarScalar(_GrammarBase):
            """Grammar scalar class.

            Dynamically generated class to handle grammar-aware types.
            """

            _type = type_

            @classmethod
            @overrides
            def validate(cls, entry):
                # Grammar[T] entry can be a list if it contains clauses
                if isinstance(entry, list):
                    # Check if the type_ supposed to be a list
                    sub_type = get_args(cls._type)

                    # handle typed list
                    if sub_type:
                        sub_type = sub_type[0]
                        if sub_type is Any:
                            sub_type = None

                    new_entry = []
                    for item in entry:
                        # Check if the item is a valid grammar clause
                        if _is_grammar_clause(item):
                            cls._grammar_append(new_entry, item)
                        else:
                            # Check if the item is a valid type if not a grammar clause
                            if sub_type and isinstance(item, sub_type):
                                new_entry.append(item)
                            else:
                                raise TypeError(_format_type_error(cls._type, entry))

                    return new_entry

                # Not a valid grammar, check if it is a dict
                if isinstance(entry, dict):
                    # Check if the type_ supposed to be a dict
                    if get_origin(cls._type) is not dict:
                        raise TypeError(_format_type_error(cls._type, entry))

                    sub_type = get_args(cls._type)
                    # The dict is not a typed dict
                    if not sub_type:
                        return entry

                    sub_key_type = sub_type[0] if sub_type else Any
                    sub_value_type = sub_type[1] if sub_type else Any

                    # validate the dict
                    for key, value in entry.items():
                        if (sub_key_type is Any or isinstance(key, sub_key_type)) and (
                            sub_value_type is Any or isinstance(value, sub_value_type)
                        ):
                            # we do not need the return value if it is a valid dict
                            pass
                        else:
                            raise TypeError(_format_type_error(cls._type, entry))

                    return entry

                # handle standard types with pydantic validators
                try:
                    for validator in find_validators(cls._type, BaseConfig):
                        # we do not need the return value of the validator
                        validator(entry)
                except PydanticTypeError as err:
                    raise TypeError(_format_type_error(cls._type, entry)) from err

                return entry

        return GrammarScalar


class GrammarGenerator(Generic[T], metaclass=GrammarGeneratorMetaClass):
    """Grammar generator class.

    Allows to use GrammarGenerator[T] to define a grammar-aware type.

    GrammarGenerator[int]
    GrammarGenerator[list[str]]
    GrammarGenerator[dict[str, int]]

    """


def _ensure_selector_valid(selector: str, *, clause: str) -> None:
    """Verify selector syntax."""
    # spaces are not allowed in selector
    if " " in selector:
        raise ValueError(f"spaces are not allowed in {clause!r} selector")

    # selector items should be separated by comma
    if selector.startswith(",") or selector.endswith(",") or ",," in selector:
        raise ValueError(f"syntax error in {clause!r} selector")


def _is_grammar_clause(item: Any) -> bool:  # pylint: disable=too-many-return-statements
    """Check if the given item is a valid grammar clause."""
    # The 'else fail' clause is a string.
    if item == _ELSE_FAIL:
        return True

    # Other grammar clauses are single-entry dictionaries.
    if not isinstance(item, dict) or len(item) != 1:
        return False

    key = tuple(item.keys())[0]

    if not isinstance(key, str):
        return False

    # Do, or do not. There is no try.
    if key == _TRY:
        raise ValueError("'try' was removed from grammar, use 'on <arch>' instead")

    if key == _ELSE:
        return True

    res = _compound_pattern.match(key)
    if res:
        _ensure_selector_valid(res.group(1), clause="on ... to")
        _ensure_selector_valid(res.group(2), clause="on ... to")
        return True

    res = _on_pattern.match(key)
    if res:
        _ensure_selector_valid(res.group(1), clause="on")
        return True

    res = _to_pattern.match(key)
    if res:
        _ensure_selector_valid(res.group(1), clause="to")
        return True

    return False


def _mark_and_append(entry: List, item: Any) -> None:
    """Mark entry as parsed for testing and debug."""
    if isinstance(item, str):
        entry.append("*" + item)
    elif isinstance(item, dict):
        key, value = tuple(item.items())[0]
        entry.append({f"*{key}": value})
