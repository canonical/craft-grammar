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

            if re.match(r"^on\s+.+", key):
                new_entry["on"] = cls.validate(value)
            elif re.match(r"^to\s+.+", key):
                new_entry["to"] = cls.validate(value)
            elif key == "else fail":
                if value:
                    raise ValueError("'else fail' must have no arguments")
                new_entry[key] = None
            elif key == "else":
                new_entry[key] = cls.validate(value)
            else:
                raise ValueError(f"invalid grammar key {key!r}")

        return new_entry


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
