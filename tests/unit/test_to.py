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

import re

import pytest
from craft_grammar import GrammarProcessor, ToStatement, errors


def test_on():
    processor = GrammarProcessor(
        checker=lambda x: True,
        arch="amd64",
        target_arch="amd64",
    )

    clause = ToStatement(to_statement="to amd64", body=["foo"], processor=processor)
    assert clause.process() == ["foo"]


def test_on_else():
    processor = GrammarProcessor(
        checker=lambda x: True,
        arch="amd64",
        target_arch="amd64",
    )

    clause = ToStatement(to_statement="to arm64", body=["foo"], processor=processor)
    clause.add_else(["bar"])
    assert clause.process() == ["bar"]


def test_on_else_fail():
    processor = GrammarProcessor(
        checker=lambda x: True,
        arch="amd64",
        target_arch="amd64",
    )

    clause = ToStatement(to_statement="to arm64", body=["foo"], processor=processor)
    clause.add_else(None)
    with pytest.raises(errors.UnsatisfiedStatementError):
        clause.process()


def test_on_nested_else_with_valid_on_else():
    processor = GrammarProcessor(
        checker=lambda x: True,
        arch="arm64",
        target_arch="arm64",
    )

    clause = ToStatement(to_statement="to amd64", body=["foo"], processor=processor)
    clause.add_else([{"to arm64": ["bar"]}])
    clause.add_else(["baz"])
    assert clause.process() == ["bar"]


def test_on_nested_else_with_on_but_valid_else():
    processor = GrammarProcessor(
        checker=lambda x: True,
        arch="i386",
        target_arch="i386",
    )

    clause = ToStatement(to_statement="to amd64", body=["foo"], processor=processor)
    clause.add_else([{"to riscv64": ["bar"]}])
    clause.add_else(["baz"])
    assert clause.process() == ["baz"]


def test_on_missing():
    processor = GrammarProcessor(
        checker=lambda x: True,
        arch="amd64",
        target_arch="amd64",
    )

    with pytest.raises(errors.ToStatementSyntaxError):
        ToStatement(
            to_statement="on amd64",
            body=["foo"],
            processor=processor,
        )


error_scenarios = [
    # spaces in selectors
    {
        "to_arch": "to amd64, ubuntu",
        "body": ["foo"],
        "else_bodies": [],
        "expected_exception": ".*not a valid 'to' clause.*spaces are not allowed in the selectors.*",
    },
    # beginning with comma
    {
        "to_arch": "to ,amd64",
        "body": ["foo"],
        "else_bodies": [],
        "expected_exception": ".*not a valid 'to' clause",
    },
    # ending with comma
    {
        "to_arch": "to amd64,",
        "body": ["foo"],
        "else_bodies": [],
        "expected_exception": ".*not a valid 'to' clause",
    },
    # multiple commas
    {
        "to_arch": "to amd64,,ubuntu",
        "body": ["foo"],
        "else_bodies": [],
        "expected_exception": ".*not a valid 'to' clause",
    },
    # invalid selector format
    {
        "to_arch": "on",
        "body": ["foo"],
        "else_bodies": [],
        "expected_exception": ".*not a valid 'to' clause.*selectors are missing",
    },
    # not even close
    {
        "to_arch": "im-invalid",
        "body": ["foo"],
        "else_bodies": [],
        "expected_exception": ".*not a valid 'to' clause",
    },
]


@pytest.mark.parametrize("scenario", error_scenarios)
def test_errors(scenario):
    with pytest.raises(  # noqa: PT012 (pytest-raises-with-multiple-statements)
        errors.ToStatementSyntaxError,
    ) as syntax_error:
        processor = GrammarProcessor(
            arch="amd64",
            target_arch="amd64",
            checker=lambda x: "invalid" not in x,
        )
        statement = ToStatement(
            to_statement=scenario["to_arch"],
            body=scenario["body"],
            processor=processor,
        )

        for else_body in scenario["else_bodies"]:
            statement.add_else(else_body)

        statement.process()

    assert re.match(scenario["expected_exception"], str(syntax_error.value))
