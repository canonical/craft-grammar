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
from typing import Any, Dict, List, Union

from overrides import overrides

_on_pattern = re.compile(r"^on\s+(.+)\s*$")
_to_pattern = re.compile(r"^to\s+(.+)\s*$")
_compound_pattern = re.compile(r"^on\s+(.+)\s+to\s+(.+)\s*$")

_ELSE_FAIL = "else fail"
_ELSE = "else"
_TRY = "try"


_GrammarType = Dict[str, Any]


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


# Public types for grammar-enabled attributes
class GrammarBool(_GrammarBase):
    """Grammar-enabled bool field."""

    __root__: Union[bool, _GrammarType]

    @classmethod
    @overrides
    def validate(cls, entry):
        # GrammarBool entry can be a list if it contains clauses
        if isinstance(entry, list):
            new_entry = []
            for item in entry:
                if _is_grammar_clause(item):
                    cls._grammar_append(new_entry, item)
                else:
                    raise TypeError(f"value must be a list of bool: {entry!r}")
            return new_entry

        if isinstance(entry, bool):
            return entry

        raise TypeError(f"value must be a bool: {entry!r}")


class GrammarInt(_GrammarBase):
    """Grammar-enabled integer field."""

    __root__: Union[int, _GrammarType]

    @classmethod
    @overrides
    def validate(cls, entry):
        # GrammarInt entry can be a list if it contains clauses
        if isinstance(entry, list):
            new_entry = []
            for item in entry:
                if _is_grammar_clause(item):
                    cls._grammar_append(new_entry, item)
                else:
                    raise TypeError(f"value must be a list of integer: {entry!r}")
            return new_entry

        if isinstance(entry, int):
            return entry

        raise TypeError(f"value must be a integer: {entry!r}")


class GrammarFloat(_GrammarBase):
    """Grammar-enabled float field."""

    __root__: Union[float, _GrammarType]

    @classmethod
    @overrides
    def validate(cls, entry):
        # GrammarFloat entry can be a list if it contains clauses
        if isinstance(entry, list):
            new_entry = []
            for item in entry:
                if _is_grammar_clause(item):
                    cls._grammar_append(new_entry, item)
                else:
                    raise TypeError(f"value must be a list of float: {entry!r}")
            return new_entry

        if isinstance(entry, (int, float)):
            return float(entry)

        raise TypeError(f"value must be a float: {entry!r}")


class GrammarStr(_GrammarBase):
    """Grammar-enabled string field."""

    __root__: Union[str, _GrammarType]

    @classmethod
    @overrides
    def validate(cls, entry):
        # GrammarStr entry can be a list if it contains clauses
        if isinstance(entry, list):
            new_entry = []
            for item in entry:
                if _is_grammar_clause(item):
                    cls._grammar_append(new_entry, item)
                else:
                    raise TypeError(f"value must be a string: {entry!r}")
            return new_entry

        if isinstance(entry, str):
            return entry

        raise TypeError(f"value must be a string: {entry!r}")


class GrammarStrList(_GrammarBase):
    """Grammar-enabled list of strings field."""

    __root__: Union[List[Union[str, _GrammarType]], _GrammarType]

    @classmethod
    @overrides
    def validate(cls, entry):
        # GrammarStrList will always be a list
        if isinstance(entry, list):
            new_entry = []
            for item in entry:
                if _is_grammar_clause(item):
                    cls._grammar_append(new_entry, item)
                elif isinstance(item, str):
                    new_entry.append(item)
                else:
                    raise TypeError(f"value must be a list of string: {entry!r}")
            return new_entry

        raise TypeError(f"value must be a list of string: {entry!r}")


class GrammarSingleEntryDictList(_GrammarBase):
    """Grammar-enabled list of dictionaries field."""

    __root__: Union[List[Dict[str, Any]], _GrammarType]

    @classmethod
    @overrides
    def validate(cls, entry):
        # GrammarSingleEntryDictList will always be a list
        if isinstance(entry, list):
            new_entry = []
            for item in entry:
                if _is_grammar_clause(item):
                    cls._grammar_append(new_entry, item)
                elif isinstance(item, dict) and len(item) == 1:
                    new_entry.append(item)
                else:
                    raise TypeError(
                        f"value must be a list of single-entry dictionaries: {entry!r}"
                    )
            return new_entry

        raise TypeError(f"value must be a list of single-entry dictionaries: {entry!r}")


class GrammarDict(_GrammarBase):
    """Grammar-enabled dictionary field."""

    __root__: Union[Dict[str, Any], _GrammarType]

    @classmethod
    @overrides
    def validate(cls, entry):
        # GrammarDict entry can be a list if it contains clauses
        if isinstance(entry, list):
            new_entry = []
            for item in entry:
                if _is_grammar_clause(item):
                    cls._grammar_append(new_entry, item)
                else:
                    raise TypeError(f"value must be a list of dictionaries: {entry!r}")
            return new_entry

        if isinstance(entry, dict):
            return entry

        raise TypeError(f"value must be a dictionary: {entry!r}")


class GrammarDictList(_GrammarBase):
    """Grammar-enabled list of dictionary field."""

    __root__: Union[List[Dict[str, Any]], _GrammarType]

    @classmethod
    @overrides
    def validate(cls, entry):
        # GrammarDictList will always be a list
        if isinstance(entry, list):
            new_entry = []
            for item in entry:
                if _is_grammar_clause(item):
                    cls._grammar_append(new_entry, item)
                elif isinstance(item, dict):
                    new_entry.append(item)
                else:
                    raise TypeError(f"value must be a list of dictionaries: {entry!r}")
            return new_entry

        raise TypeError(f"value must be a list of dictionary: {entry!r}")


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
