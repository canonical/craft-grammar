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
from craft_grammar import (
    CompoundStatement,
    GrammarProcessor,
    OnStatement,
    ToStatement,
    errors,
)

scenarios = [
    # on amd64
    {
        "on_arch": "on amd64",
        "to_arch": "to armhf",
        "body": ["foo"],
        "else_bodies": [],
        "arch": "amd64",
        "expected_packages": ["foo"],
    },
    # on i386
    {
        "on_arch": "on amd64",
        "to_arch": "to armhf",
        "body": ["foo"],
        "else_bodies": [],
        "arch": "i386",
        "expected_packages": [],
    },
    # ignored else
    {
        "on_arch": "on amd64",
        "to_arch": "to armhf",
        "body": ["foo"],
        "else_bodies": [["bar"]],
        "arch": "amd64",
        "expected_packages": ["foo"],
    },
    # used else
    {
        "on_arch": "on amd64",
        "to_arch": "to i386",
        "body": ["foo"],
        "else_bodies": [["bar"]],
        "arch": "i386",
        "expected_packages": ["bar"],
    },
    # third else ignored
    {
        "on_arch": "on amd64",
        "to_arch": "to i386",
        "body": ["foo"],
        "else_bodies": [["bar"], ["baz"]],
        "arch": "i386",
        "expected_packages": ["bar"],
    },
    # third else followed
    {
        "on_arch": "on amd64",
        "to_arch": "to i386",
        "body": ["foo"],
        "else_bodies": [[{"on armhf": ["bar"]}], ["baz"]],
        "arch": "i386",
        "expected_packages": ["baz"],
    },
    # nested amd64
    {
        "on_arch": "on amd64",
        "to_arch": "to armhf",
        "body": [{"on amd64": ["foo"]}, {"on i386": ["bar"]}],
        "else_bodies": [],
        "arch": "amd64",
        "expected_packages": ["foo"],
    },
    # nested i386
    {
        "on_arch": "on i386",
        "to_arch": "to armhf",
        "body": [{"on amd64": ["foo"]}, {"on i386": ["bar"]}],
        "else_bodies": [],
        "arch": "i386",
        "expected_packages": ["bar"],
    },
    # nested body ignored else
    {
        "on_arch": "on amd64",
        "to_arch": "to armhf",
        "body": [{"on amd64": ["foo"]}, {"else": ["bar"]}],
        "else_bodies": [],
        "arch": "amd64",
        "expected_packages": ["foo"],
    },
    # nested body used else
    {
        "on_arch": "on i386",
        "to_arch": "to armhf",
        "body": [{"on amd64": ["foo"]}, {"else": ["bar"]}],
        "else_bodies": [],
        "arch": "i386",
        "expected_packages": ["bar"],
    },
    # nested else ignored else
    {
        "on_arch": "on armhf",
        "to_arch": "to i386",
        "body": ["foo"],
        "else_bodies": [[{"on amd64": ["bar"]}, {"else": ["baz"]}]],
        "arch": "amd64",
        "expected_packages": ["bar"],
    },
    # nested else used else",
    {
        "on_arch": "on armhf",
        "to_arch": "to i386",
        "body": ["foo"],
        "else_bodies": [[{"on amd64": ["bar"]}, {"else": ["baz"]}]],
        "arch": "i386",
        "expected_packages": ["baz"],
    },
    # "with hyphen
    {
        "on_arch": "on other-arch",
        "to_arch": "to yet-another-arch",
        "body": ["foo"],
        "else_bodies": [],
        "arch": "amd64",
        "expected_packages": [],
    },
    # multiple selectors
    {
        "on_arch": "on amd64,i386",
        "to_arch": "to armhf,arm64",
        "body": ["foo"],
        "else_bodies": [],
        "arch": "amd64",
        "expected_packages": [],
    },
]


@pytest.mark.parametrize("scenario", scenarios)
def test_compound_statement(scenario):
    processor = GrammarProcessor(
        arch=scenario["arch"],
        target_arch="armhf",
        checker=lambda x: True,
    )
    statements = [
        OnStatement(
            on_statement=scenario["on_arch"],
            body=scenario["body"],
            processor=processor,
        ),
        ToStatement(
            to_statement=scenario["to_arch"],
            body=scenario["body"],
            processor=processor,
        ),
    ]
    statement = CompoundStatement(
        statements=statements,
        body=scenario["body"],
        processor=processor,
    )

    for else_body in scenario["else_bodies"]:
        statement.add_else(else_body)

    assert statement.process() == scenario["expected_packages"]


error_scenarios = [
    # spaces in on selectors
    {
        "on_arch": "on amd64, ubuntu",
        "to_arch": "to i386",
        "body": ["foo"],
        "else_bodies": [],
        "expected_exception": errors.OnStatementSyntaxError,
        "expected_message": ".*not a valid 'on' clause.*spaces are not allowed in the "
        "selectors.*",
    },
    # spaces in to selectors
    {
        "on_arch": "on amd64,ubuntu",
        "to_arch": "to i386, armhf",
        "body": ["foo"],
        "else_bodies": [],
        "expected_exception": errors.ToStatementSyntaxError,
        "expected_message": ".*not a valid 'to' clause.*spaces are not allowed in the "
        "selectors.*",
    },
]


@pytest.mark.parametrize("scenario", error_scenarios)
def test_errors(scenario):
    with pytest.raises(  # noqa: PT012 (pytest-raises-with-multiple-statements)
        scenario["expected_exception"],
    ) as grammar_error:
        processor = GrammarProcessor(
            arch="amd64",
            target_arch="armhf",
            checker=lambda x: "invalid" not in x,
        )
        statements = [
            OnStatement(
                on_statement=scenario["on_arch"],
                body=scenario["body"],
                processor=processor,
            ),
            ToStatement(
                to_statement=scenario["to_arch"],
                body=scenario["body"],
                processor=processor,
            ),
        ]
        statement = CompoundStatement(
            statements=statements,
            body=scenario["body"],
            processor=processor,
        )

        for else_body in scenario["else_bodies"]:
            statement.add_else(else_body)

        statement.process()

    assert re.match(scenario["expected_message"], str(grammar_error.value))
