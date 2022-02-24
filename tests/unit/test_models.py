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
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import textwrap
from unittest.mock import ANY

import pydantic
import pytest
import yaml

from craft_grammar.models import GrammarSingleEntryDictList, GrammarStr, GrammarStrList


class ValidationTest(pydantic.BaseModel):
    """A test model containing all types of grammar-aware types."""

    control: str
    grammar_str: GrammarStr
    grammar_strlist: GrammarStrList
    grammar_single_entry_dictlist: GrammarSingleEntryDictList


def test_validate_grammar_trivial():
    data = yaml.safe_load(
        textwrap.dedent(
            """
            control: a string
            grammar_str: another string
            grammar_strlist:
              - a
              - string
              - list
            grammar_single_entry_dictlist:
              - key: value
              - other_key: other_value
            """
        )
    )

    v = ValidationTest(**data)
    assert v.control == "a string"
    assert v.grammar_str == "another string"
    assert v.grammar_strlist == ["a", "string", "list"]
    assert v.grammar_single_entry_dictlist == [
        {"key": "value"},
        {"other_key": "other_value"},
    ]


def test_validate_grammar_simple():
    data = yaml.safe_load(
        textwrap.dedent(
            """
            control: a string
            grammar_str:
              on amd64: another string
              else: something different
            grammar_strlist:
              to amd64,arm64:
                - a
                - string
                - list
            grammar_single_entry_dictlist:
              on arch:
                 - key: value
                 - other_key: other_value
              else fail:
            """
        )
    )

    v = ValidationTest(**data)
    assert v.control == "a string"
    assert v.grammar_str == {
        "on": "another string",
        "else": "something different",
    }
    assert v.grammar_strlist == {
        "to": ["a", "string", "list"],
    }
    assert v.grammar_single_entry_dictlist == {
        "on": [{"key": "value"}, {"other_key": "other_value"}],
        "else fail": ANY,
    }


def test_validate_grammar_recursive():
    data = yaml.safe_load(
        textwrap.dedent(
            """
            control: a string
            grammar_str:
              on amd64: another string
              else:
                to arm64: this other thing
            grammar_strlist:
              to amd64,arm64:
                on riscv64:
                  - a
                  - string
                  - list
                else:
                  on s390x:
                    - we're
                    - "on"
                    - s390x
                  else fail:
              else:
                - other
                - stuff
            grammar_single_entry_dictlist:
              on arch,other_arch:
                 on other_arch:
                    to yet_another_arch:
                       - key: value
                       - other_key: other_value
                    else fail:
                 else:
                    - yet_another_key: yet_another_value
              else fail:
            """
        )
    )

    v = ValidationTest(**data)
    assert v.control == "a string"
    assert v.grammar_str == {
        "on": "another string",
        "else": {
            "to": "this other thing",
        },
    }
    assert v.grammar_strlist == {
        "to": {
            "on": ["a", "string", "list"],
            "else": {
                "on": ["we're", "on", "s390x"],
                "else fail": ANY,
            },
        },
        "else": ["other", "stuff"],
    }
    assert v.grammar_single_entry_dictlist == {
        "on": {
            "on": {
                "to": [{"key": "value"}, {"other_key": "other_value"}],
                "else fail": ANY,
            },
            "else": [{"yet_another_key": "yet_another_value"}],
        },
        "else fail": ANY,
    }


def test_grammar_str_error():
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: GrammarStr

    with pytest.raises(pydantic.ValidationError) as raised:
        GrammarValidation(x=["foo"])  # type: ignore

    err = raised.value.errors()
    assert len(err) == 1
    assert err[0]["loc"] == ("x",)
    assert err[0]["type"] == "type_error"
    assert err[0]["msg"] == "value must be a string: ['foo']"


def test_grammar_strlist_error():
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: GrammarStrList

    with pytest.raises(pydantic.ValidationError) as raised:
        GrammarValidation(x=["foo", 23])  # type: ignore

    err = raised.value.errors()
    assert len(err) == 1
    assert err[0]["loc"] == ("x",)
    assert err[0]["type"] == "type_error"
    assert err[0]["msg"] == "value must be a list of string: ['foo', 23]"


@pytest.mark.parametrize(
    "value",
    [
        23,
        "string",
        [{"a": 42}, "foo"],
        [{"a": 42, "b": 43}],
    ],
)
def test_grammar_single_entry_dictlist_error(value):
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: GrammarSingleEntryDictList

    with pytest.raises(pydantic.ValidationError) as raised:
        GrammarValidation(x=value)  # type: ignore

    err = raised.value.errors()
    assert len(err) == 1
    assert err[0]["loc"] == ("x",)
    assert err[0]["type"] == "type_error"
    assert err[0]["msg"] == (
        f"value must be a list of single-entry dictionaries: {value!r}"
    )


def test_grammar_nested_error():
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: GrammarStr

    with pytest.raises(pydantic.ValidationError) as raised:
        GrammarValidation(
            x={
                "on arm64,amd64": {"on arm64": "foo", "else": 35},
                "else": "baz",
            }  # type: ignore
        )
    err = raised.value.errors()
    assert len(err) == 1
    assert err[0]["loc"] == ("x",)
    assert err[0]["type"] == "type_error"
    assert err[0]["msg"] == "value must be a string: 35"


def test_grammar_str_elsefail_error():
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: GrammarStr

    with pytest.raises(pydantic.ValidationError) as raised:
        GrammarValidation(x={"on arch": "foo", "else fail": "bar"})  # type: ignore

    err = raised.value.errors()
    assert len(err) == 1
    assert err[0]["loc"] == ("x",)
    assert err[0]["type"] == "value_error"
    assert err[0]["msg"] == "'else fail' must have no arguments"


def test_grammar_try():
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: GrammarStr

    with pytest.raises(pydantic.ValidationError) as raised:
        GrammarValidation(x={"try": "foo"})  # type: ignore

    err = raised.value.errors()
    assert len(err) == 1
    assert err[0]["loc"] == ("x",)
    assert err[0]["type"] == "value_error"
    assert err[0]["msg"] == "'try' was removed from grammar, use 'on <arch>' instead"


def test_grammar_extras():
    class GrammarValidation(pydantic.BaseModel):
        """Test validation of grammar-enabled types."""

        x: GrammarStr

    with pytest.raises(pydantic.ValidationError) as raised:
        GrammarValidation(x={"on arm64": "foo", "foo": "bar"})  # type: ignore

    err = raised.value.errors()
    assert len(err) == 1
    assert err[0]["loc"] == ("x",)
    assert err[0]["type"] == "value_error"
    assert err[0]["msg"] == "invalid grammar key 'foo'"


@pytest.mark.parametrize(
    "clause,err_msg",
    [
        ("on", "invalid grammar key 'on'"),
        ("on ,", "syntax error in 'on' selector"),
        ("on ,arch", "syntax error in 'on' selector"),
        ("on arch,", "syntax error in 'on' selector"),
        ("on arch,,arch", "syntax error in 'on' selector"),
        ("on arch, arch", "spaces are not allowed in 'on' selector"),
        ("to", "invalid grammar key 'to'"),
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

        x: GrammarStr

    with pytest.raises(pydantic.ValidationError) as raised:
        GrammarValidation(x={clause: "foo"})  # type: ignore

    err = raised.value.errors()
    assert len(err) == 1
    assert err[0]["loc"] == ("x",)
    assert err[0]["type"] == "value_error"
    assert err[0]["msg"] == err_msg
