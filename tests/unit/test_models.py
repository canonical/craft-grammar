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
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import textwrap
from typing import Annotated, Any, TypeVar

import pydantic
import pytest
import yaml
from craft_grammar.models import Grammar

T = TypeVar("T")

NonEmptyDict = Annotated[dict[str, T], pydantic.Field(min_length=1)]


class ValidationTest(pydantic.BaseModel):
    """A test model containing all types of grammar-aware types."""

    control: str
    grammar_bool: Grammar[bool]
    grammar_int: Grammar[int]
    grammar_float: Grammar[float]
    grammar_str: Grammar[str]
    grammar_strlist: Grammar[list[str]]
    grammar_dict: Grammar[dict[str, Any]]
    grammar_dictlist: Grammar[list[dict]]
    grammar_annotated: Grammar[NonEmptyDict[int]]


def test_validate_grammar_trivial():
    data = yaml.safe_load(
        textwrap.dedent(
            """
            control: a string
            grammar_bool: true
            grammar_int: 42
            grammar_float: 3.14
            grammar_str: another string
            grammar_strlist:
              - a
              - string
              - list
            grammar_dict:
              key: value
              other_key: other_value
            grammar_dictlist:
              - key: value
                other_key: other_value
              - key2: value
                other_key2: other_value
            grammar_annotated:
              thing: 123
            """,
        ),
    )

    v = ValidationTest(**data)
    assert v.control == "a string"
    assert v.grammar_bool is True
    assert v.grammar_int == 42
    assert v.grammar_float == 3.14
    assert v.grammar_str == "another string"
    assert v.grammar_strlist == ["a", "string", "list"]
    assert v.grammar_dict == {"key": "value", "other_key": "other_value"}
    assert v.grammar_dictlist == [
        {"key": "value", "other_key": "other_value"},
        {"key2": "value", "other_key2": "other_value"},
    ]
    assert v.grammar_annotated == {"thing": 123}


def test_validate_grammar_simple():
    data = yaml.safe_load(
        textwrap.dedent(
            """
            control: a string
            grammar_bool:
              - on amd64: true
              - else: false
            grammar_int:
              - on amd64: 42
              - else: 23
            grammar_float:
              - on amd64: 3.14
              - else: 2.71
            grammar_str:
              - on amd64: another string
              - else: something different
            grammar_strlist:
              - to amd64,arm64:
                  - a
                  - string
                  - list
              - else fail
            grammar_dict:
              - on amd64:
                  key: value
                  other_key: other_value
              - else fail
            grammar_dictlist:
              - on arch:
                 - key: value
                   other_key: other_value
                 - key2: value
                   other_key2: other_value
              - else fail
            grammar_annotated:
              - on amd64:
                  thing: 64
              - on riscv64:
                  riscy: 64
              - else:
                  what: 0
            """,
        ),
    )

    v = ValidationTest.model_validate(data)
    assert v.control == "a string"
    assert v.grammar_bool == [
        {"*on amd64": True},
        {"*else": False},
    ]
    assert v.grammar_int == [
        {"*on amd64": 42},
        {"*else": 23},
    ]
    assert v.grammar_float == [
        {"*on amd64": 3.14},
        {"*else": 2.71},
    ]
    assert v.grammar_str == [
        {"*on amd64": "another string"},
        {"*else": "something different"},
    ]
    assert v.grammar_strlist == [
        {"*to amd64,arm64": ["a", "string", "list"]},
        "*else fail",
    ]
    assert v.grammar_dict == [
        {"*on amd64": {"key": "value", "other_key": "other_value"}},
        "*else fail",
    ]
    assert v.grammar_dictlist == [
        {
            "*on arch": [
                {"key": "value", "other_key": "other_value"},
                {"key2": "value", "other_key2": "other_value"},
            ],
        },
        "*else fail",
    ]
    assert v.grammar_annotated == [
        {
            "*on amd64": {
                "thing": 64,
            },
        },
        {
            "*on riscv64": {
                "riscy": 64,
            },
        },
        {
            "*else": {
                "what": 0,
            },
        },
    ]


