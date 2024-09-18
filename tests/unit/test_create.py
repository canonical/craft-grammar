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
from __future__ import annotations

from typing import List, Literal, Optional, Union  # noqa: UP035 (deprecated-import)

from craft_grammar import create_grammar_model
from pydantic import BaseModel, Field


class SubModel(BaseModel):
    """A Pydantic model used as an attribute of another model."""


class MyModel(BaseModel):
    """A Pydantic model that we want to "grammify"."""

    # Primitive types
    str_value: str
    str_value_or_none: str | None
    optional_str_value: Optional[str]  # noqa: UP007 (non-pep604-annotation)
    str_with_default: str = "string"
    str_or_non_with_default: str | None = "string or None"
    union_value: Union[str, int, None]  # noqa: UP007 (non-pep604-annotation)
    literal_value: Literal["red", "green", "blue"] = "green"

    # Collections
    list_value: list[int] = []
    other_list: List[int]  # noqa: UP006 (non-pep585-annotation)
    dict_value: dict[str, bool]
    list_of_dicts: list[dict[str, str]]

    # Pydantic models
    sub_model: SubModel

    # An aliased field (should use the alias)
    aliased_field: int = Field(default=1, alias="alias_name")

    # A field with a default factory
    factory_field: str = Field(default_factory=str)


EXPECTED_GRAMMAR_MODEL = """\
class GrammarMyModel(BaseModel):

    model_config = ConfigDict(
        validate_assignment=True,
        extra="ignore",
        frozen=True,
        alias_generator=lambda s: s.replace("_", "-"),
        coerce_numbers_to_str=True,
    )

    str_value: Grammar[str]
    str_value_or_none: Grammar[str] | None
    optional_str_value: Optional[Grammar[str]]
    str_with_default: Grammar[str] = "string"
    str_or_non_with_default: Grammar[str] | None = "string or None"
    union_value: Grammar[Union[str, int, None]]
    literal_value: Grammar[str] = "green"
    list_value: Grammar[list[int]] = []
    other_list: Grammar[List[int]]
    dict_value: Grammar[dict[str, bool]]
    list_of_dicts: Grammar[list[dict[str, str]]]
    sub_model: GrammarSubModel
    alias_name: Grammar[int] = 1
    factory_field: Grammar[str] = ""
"""


def test_create_model():
    grammar_model = create_grammar_model(MyModel)

    assert grammar_model == EXPECTED_GRAMMAR_MODEL
