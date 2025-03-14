# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2022-2024 Canonical Ltd.
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

# ruff: noqa: ANN401 (any-type)

import abc
import re
from typing import Any, Generic, TypeVar, get_args, get_origin

import pydantic
import pydantic_core
from overrides import overrides
from pydantic import GetCoreSchemaHandler, ValidationError, ValidationInfo
from pydantic_core import core_schema

_on_pattern = re.compile(r"^on\s+(.+)\s*$")
_to_pattern = re.compile(r"^to\s+(.+)\s*$")
_compound_pattern = re.compile(r"^on\s+(.+)\s+to\s+(.+)\s*$")

_ELSE_FAIL = "else fail"
_ELSE = "else"
_TRY = "try"


T = TypeVar("T")


class _GrammarBase(abc.ABC):
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        source: type[Any],
        handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        return core_schema.with_info_after_validator_function(
            cls.validate,
            core_schema.any_schema(),
        )

    @classmethod
    @abc.abstractmethod
    def validate(cls, input_value: Any, /, info: ValidationInfo) -> Any:
        """Ensure the given entry is valid type or grammar."""

    @classmethod
    def _grammar_append(cls, entry: list[Any], item: Any, info: ValidationInfo) -> None:
        if item == _ELSE_FAIL:
            _mark_and_append(entry, item)
        else:
            key, value = tuple(item.items())[0]
            _mark_and_append(entry, {key: cls.validate(value, info)})

    @classmethod
    def _validate_grammar_list(  # noqa: PLR0912
        cls,
        type_: type[list[T]],
        input_value: list[Any],
        info: ValidationInfo,
    ) -> list[T]:
        # Check if the type_ is supposed to be a list
        sub_type: Any = get_args(type_)
        unsubscripted_type = get_origin(type_) or type_

        # handle typed list
        if sub_type:
            sub_type = sub_type[0]
            if sub_type is Any:
                sub_type = None

        new_entry: list[Any] = []
        errors: list[pydantic_core.InitErrorDetails] = []
        for index, item in enumerate(input_value):
            # Check if the item is a valid grammar clause
            try:
                if _is_grammar_clause(item):
                    cls._grammar_append(new_entry, item, info)
                    continue
            except pydantic.ValidationError as exc:
                errors.extend(
                    pydantic_core.InitErrorDetails(
                        type=err["type"],
                        loc=(index, *err["loc"]),
                        input=err["input"],
                        ctx=err.get("ctx", {"error": err}),
                    )
                    for err in exc.errors()
                )
                break
            except ValueError as exc:
                errors.append(
                    pydantic_core.InitErrorDetails(
                        type="value_error",
                        loc=(index,),
                        input=item,
                        ctx={"error": exc},
                    ),
                )
                continue
            if sub_type:
                sub_type_adapter = pydantic.TypeAdapter(
                    sub_type,
                    config=pydantic.ConfigDict(coerce_numbers_to_str=True),
                )
                try:
                    new_entry.append(sub_type_adapter.validate_python(item))
                except ValidationError:
                    pass
                else:
                    continue
            if issubclass(unsubscripted_type, str):
                if isinstance(item, dict):
                    errors.append(
                        pydantic_core.InitErrorDetails(
                            type="value_error",
                            loc=(index,),
                            input=item,
                            ctx={
                                "error": ValueError(
                                    f"value must be a str or valid grammar dict: {input_value!r}",
                                ),
                            },
                        ),
                    )
                else:
                    raise pydantic.ValidationError.from_exception_data(
                        title=f"Grammar[{type_.__name__}]",
                        line_errors=[
                            pydantic_core.InitErrorDetails(
                                type="string_type",
                                loc=(),
                                input=item,
                            ),
                        ],
                    )
                    break
            else:
                raise ValueError(  # noqa: TRY004
                    _format_type_error(type_, input_value),
                )

        if errors:
            raise pydantic.ValidationError.from_exception_data(
                title=f"Grammar[{type_.__name__}]",
                line_errors=errors,
            )
        return new_entry


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
        if len(args) == 2:  # noqa: PLR2004 (magic-value-comparison)
            return f"value must be a dict of {args[0].__name__} to {args[1].__name__}: {entry!r}"
        return f"value must be a dict: {entry!r}"

    return f"value must be a {type_.__name__}: {entry!r}"


class GrammarMetaClass(type):
    """Grammar type metaclass.

    Allows to use GrammarType[T] to define a grammar-aware type.
    """

    # Define __getitem__ method to be able to use index
    def __getitem__(cls, type_: Any) -> Any:
        class GrammarScalar(_GrammarBase):
            """Grammar scalar class.

            Dynamically generated class to handle grammar-aware types.
            """

            @classmethod
            @overrides
            def validate(cls, input_value: Any, /, info: ValidationInfo) -> Any:
                # Grammar[T] entry can be a list if it contains clauses
                if isinstance(input_value, list):
                    return cls._validate_grammar_list(type_, input_value, info)

                type_adapter = pydantic.TypeAdapter(
                    type_,
                    config=pydantic.ConfigDict(coerce_numbers_to_str=True),
                )

                # Not a valid grammar, check if it is a dict
                if isinstance(input_value, dict):
                    # Check if the input is valid in its non-grammar type.
                    type_adapter.validate_python(input_value)
                    return input_value

                # handle primitive types with pydantic validators
                if isinstance(type_, type) and issubclass(type_, str):
                    return type_adapter.validate_python(input_value, strict=False)
                try:
                    type_adapter.validate_python(input_value)
                except ValidationError as err:
                    raise ValueError(_format_type_error(type_, input_value)) from err

                return input_value

        return GrammarScalar


class Grammar(Generic[T], metaclass=GrammarMetaClass):
    """Grammar aware type.

    Allows to use Grammar[T] to define a grammar-aware type.

    Grammar[int]
    Grammar[list[str]]
    Grammar[dict[str, int]]

    """


def _ensure_selector_valid(selector: str, *, clause: str) -> None:
    """Verify selector syntax."""
    # spaces are not allowed in selector
    if " " in selector:
        raise ValueError(f"spaces are not allowed in {clause!r} selector")

    # selector items should be separated by comma
    if selector.startswith(",") or selector.endswith(",") or ",," in selector:
        raise ValueError(f"syntax error in {clause!r} selector")


def _is_grammar_clause(item: Any) -> bool:  # noqa: PLR0911 (too-many-return-statements)
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


def _mark_and_append(entry: list[Any], item: Any) -> None:
    """Mark entry as parsed for testing and debug."""
    if isinstance(item, str):
        entry.append("*" + item)
    elif isinstance(item, dict):
        key, value = tuple(item.items())[0]
        entry.append({f"*{key}": value})