def test_validate_grammar_recursive():
    data = yaml.safe_load(
        textwrap.dedent(
            """
            control: a string
            grammar_bool:
              - on amd64: true
              - else:
                - to arm64: false
                - else fail
            grammar_int:
              - on amd64: 42
              - else:
                - to arm64: 23
                - else fail
            grammar_float:
              - on amd64: 3.14
              - else:
                - to arm64: 2.71
                - else fail
            grammar_str:
              - on amd64: another string
              - else:
                - to arm64: this other thing
                - else fail
            grammar_strlist:
              - to amd64,arm64:
                - on riscv64:
                  - a
                  - string
                  - list
                  - to amd64:
                    - with
                    - extras
                - else:
                  - on s390x:
                    - we're
                    - "on"
                    - s390x
                  - else fail
              - else:
                - other
                - stuff
            grammar_dict:
                - on amd64,arm64:
                    key: value
                    other_key: other_value
                - else:
                    - on other_arch:
                        - to yet_another_arch:
                            yet_another_key: yet_another_value
                        - else fail
                    - else fail
            grammar_dictlist:
              - on arch,other_arch:
                 - on other_arch:
                    - to yet_another_arch:
                       - key: value
                         other_key: other_value
                       - key2: value
                         other_key2: other_value
                    - else fail
                 - else:
                    - yet_another_key: yet_another_value
                    - yet_another_key2: yet_another_value2
              - else fail
            grammar_annotated:
              - on amd64:
                  thing: 123
              - on riscv64 to arm64:
                  thing: 64
              - else:
                  thing: 65
              - else fail
            """,
        ),
    )

    v = ValidationTest(**data)
    assert v.control == "a string"
    assert v.grammar_bool == [
        {"*on amd64": True},
        {"*else": [{"*to arm64": False}, "*else fail"]},
    ]
    assert v.grammar_int == [
        {"*on amd64": 42},
        {"*else": [{"*to arm64": 23}, "*else fail"]},
    ]
    assert v.grammar_float == [
        {"*on amd64": 3.14},
        {"*else": [{"*to arm64": 2.71}, "*else fail"]},
    ]
    assert v.grammar_str == [
        {"*on amd64": "another string"},
        {
            "*else": [
                {"*to arm64": "this other thing"},
                "*else fail",
            ],
        },
    ]
    assert v.grammar_strlist == [
        {
            "*to amd64,arm64": [
                {
                    "*on riscv64": [
                        "a",
                        "string",
                        "list",
                        {"*to amd64": ["with", "extras"]},
                    ],
                },
                {
                    "*else": [
                        {"*on s390x": ["we're", "on", "s390x"]},
                        "*else fail",
                    ],
                },
            ],
        },
        {"*else": ["other", "stuff"]},
    ]
    assert v.grammar_dict == [
        {"*on amd64,arm64": {"key": "value", "other_key": "other_value"}},
        {
            "*else": [
                {
                    "*on other_arch": [
                        {
                            "*to yet_another_arch": {
                                "yet_another_key": "yet_another_value",
                            },
                        },
                        "*else fail",
                    ],
                },
                "*else fail",
            ],
        },
    ]

    assert v.grammar_dictlist == [
        {
            "*on arch,other_arch": [
                {
                    "*on other_arch": [
                        {
                            "*to yet_another_arch": [
                                {"key": "value", "other_key": "other_value"},
                                {"key2": "value", "other_key2": "other_value"},
                            ],
                        },
                        "*else fail",
                    ],
                },
                {
                    "*else": [
                        {
                            "yet_another_key": "yet_another_value",
                        },
                        {
                            "yet_another_key2": "yet_another_value2",
                        },
                    ],
                },
            ],
        },
        "*else fail",
    ]
    assert v.grammar_annotated == [
        {"*on amd64": {"thing": 123}},
        {"*on riscv64 to arm64": {"thing": 64}},
        {"*else": {"thing": 65}},
        "*else fail",
    ]


@pytest.mark.parametrize("value", ["foo", 13, 3.14159])
def test_grammar_str_success(value):
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: Grammar[str]

    actual = GrammarValidation(x=value)

    assert actual.x == str(value)


@pytest.mark.parametrize(
    "value",
    [["foo"], {"x"}],
)
def test_grammar_str_error(value):
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: Grammar[str]

    with pytest.raises(pydantic.ValidationError) as raised:
        GrammarValidation(x=value)

    err = raised.value.errors()
    assert len(err) == 1
    assert err[0]["loc"] == ("x",)
    assert err[0]["type"] == "string_type"
    assert err[0]["msg"] == "Input should be a valid string"


