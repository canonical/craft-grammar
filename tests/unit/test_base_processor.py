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
"""Unit tests for the base processor."""

import pytest
from craft_grammar._base_processor import BaseProcessor
from craft_grammar._types import Grammar
from craft_grammar.errors import PlatformNameError
from typing_extensions import Any, override


class _StubProcessor(BaseProcessor):
    @override
    def process(self, *, grammar: Grammar, call_stack: Any | None = None) -> list[Any]:
        return []


@pytest.mark.parametrize("platforms", [{"any"}])
def test_platform_name_error(platforms):
    with pytest.raises(PlatformNameError):
        _StubProcessor(arch="riscv64", target_arch="s390x", platforms=platforms)


def test_platforms_include_any():
    proc = _StubProcessor(arch="riscv64", target_arch="s390x", platforms=set())
    assert proc.platforms
    assert "any" in proc.platforms


def test_platforms_none_by_default():
    proc = _StubProcessor(arch="riscv64", target_arch="s390x")
    assert proc.platforms is None
