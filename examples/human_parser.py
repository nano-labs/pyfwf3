#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Parser humans."""

from datetime import datetime
from pyfwf3.parser import (BaseLineParser, BaseFileParser, OrderedDict,
                           InvalidLineError)


class HumanLineParser(BaseLineParser):
    """Line parser for humans.txt example file."""

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


class EnhancedHumanLineParser(HumanLineParser):
    """Adds some magic to the parser."""

    def _after_parse(self):
        """Customization on parsed line object."""
        try:
            # Parse birthday as date object
            self.birthday = datetime.strptime(self.birthday, "%Y%m%d").date()
        except ValueError:
            # Set birthday as 1900-01-01 as failover
            self.birthday = datetime(1900, 1, 1).date()

        # set a new attribute 'age'
        self.age = datetime.today().year - self.birthday.year

        # skip those who does not have a profession
        if not self.profession:
            raise InvalidLineError()


class TrumpLineParser(EnhancedHumanLineParser):
    """Line parser that does not allow non-US humans."""

    def _before_parse(self):
        """Skip any line that not starts with 'US'."""
        if not self._original_line.startswith("US"):
            raise InvalidLineError()


class AllCapsLineParser(EnhancedHumanLineParser):
    """Line parser that UPPERCASE EVERYTHING."""

    def _before_parse(self):
        """Put everything uppercased even before parse it."""
        self._original_line = self._original_line.upper()


class HumanParser(BaseFileParser):
    """File parser for humans.txt example file."""

    _line_parser = HumanLineParser
