# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2025 Canonical Ltd.
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
from craft_grammar import ForStatement, GrammarProcessor, errors


def test_for():
    """Match a platform."""
    processor = GrammarProcessor(
        checker=lambda x: True,
        arch="amd64",
        target_arch="riscv64",
        platforms=["test-platform"],
    )

    clause = ForStatement(
        for_statement="for test-platform",
        body=["foo"],
        processor=processor,
    )
    assert clause.process() == ["foo"]


@pytest.mark.parametrize("platform", ["foo", "bar", "baz", "qux"])
def test_for_many_platforms(platform):
    """Match against multiple platforms."""
    processor = GrammarProcessor(
        checker=lambda x: True,
        arch="amd64",
        target_arch="riscv64",
        platforms=["foo", "bar", "baz", "qux"],
    )

    clause = ForStatement(
        for_statement=f"for {platform}",
        body=["body"],
        processor=processor,
    )
    assert clause.process() == ["body"]


def test_for_no_match():
    """Match no platforms."""
    processor = GrammarProcessor(
        checker=lambda x: True,
        arch="amd64",
        target_arch="riscv64",
        platforms=["foo", "bar", "baz", "qux"],
    )

    clause = ForStatement(
        for_statement="for other",
        body=["body"],
        processor=processor,
    )
    assert clause.process() == []


def test_for_no_platforms_to_match():
    """Don't match platforms if none are provided."""
    processor = GrammarProcessor(
        checker=lambda x: True,
        arch="amd64",
        target_arch="riscv64",
        # platforms not defined here
    )

    clause = ForStatement(
        for_statement="for test-platform",
        body=["body"],
        processor=processor,
    )
    assert clause.process() == []


@pytest.mark.parametrize(
    ("statement", "expected_error"),
    [
        pytest.param(
            "for test platform",
            "spaces are not allowed in the selector",
            id="spaces in selectors",
        ),
        pytest.param(
            "for ,test-platform",
            "multiple selectors are not allowed",
            id="beginning with comma",
        ),
        pytest.param(
            "for amd64,",
            "multiple selectors are not allowed",
            id="ending with comma",
        ),
        pytest.param(
            "for test,,platform",
            "multiple selectors are not allowed",
            id="multiple commas",
        ),
        pytest.param(
            "for",
            "selector is missing",
            id="invalid selector format",
        ),
        pytest.param(
            "im-invalid",
            "selector is missing",
            id="not even close",
        ),
    ],
)
def test_errors(statement, expected_error):
    """Error on invalid usage."""
    processor = GrammarProcessor(
        arch="amd64",
        target_arch="riscv64",
        platforms=["test-platform"],
        checker=lambda x: "invalid" not in x,
    )
    expected_error = re.escape(
        f"Invalid grammar syntax: {statement!r} is not a valid 'for' clause: "
        f"{expected_error}."
    )

    with pytest.raises(errors.ForStatementSyntaxError, match=expected_error):
        statement = ForStatement(
            for_statement=statement,
            body=["foo"],
            processor=processor,
        )


def test_unknown_platform_name():
    processor = GrammarProcessor(
        arch="amd64",
        target_arch="riscv64",
        platforms=["test-platform"],
        checker=lambda x: "invalid" not in x,
        valid_platforms=["test-platform", "other-platform"],
    )
    with pytest.raises(errors.UnknownPlatformNameError):
        ForStatement(
            for_statement="for invalid-platform", body=["foo"], processor=processor
        )