@pytest.mark.parametrize(
    "value",
    [["foo"], ["foo", 23]],
)
def test_grammar_strlist_success(value):
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: Grammar[list[str]]

    actual = GrammarValidation(x=value)
    assert actual.x == [str(i) for i in value]


@pytest.mark.parametrize(
    "value",
    [23, "foo", [{"a": "b"}]],
)
def test_grammar_strlist_error(value):
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: Grammar[list[str]]

    with pytest.raises(pydantic.ValidationError) as raised:
        GrammarValidation(x=value)
    err = raised.value.errors()
    assert len(err) == 1
    assert err[0]["loc"] == ("x",)
    assert err[0]["type"] == "value_error"
    assert err[0]["msg"] == f"Value error, value must be a list of str: {value!r}"


def test_grammar_nested_error():
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: Grammar[str]

    with pytest.raises(pydantic.ValidationError) as raised:
        GrammarValidation(
            x=[  # pyright: ignore [reportArgumentType]
                {"on arm64,amd64": [{"on arm64": "foo"}, {"else": [35]}]},
            ],
        )
    err = raised.value.errors()
    assert len(err) == 1
    assert err[0]["loc"] == ("x", 0, 1)
    assert err[0]["type"] == "string_type"
    assert err[0]["msg"] == "Input should be a valid string"


def test_grammar_str_elsefail():
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: Grammar[str]

    GrammarValidation(
        x=[{"on arch": "foo"}, "else fail"],  # pyright: ignore [reportArgumentType]
    )


def test_grammar_strlist_elsefail():
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: Grammar[list[str]]

    GrammarValidation(
        x=[{"on arch": ["foo"]}, "else fail"],  # pyright: ignore [reportArgumentType]
    )


def test_grammar_try():
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: Grammar[str]

    with pytest.raises(pydantic.ValidationError) as raised:
        GrammarValidation(x=[{"try": "foo"}])  # pyright: ignore [reportArgumentType]

    err = raised.value.errors()
    assert len(err) == 1
    assert err[0]["loc"] == ("x", 0)
    assert err[0]["type"] == "value_error"
    assert (
        err[0]["msg"]
        == "Value error, 'try' was removed from grammar, use 'on <arch>' instead"
    )


@pytest.mark.parametrize(
    ("clause", "err_msg"),
    [
        ("a", "value must be a str or valid grammar dict: [{'a': 'foo'}]"),
        ("on", "value must be a str or valid grammar dict: [{'on': 'foo'}]"),
        ("on ,", "syntax error in 'on' selector"),
        ("on ,arch", "syntax error in 'on' selector"),
        ("on arch,", "syntax error in 'on' selector"),
        ("on arch,,arch", "syntax error in 'on' selector"),
        ("on arch, arch", "spaces are not allowed in 'on' selector"),
        ("to", "value must be a str or valid grammar dict: [{'to': 'foo'}]"),
        ("to ,", "syntax error in 'to' selector"),
        ("to ,arch", "syntax error in 'to' selector"),
        ("to arch,", "syntax error in 'to' selector"),
        ("to arch,,arch", "syntax error in 'to' selector"),
        ("to arch, arch", "spaces are not allowed in 'to' selector"),
        ("on , to b", "syntax error in 'on ... to' selector"),
        ("on ,a to b", "syntax error in 'on ... to' selector"),
        ("on a, to b", "syntax error in 'on ... to' selector"),
        ("on a,,a to b", "syntax error in 'on ... to' selector"),
        ("on a to ,", "syntax error in 'on ... to' selector"),
        ("on a to ,b", "syntax error in 'on ... to' selector"),
        ("on a to b,", "syntax error in 'on ... to' selector"),
        ("on a to b,,b", "syntax error in 'on ... to' selector"),
        ("on a, a to b", "spaces are not allowed in 'on ... to' selector"),
        ("on a to b, b", "spaces are not allowed in 'on ... to' selector"),
    ],
)
def test_grammar_errors(clause, err_msg):
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: Grammar[str]

    with pytest.raises(pydantic.ValidationError) as raised:
        GrammarValidation(x=[{clause: "foo"}])  # pyright: ignore [reportArgumentType]

    err = raised.value.errors()
    assert len(err) == 1
    assert err[0]["loc"] == ("x", 0)
    assert err[0]["msg"].endswith(err_msg)
