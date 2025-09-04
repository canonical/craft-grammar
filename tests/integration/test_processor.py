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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pathlib
import re
from copy import deepcopy
from typing import Any, cast

import pytest
import yaml
from craft_grammar import GrammarProcessor, Variant, errors

_DATA_FILES_PATH = pathlib.Path(__file__).parent / "data"
VALID_DATA_FILES_PATH = _DATA_FILES_PATH / "valid"
INVALID_DATA_FILES_PATH = _DATA_FILES_PATH / "invalid"


# Values that should return as a single object / list / dict.
NON_SCALAR_VALUES = [
    "build-packages",
    "organize",
]

# Values that should return a dict, not in a list.
DICT_ONLY_VALUES = [
    "organize",
]


def self_check(value: Any) -> bool:
    return bool(
        value == value  # pylint: disable=comparison-with-itself  # noqa: PLR0124
    )


def process_data(
    *, data: dict[str, Any], processor: GrammarProcessor
) -> dict[str, Any]:
    """Process grammar in a dict of data."""
    data = deepcopy(data)

    for key, value in data.items():
        unprocessed_grammar = value

        # grammar aware models can be strings or list of dicts and strings
        if isinstance(unprocessed_grammar, list):
            unprocessed_grammar = cast(list[dict[str, Any] | str], unprocessed_grammar)
        # grammar aware models can be a string
        elif isinstance(unprocessed_grammar, str):
            unprocessed_grammar = [unprocessed_grammar]
        # skip all other data types
        else:
            continue

        processed_grammar = processor.process(grammar=unprocessed_grammar)

        if processor.variant == Variant.FOR_VARIANT:
            # special cases:
            # - scalar values should return as a single object, not in a list.
            # - dict values should return as a dict, not in a list.
            if key in DICT_ONLY_VALUES:
                processed_grammar = {
                    k: v for d in processed_grammar for k, v in d.items()
                }
                if not processed_grammar:
                    processed_grammar = None
            elif key not in NON_SCALAR_VALUES:
                processed_grammar = processed_grammar[0] if processed_grammar else None  # type: ignore[assignment]
        elif key not in NON_SCALAR_VALUES or key in DICT_ONLY_VALUES:
            processed_grammar = processed_grammar[0] if processed_grammar else None  # type: ignore[assignment]

        data[key] = processed_grammar

    return data


@pytest.mark.parametrize("platform", ["platform1", "platform2", "platform3"])
def test_for(platform):
    """Process the `for` statement."""
    data = yaml.safe_load((VALID_DATA_FILES_PATH / "for.yaml").read_text())
    expected_data = yaml.safe_load(
        (VALID_DATA_FILES_PATH / f"for.for-{platform}.yaml").read_text()
    )
    processor = GrammarProcessor(
        checker=self_check, arch="amd64", target_arch="riscv64", platforms=[platform]
    )

    processed_data = process_data(data=data, processor=processor)

    assert processed_data == expected_data


@pytest.mark.parametrize(
    ("arch", "target_arch"),
    [
        ("amd64", "riscv64"),
        ("amd64", "s390x"),
        ("arm64", "arm64"),
    ],
)
def test_on_to(arch, target_arch):
    """Process `on` and `to` statements."""
    data = yaml.safe_load((VALID_DATA_FILES_PATH / "on-and-to.yaml").read_text())
    expected_data = yaml.safe_load(
        (
            VALID_DATA_FILES_PATH / f"on-and-to.on-{arch}-to-{target_arch}.yaml"
        ).read_text()
    )
    processor = GrammarProcessor(checker=self_check, arch=arch, target_arch=target_arch)

    processed_data = process_data(data=data, processor=processor)

    assert processed_data == expected_data


@pytest.mark.parametrize(
    "filename",
    [
        "for-and-to",
        "for-and-on",
        "for-and-else",
    ],
)
def test_variant_error(filename):
    """Error when two variants of grammar are used."""
    data = yaml.safe_load((INVALID_DATA_FILES_PATH / f"{filename}.yaml").read_text())
    expected_error = re.escape(
        "Invalid grammar syntax: The 'for' statement can't be used with other grammar statements."
    )
    processor = GrammarProcessor(
        checker=self_check, arch="amd64", target_arch="riscv64", platforms=["platform1"]
    )

    with pytest.raises(errors.GrammarSyntaxError, match=expected_error):
        process_data(data=data, processor=processor)
