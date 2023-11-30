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


import pytest
from craft_grammar import errors

scenarios = (
    {
        "exception_class": errors.GrammarSyntaxError,
        "args": ["syntax incorrect"],
        "expected_message": "Invalid grammar syntax: syntax incorrect.",
    },
    {
        "exception_class": errors.OnStatementSyntaxError,
        "args": ["syntax incorrect"],
        "expected_message": "Invalid grammar syntax: 'syntax incorrect' is not a valid 'on' clause.",
    },
    {
        "exception_class": errors.ToStatementSyntaxError,
        "args": ["syntax incorrect"],
        "expected_message": "Invalid grammar syntax: 'syntax incorrect' is not a valid 'to' clause.",
    },
    {
        "exception_class": errors.UnsatisfiedStatementError,
        "args": ["foo bar"],
        "expected_message": "Unable to satisfy 'foo bar', failure forced.",
    },
)


@pytest.mark.parametrize("scenario", scenarios)
def test_error_formatting(scenario):
    assert str(scenario["exception_class"](*scenario["args"])) == (
        scenario["expected_message"]
    )
