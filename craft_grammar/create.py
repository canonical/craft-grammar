#  This file is part of craft-grammar.
#
#  Copyright 2024 Canonical Ltd.
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License version 3, as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
#  SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Utilities to create grammar models."""

import builtins
import logging
import types
import typing

from pydantic import BaseModel

logger = logging.getLogger(__name__)

CONFIG_TEMPLATE = """
    model_config = ConfigDict(
        validate_assignment=True,
        extra="ignore",
        frozen=True,
        alias_generator=lambda s: s.replace("_", "-"),
        coerce_numbers_to_str=True,
    )
"""


def create_grammar_model(model_class: type[BaseModel]) -> str:
    """Create the code for a grammar-aware class compatible with ``model_class``.

    :param model_class: A pydantic.BaseModel subclass.
    """
    class_decl = f"class Grammar{model_class.__name__}(BaseModel):"

    attributes = []
    type_hints = typing.get_type_hints(model_class)
    for attr_name, attr_type in type_hints.items():
        if attr_name == "__slots__":
            # This happens in Python 3.12 apparently
            continue

        grammar_type = _get_grammar_type_for(attr_type)

        if grammar_type is None:
            logger.debug(
                "Skipping unknown type %s for attribute %s",
                attr_type,
                attr_name,
            )
            continue

        attr_field = model_class.model_fields[attr_name]
        alias = attr_field.alias
        new_name = attr_name
        if alias and "-" not in alias:
            new_name = alias
        attr_decl = f"{new_name}: {grammar_type}"

        if not attr_field.is_required():
            default_factory = attr_field.default_factory
            if default_factory is not None:
                default = repr(default_factory())  # type: ignore[call-arg]
            else:
                default = repr(attr_field.default)
            # repr(x) uses single quotes for strings; replace them with double
            # quotes here to be consistent with the codebase.
            default = default.replace("'", '"')
            attr_decl += f" = {default}"

        attributes.append(attr_decl)

    lines = [class_decl, *CONFIG_TEMPLATE.split("\n")]
    lines.extend(f"    {attr}" for attr in attributes)
    lines.append("")  # Final newline

    return "\n".join(lines)


def _get_grammar_type_for(  # noqa: PLR0911,PLR0912 (too many returns/branches)
    model_type: type,
) -> str | None:
    """Get the "grammar" type for ``model_type``.

    Returns None if we don't know how to "grammify" ``model_type``.
    """
    if model_type is type(None):
        # None -> None
        return "None"

    origin = typing.get_origin(model_type)
    args = typing.get_args(model_type)

    match origin:
        case None:
            # Primitive, regular class, Pydantic model, etc.
            if issubclass(model_type, BaseModel):
                # PydanticModel -> GrammarPydanticModel
                # (assumes that generate_grammar_model(model_type) will be called).
                return f"Grammar{model_type.__name__}"
            return f"Grammar[{model_type.__name__}]"

        case typing.Union:
            # Type is either a Union[] or an Optional[]
            if len(args) == 2 and type(None) in args:  # noqa: PLR2004 (magic value)
                # Type is an Optional[]
                # Optional[T] -> Optional[Grammar[T]]
                other_type = [t for t in args if t is not type(None)][0]
                grammar_type = _get_grammar_type_for(other_type)
                return f"Optional[{grammar_type}]"

            # Union[X, Y] -> Grammar[Union[X, Y]]
            union_args = []
            for arg in typing.get_args(model_type):
                if typing.get_origin(arg) is None:
                    name = "None" if arg is type(None) else arg.__name__
                    union_args.append(name)
                else:
                    # print dict[k, v] as "dict[k,v]"
                    union_args.append(str(arg))
            comma_args = ", ".join(union_args)
            return f"Grammar[Union[{comma_args}]]"

        case types.UnionType:
            # Type is an expression like "str | int | None"
            # A type like "str | None" becomes "Grammar[str] | None"
            grammar_types = [_get_grammar_type_for(a) for a in args]
            grammar_args = [t for t in grammar_types if t is not None]
            return " | ".join(grammar_args)

        case builtins.list | builtins.dict:
            # list[T] -> Grammar[list[T]]
            name = str(model_type).removeprefix("typing.")
            return f"Grammar[{name}]"

        case typing.Literal:
            # Literal["a", "b"] -> Grammar[str]
            arg_types = {type(a) for a in typing.get_args(model_type)}
            if len(arg_types) == 1:
                # For now only handle the case where all possible literal values
                # have the same type
                arg_type = arg_types.pop()
                return _get_grammar_type_for(arg_type)
            return None

        case _:
            return None
