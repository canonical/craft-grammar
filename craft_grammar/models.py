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

import re
from typing import Any, Dict, List, Union

from overrides import overrides

_on_pattern = re.compile(r"^on\s+(.+)\s*$")
_to_pattern = re.compile(r"^to\s+(.+)\s*$")
_compound_pattern = re.compile(r"^on\s+(.+)\s+to\s+(.+)\s*$")


class _GrammarBase:
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, entry):
        """Transform 'on' and 'to' field names."""
        if not isinstance(entry, dict):
            return entry

        new_entry = {}
        for key, value in entry.items():
            # Do, or do not. There is no try.
            if key == "try":
                raise ValueError(
                    "'try' was removed from grammar, use 'on <arch>' instead"
                )

            # 'else fail' clause
            if key == "else fail":
                if value:
                    raise ValueError("'else fail' must have no arguments")
                new_entry[key] = None
                continue

            # 'else' clause
            if key == "else":
                new_entry[key] = cls.validate(value)
                continue

            # 'on ... to' clause
            res = _compound_pattern.match(key)
            if res:
                _ensure_selector_valid(res.group(1), clause="on ... to")
                _ensure_selector_valid(res.group(2), clause="on ... to")
                new_entry["to"] = cls.validate(value)
                continue

            # 'on' clause
            res = _on_pattern.match(key)
            if res:
                _ensure_selector_valid(res.group(1), clause="on")
                new_entry["on"] = cls.validate(value)
                continue

            # 'to' clause
            res = _to_pattern.match(key)
            if res:
                _ensure_selector_valid(res.group(1), clause="to")
                new_entry["to"] = cls.validate(value)
                continue

            raise ValueError(f"invalid grammar key {key!r}")

        return new_entry


def _ensure_selector_valid(selector: str, *, clause: str) -> None:
    # spaces are not allowed in selector
    if " " in selector:
        raise ValueError(f"spaces are not allowed in {clause!r} selector")

    # selector items should be separated by comma
    if selector.startswith(",") or selector.endswith(",") or ",," in selector:
        raise ValueError(f"syntax error in {clause!r} selector")


_GrammarType = Dict[str, Any]


# Public types for grammar-enabled attributes


class GrammarStr(_GrammarBase):
    """Grammar-enabled string field."""

    __root__: Union[str, _GrammarType]

    @classmethod
    @overrides
    def validate(cls, entry):
        if isinstance(entry, dict):
            return super().validate(entry)

        if isinstance(entry, str):
            return entry

        raise TypeError(f"value must be a string: {entry!r}")


class GrammarStrList(_GrammarBase):
    """Grammar-enabled list of strings field."""

    __root__: Union[List[str], _GrammarType]

    @classmethod
    @overrides
    def validate(cls, entry):
        if isinstance(entry, dict):
            return super().validate(entry)

        if isinstance(entry, list) and all((isinstance(x, str) for x in entry)):
            return entry

        raise TypeError(f"value must be a list of string: {entry!r}")


class GrammarSingleEntryDictList(_GrammarBase):
    """Grammar-enabled list of dictionaries field."""

    __root__: Union[List[Dict[str, Any]], _GrammarType]

    @classmethod
    @overrides
    def validate(cls, entry):
        if isinstance(entry, dict):
            return super().validate(entry)

        if isinstance(entry, list) and all(
            ((isinstance(x, dict) and len(x) == 1) for x in entry)
        ):
            return entry

        raise TypeError(f"value must be a list of single-entry dictionaries: {entry!r}")
