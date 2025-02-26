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


@pytest.mark.parametrize(
    "entry",
    [
        [{"on amd64,i386": ["foo"]}, {"on amd64,i386": ["bar"]}],
        [{"on amd64,i386": ["foo"]}, {"on i386,amd64": ["bar"]}],
    ],
)
def test_duplicates(entry):
    """Test that multiple identical selector sets is an error."""

    processor = GrammarProcessor(
        arch="amd64",
        target_arch="amd64",
        checker=lambda x: True,
    )
    with pytest.raises(errors.GrammarSyntaxError) as error:
        processor.process(grammar=entry)

    expected = (
        "Invalid grammar syntax: found duplicate 'on amd64,i386' "
        "statements. These should be merged."
    )
    assert expected in str(error.value)


scenarios = [
    # unconditional
    {
        "grammar_entry": ["foo", "bar"],
        "arch": "amd64",
        "target_arch": "amd64",
        "expected_results": ["foo", "bar"],
    },
    # unconditional dict
    {
        "grammar_entry": [{"foo": "bar"}],
        "arch": "amd64",
        "target_arch": "amd64",
        "expected_results": [{"foo": "bar"}],
    },
    # unconditional multi-dict
    {
        "grammar_entry": [{"foo": "bar"}, {"foo2": "bar2"}],
        "arch": "amd64",
        "target_arch": "amd64",
        "expected_results": [{"foo": "bar"}, {"foo2": "bar2"}],
    },
    # mixed including
    {
        "grammar_entry": ["foo", {"on i386": ["bar"]}],
        "arch": "i386",
        "target_arch": "i386",
        "expected_results": ["foo", "bar"],
    },
    # mixed excluding
    {
        "grammar_entry": ["foo", {"on i386": ["bar"]}],
        "arch": "amd64",
        "target_arch": "amd64",
        "expected_results": ["foo"],
    },
    # on amd64
    {
        "grammar_entry": [{"on amd64": ["foo"]}, {"on i386": ["bar"]}],
        "arch": "amd64",
        "target_arch": "amd64",
        "expected_results": ["foo"],
    },
    # on i386
    {
        "grammar_entry": [{"on amd64": ["foo"]}, {"on i386": ["bar"]}],
        "arch": "i386",
        "target_arch": "i386",
        "expected_results": ["bar"],
    },
    # ignored else
    {
        "grammar_entry": [{"on amd64": ["foo"]}, {"else": ["bar"]}],
        "arch": "amd64",
        "target_arch": "amd64",
        "expected_results": ["foo"],
    },
    # used else
    {
        "grammar_entry": [{"on amd64": ["foo"]}, {"else": ["bar"]}],
        "arch": "i386",
        "target_arch": "i386",
        "expected_results": ["bar"],
    },
    # nested amd64
    {
        "grammar_entry": [{"on amd64": [{"on amd64": ["foo"]}, {"on i386": ["bar"]}]}],
        "arch": "amd64",
        "target_arch": "amd64",
        "expected_results": ["foo"],
    },
    # nested amd64 dict
    {
        "grammar_entry": [
            {"on amd64": [{"on amd64": [{"foo": "bar"}]}, {"on i386": ["bar"]}]},
        ],
        "arch": "amd64",
        "target_arch": "amd64",
        "expected_results": [{"foo": "bar"}],
    },
    # nested i386
    {
        "grammar_entry": [{"on i386": [{"on amd64": ["foo"]}, {"on i386": ["bar"]}]}],
        "arch": "i386",
        "target_arch": "i386",
        "expected_results": ["bar"],
    },
    # nested ignored else
    {
        "grammar_entry": [{"on amd64": [{"on amd64": ["foo"]}, {"else": ["bar"]}]}],
        "arch": "amd64",
        "target_arch": "amd64",
        "expected_results": ["foo"],
    },
    # nested used else
    {
        "grammar_entry": [{"on i386": [{"on amd64": ["foo"]}, {"else": ["bar"]}]}],
        "arch": "i386",
        "target_arch": "amd64",
        "expected_results": ["bar"],
    },
    # try
    {
        "grammar_entry": [{"try": ["valid"]}],
        "arch": "amd64",
        "target_arch": "amd64",
        "expected_results": ["valid"],
    },
    # try else
    {
        "grammar_entry": [{"try": ["invalid"]}, {"else": ["valid"]}],
        "arch": "amd64",
        "target_arch": "amd64",
        "expected_results": ["valid"],
    },
    # nested try
    {
        "grammar_entry": [{"on amd64": [{"try": ["foo"]}, {"else": ["bar"]}]}],
        "arch": "amd64",
        "target_arch": "amd64",
        "expected_results": ["foo"],
    },
    # nested try else
    {
        "grammar_entry": [{"on i386": [{"try": ["invalid"]}, {"else": ["bar"]}]}],
        "arch": "i386",
        "target_arch": "i386",
        "expected_results": ["bar"],
    },
    # optional
    {
        "grammar_entry": ["foo", {"try": ["invalid"]}],
        "arch": "i386",
        "target_arch": "i386",
        "expected_results": ["foo"],
    },
    # multi
    {
        "grammar_entry": [
            "foo",
            {"on amd64": ["foo2"]},
            {"on amd64 to arm64": ["foo3"]},
        ],
        "arch": "amd64",
        "target_arch": "i386",
        "expected_results": ["foo", "foo2"],
    },
    # multi-ordering
    {
        "grammar_entry": [
            "foo",
            {"on amd64": ["on-foo"]},
            "after-on",
            {"on amd64 to i386": ["on-to-foo"]},
            {"on amd64 to arm64": ["no-show"]},
            "n-1",
            "n",
        ],
        "arch": "amd64",
        "target_arch": "i386",
        "expected_results": [
            "foo",
            "on-foo",
            "after-on",
            "on-to-foo",
            "n-1",
            "n",
        ],
    },
    # complex nested dicts
    {
        "grammar_entry": [
            {"yes1": "yes1"},
            {
                "on amd64": [
                    {"yes2": "yes2"},
                    {"on amd64": [{"yes3": "yes3"}]},
                    {"yes4": "yes4"},
                    {"on i386": [{"no1": "no1"}]},
                    {"else": [{"yes5": "yes5"}]},
                    {"yes6": "yes6"},
                ],
            },
            {"else": [{"no2": "no2"}]},
            {"yes7": "yes7"},
            {"on i386": [{"no3": "no3"}]},
            {"else": [{"yes8": "yes8"}]},
            {
                "yes9": "yes9",
                "yes10": "yes10",
            },
            {
                "on riscv64": [
                    {"no3": "no3"},
                ],
            },
        ],
        "arch": "amd64",
        "target_arch": "amd64",
        "expected_results": [
            {"yes1": "yes1"},
            {"yes2": "yes2"},
            {"yes3": "yes3"},
            {"yes4": "yes4"},
            {"yes5": "yes5"},
            {"yes6": "yes6"},
            {"yes7": "yes7"},
            {"yes8": "yes8"},
            {"yes9": "yes9", "yes10": "yes10"},
        ],
    },
]


