#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Parser humans."""

from datetime import datetime
from pyfwf3.parser import BaseLineParser, OrderedDict


class HumanLP(BaseLineParser):

    _map = OrderedDict(
        [
            ("name", slice(32, 56)),
            ("sex", slice(19, 20)),
            ("birthday", slice(11, 19)),
            ("location", slice(0, 9)),
            ("state", slice(9, 11)),
            ("universe", slice(56, 68)),
            ("profession", slice(68, 81)),
        ]
    )

    def _after_parse(self):
        try:
            self.birthday = datetime.strptime(self.birthday, "%Y%m%d").date()
        except ValueError:
            self.birthday = datetime(1900, 1, 1).date()
        self.age = datetime.today().year - self.birthday.year
