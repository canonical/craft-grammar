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

import pytest
from craft_grammar import GrammarProcessor, TryStatement, errors

scenarios = [
    # followed body
    {
        "body": ["foo", "bar"],
        "else_bodies": [],
        "expected_packages": ["foo", "bar"],
    },
    # followed else
    {
        "body": ["invalid"],
        "else_bodies": [["valid"]],
        "expected_packages": ["valid"],
    },
    # optional without else
    {"body": ["invalid"], "else_bodies": [], "expected_packages": []},
    # followed chained else
    {
        "body": ["invalid1"],
        "else_bodies": [["invalid2"], ["finally-valid"]],
        "expected_packages": ["finally-valid"],
    },
    # nested body followed body
    {
        "body": [{"try": ["foo"]}, {"else": ["bar"]}],
        "else_bodies": [],
        "expected_packages": ["foo"],
    },
    # nested body followed else
    {
        "body": [{"try": ["invalid"]}, {"else": ["bar"]}],
        "else_bodies": [],
        "expected_packages": ["bar"],
    },
    # nested else followed body
    {
        "body": ["invalid"],
        "else_bodies": [[{"try": ["foo"]}, {"else": ["bar"]}]],
        "expected_packages": ["foo"],
    },
    # nested else followed else
    {
        "body": ["invalid"],
        "else_bodies": [[{"try": ["invalid"]}, {"else": ["bar"]}]],
        "expected_packages": ["bar"],
    },
    # multiple elses
    {
        "body": ["invalid1"],
        "else_bodies": [["invalid2"], ["valid"]],
        "expected_packages": ["valid"],
    },
    # multiple elses all invalid
    {
        "body": ["invalid1"],
        "else_bodies": [["invalid2"], ["invalid3"]],
        "expected_packages": ["invalid3"],
    },
]


@pytest.mark.parametrize("scenario", scenarios)
def test_try_statement_grammar(scenario):
    processor = GrammarProcessor(
        arch="amd64",
        target_arch="amd64",
        checker=lambda x: "invalid" not in x,
    )
    statement = TryStatement(body=scenario["body"], processor=processor)

    for else_body in scenario["else_bodies"]:
        statement.add_else(else_body)

    assert statement.process() == scenario["expected_packages"]


def test_invalid_try_with_no_else():
    def checker(primitive) -> bool:
        return primitive == "valid-else"

    processor = GrammarProcessor(checker=checker, arch="amd64", target_arch="amd64")
    clause = TryStatement(
        body=["invalid-try"],
        processor=processor,
    )

    assert clause.process() == []


def test_invalid_try_with_else_fail():
    def checker(primitive) -> bool:
        return primitive == "valid-else"

    processor = GrammarProcessor(checker=checker, arch="amd64", target_arch="amd64")
    clause = TryStatement(
        body=["invalid-try"],
        processor=processor,
    )
    clause.add_else(None)

    with pytest.raises(errors.UnsatisfiedStatementError):
        clause.process()
