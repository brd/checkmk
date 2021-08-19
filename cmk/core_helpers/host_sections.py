#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from __future__ import annotations

import abc
from typing import cast, Final, Generic, Mapping, Optional, Sequence, Tuple, TypeVar

from cmk.utils.type_defs import HostName, SectionName

from cmk.core_helpers.cache import TRawDataSection

THostSections = TypeVar("THostSections", bound="HostSections")


class HostSections(Generic[TRawDataSection], metaclass=abc.ABCMeta):
    """Host informations from the sources."""
    def __init__(
        self,
        sections: Optional[Mapping[SectionName, TRawDataSection]] = None,
        *,
        cache_info: Optional[Mapping[SectionName, Tuple[int, int]]] = None,
        # For `piggybacked_raw_data`, Sequence[bytes] is equivalent to AgentRawData.
        piggybacked_raw_data: Optional[Mapping[HostName, Sequence[bytes]]] = None,
    ) -> None:
        super().__init__()
        self.sections: Final = sections if sections else {}
        self.cache_info: Final = cache_info if cache_info else {}
        self.piggybacked_raw_data: Final = piggybacked_raw_data if piggybacked_raw_data else {}

    def __repr__(self):
        return "%s(sections=%r, cache_info=%r, piggybacked_raw_data=%r)" % (
            type(self).__name__,
            self.sections,
            self.cache_info,
            self.piggybacked_raw_data,
        )

    def __add__(self, other: HostSections) -> HostSections:
        new_sections = dict(self.sections)
        for section_name, section_content in other.sections.items():
            new_sections.setdefault(
                section_name,
                cast(TRawDataSection, []),
            ).extend(section_content)

        new_piggybacked_raw_data = dict(self.piggybacked_raw_data)
        for hostname, raw_lines in other.piggybacked_raw_data.items():
            list(new_piggybacked_raw_data.setdefault(hostname, [])).extend(raw_lines)

        # TODO: It should be supported that different sources produce equal sections.
        # this is handled for the self.sections data by simply concatenating the lines
        # of the sections, but for the self.cache_info this is not done. Why?
        # TODO: checking._execute_check() is using the oldest cached_at and the largest interval.
        #       Would this be correct here?
        new_cache_info = dict(self.cache_info)
        new_cache_info.update(other.cache_info)

        return HostSections(
            new_sections,
            cache_info=new_cache_info,
            piggybacked_raw_data=new_piggybacked_raw_data,
        )