@pytest.mark.parametrize("scenario", scenarios)
def test_basic_grammar(scenario):
    processor = GrammarProcessor(
        arch=scenario["arch"],
        target_arch=scenario["target_arch"],
        checker=lambda x: "invalid" not in x,
    )
    assert (
        processor.process(grammar=scenario["grammar_entry"])
        == scenario["expected_results"]
    )


transformer_scenarios = [
    # unconditional
    {
        "grammar_entry": ["foo", "bar"],
        "arch": "amd64",
        "expected_results": ["foo", "bar"],
    },
    # mixed including
    {
        "grammar_entry": ["foo", {"on i386": ["bar"]}],
        "arch": "i386",
        "expected_results": ["foo", "bar"],
    },
    # mixed excluding
    {
        "grammar_entry": ["foo", {"on i386": ["bar"]}],
        "arch": "amd64",
        "expected_results": ["foo"],
    },
    # to
    {
        "grammar_entry": [{"to i386": ["foo"]}],
        "arch": "amd64",
        "expected_results": ["foo:i386"],
    },
    # transform applies to nested
    {
        "grammar_entry": [{"to i386": [{"on amd64": ["foo"]}]}],
        "arch": "amd64",
        "expected_results": ["foo:i386"],
    },
    # not to
    {
        "grammar_entry": [{"to amd64": ["foo"]}, {"else": ["bar"]}],
        "arch": "amd64",
        "expected_results": ["bar"],
    },
]


@pytest.mark.parametrize("scenario", transformer_scenarios)
def test_grammar_with_transformer(scenario):
    # Transform all 'to' statements to include arch
    def transformer(call_stack, package_name, target_arch):
        if (
            any(isinstance(s, ToStatement) for s in call_stack)
            and ":" not in package_name
        ):
            package_name = f"{package_name}:{target_arch}"

        return package_name

    processor = GrammarProcessor(
        arch=scenario["arch"],
        target_arch="i386",
        checker=lambda x: True,
        transformer=transformer,
    )

    assert (
        processor.process(grammar=scenario["grammar_entry"])
        == scenario["expected_results"]
    )


error_scenarios = [
    # unmatched else
    {
        "grammar_entry": [{"else": ["foo"]}],
        "expected_exception": ".*'else' doesn't seem to correspond.*",
    },
    # unmatched else fail
    {
        "grammar_entry": ["else fail"],
        "expected_exception": ".*'else' doesn't seem to correspond.*",
    },
]


@pytest.mark.parametrize("scenario", error_scenarios)
def test_invalid_grammar(scenario):
    processor = GrammarProcessor(
        arch="amd64",
        target_arch="amd64",
        checker=lambda x: True,
    )

    with pytest.raises(errors.GrammarSyntaxError) as error:
        processor.process(grammar=scenario["grammar_entry"])

    assert re.match(scenario["expected_exception"], str(error.value))
