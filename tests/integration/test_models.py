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

"""Integration tests for the Grammar model."""

import pathlib

import pydantic
import pytest
import yaml
from craft_grammar.models import Grammar

_DATA_FILES_PATH = pathlib.Path(__file__).parent / "data"
VALID_DATA_FILES_PATH = _DATA_FILES_PATH / "valid"


class GrammarModel(pydantic.BaseModel):
    """A simple grammar model."""

    model_config = pydantic.ConfigDict(
        validate_assignment=True,
        extra="forbid",
        alias_generator=lambda s: s.replace("_", "-"),
        populate_by_name=True,
    )

    plugin: str | None = None
    source_branch: Grammar[str] | None = None
    build_packages: Grammar[list[str]] | None = None
    organize: Grammar[dict[str, str]] | None = None


@pytest.mark.parametrize(
    "filename",
    [
        "for",
        "on-and-to",
    ],
)
def test_validate_models(filename):
    """Validate valid models."""
    data = yaml.safe_load((VALID_DATA_FILES_PATH / f"{filename}.yaml").read_text())
    expected_data = yaml.safe_load(
        (VALID_DATA_FILES_PATH / f"{filename}.validated.yaml").read_text()
    )

    model = GrammarModel.model_validate(data)

    assert model.model_dump(by_alias=True) == expected_data
