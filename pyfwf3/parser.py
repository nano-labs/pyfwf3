#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Parsers for fixed width fields file format."""

from operator import eq as equals
from collections import OrderedDict
from terminaltables import AsciiTable


class InvalidLineError(Exception):
    """Some problem with this line. Line skipped."""

    pass


class ValuesList(list):
    """Extended list with better shell representation."""

    def __init__(self, *args, **kwargs):
        """Set the headers of the list."""
        headers = kwargs.pop("headers")
        super().__init__(*args, **kwargs)
        self._headers = list(headers)

    def __repr__(self):
        """Table-like shell representation."""
        table_data = [self._headers]
        if len(self) and not isinstance(self[0], tuple):
            table_data.extend([[i] for i in self])
        else:
            table_data.extend(self)
        return AsciiTable(table_data).table


class BaseLineParser:
    """Parser for each single line of file."""

    _map = OrderedDict()

    def __init__(self, line, line_number=None):
        """Parse and objectify this line."""
        self._parsable_line = None
        self._unparsed_line = line
        self._line_number = line_number
        self._headers = list(self._map.keys())
        self._before_parse()
        line = self._parsable_line or self._unparsed_line
        for k, v in self._map.items():
            self.__setattr__(k, line[v].rstrip())
        self._after_parse()

    def _update_headers(self):
        """Add any new attributes to headers."""
        new_headers = [attr for attr in dir(self) if not attr.startswith("_")]
        self._headers = sorted(new_headers,
                               key=(self._headers + sorted(new_headers)).index)

    def _before_parse(self):
        """Method called before any parse is done.

        raise InvalidLineError if you want to skip this line.
        """
        pass

    def _after_parse(self):
        """Method called after parsing is done.

        Raise InvalidLineError if you want to skip this line.
        Call self._update_headers() if you added some new attribute
        """
        pass

    def __repr__(self):
        """Shell line representation."""
        return repr(ValuesList([self._values()], headers=self._headers))

    def __iter__(self):
        """Line as a iterable. Allows to convert to list or tuples."""
        for v in self._values():
            yield v

    def _values(self, *args):
        """Return a value or list of values of this line."""
        args = args or self._headers
        return tuple([self.__getattribute__(arg) for arg in args])


class BaseFileParser:
    """Parser for a fixed width fields file."""

    class QuerySet:
        """Filtered subset of file lines."""

        def __init__(self, lines, parent=None):
            """Get lines and return a queryset object of that lines."""
            self.lines = lines
            self._parent_ = parent

        def new(self, lines):
            """Return a new queryset of same parent."""
            return self.__class__(lines, self._parent_)

        def values(self, *args):
            """Return a list or list of lists that contains that values."""
            # if not args and self.lines:
            #     args = self.lines[0].map.keys()
            # args = args or self._parent_._line_parser._get_headers()
            if len(args) == 1:
                data = [l.__getattribute__(args[0]) for l in self.lines]
            else:
                data = [l._values(*args) for l in self.lines]
            headers = self.lines[0]._headers if data and not args else args
            return ValuesList(data, headers=headers)

        @staticmethod
        def _filter_validators(keywords):
            """Create a validation list using filter keywords.

            Return [
                (<line field name>, <function pointer>, <function args tuple>),
                ...
            ]
            """
            def attr_comparisons(obj, attr, value):
                """Lookup for object's method or attribute and compare.

                obj: field value from a line
                attr: attribute of that object to compare
                value: value to compare with object's attribute
                """
                if attr == "in":
                    return obj in value

                # translate 'somemethod' to '__somemethod__' if exists
                if (not hasattr(obj, attr) and
                        hasattr(obj, "__{}__".format(attr))):
                    attr = "__{}__".format(attr)
                # else: let it raise exception

                obj_attr = obj.__getattribute__(attr)
                if callable(obj_attr):
                    try:
                        # for cases that expect arguments
                        # Ex: .__gt__() or .startswith()
                        return bool(obj_attr(value))
                    except TypeError:
                        # for cases that DONT expect arguments
                        # Ex: .__len__() or .isalpha()
                        return obj_attr() == value
                # for cases that the attribute is not callable
                # Ex: .real (on int and float) or .day (on datetime)
                return obj_attr == value

            validators = []
            for field, value in keywords.items():
                if "__" not in field:
                    validators.append((field, equals, (value,)))

                else:
                    real_field, field_attr = field.split("__")
                    field_attr = {"lte": "le",
                                  "gte": "ge"}.get(field_attr, field_attr)
                    validators.append((real_field, attr_comparisons,
                                       (field_attr, value)))
            return validators

        def filter(self, **kwargs):
            """Filter lines based on fields.

            Special filter may be used with __ notation.
                Some special filters are but not limited to:
                __lt: less than
                __lte: less than or equals
                __le: less than or equals
                __gt: greater than
                __gte: greater than or equals
                __ge: greater than or equals
                __ne: not equals
                __len: field lenght (without trailing spaces)
                __startswith: value starts with that string
                __endswith: value ends with that string
                __in: value is in a list

            It will actually look for any attribute or method of the field
            object that matches with 'object.somefilter' or
            'object.__somefilter__' and call it or compare with it

            Ex:
                Get people that name is not empty and are 18 years old or older
                    people = persons.filter(name__ne="", age__gte=18)
                Now from those people get only womens
                    womens = people.filter(sex="F")
                And from those get the ones who lives in Texas or New York
                    womens = womens.filter(state__in=["TX", "NY"])

                And let's say that you use the _before_parse() method to
                turn the 'birthday' field into a datetime object. Now you
                may filter for womens that was born on july 4th
                    womens = womens.filter(birthday__month=7, birthday__day=4)
            """
            validators = self._filter_validators(kwargs)
            return self.new(
                [
                    l for l in self.lines
                    if all(
                        [
                            function(l.__getattribute__(field), *args)
                            for field, function, args in validators
                        ]
                    )
                ]
            )

        def exclude(self, **kwargs):
            """Filter lines that DO NOT match the kwargs."""
            validators = self._filter_validators(kwargs)
            return self.new(
                [
                    l for l in self.lines
                    if not any(
                        [
                            function(l.__getattribute__(field), *args)
                            for field, function, args in validators
                        ]
                    )
                ]
            )

        def order_by(self, field, reverse=False):
            """Order lines by fields."""
            return self.new(
                sorted(self.lines, key=lambda x: x.__getattribute__(field),
                       reverse=reverse))

        def count(self):
            """Size of queryset."""
            return len(self)

        def unique(self, *args):
            """List of unique values for that fields."""
            return list(set(self.values(*args)))

        def __getitem__(self, index):
            """Allow to get queryset slices."""
            if isinstance(index, slice):
                return self.new(self.lines.__getitem__(index))
            else:
                return self.lines.__getitem__(index)

        def __len__(self, *args, **kwargs):
            """Size of queryset."""
            return self.lines.__len__(*args, **kwargs)

        def __repr__(self):
            """Screen representation."""
            return repr(self.values())

    _line_parser = BaseLineParser

    def __init__(self, file_discriptor, line_parser=None):
        """Create instance using a file discriptor as input.

        May use a custom line parser object
        """
        self._line_parser = line_parser or self._line_parser
        line_number = 0
        lines = []
        for l in file_discriptor.readlines():
            line_number += 1
            if l:
                try:
                    lines.append(self._line_parser(l, line_number))
                except InvalidLineError:
                    pass
        self.lines = self.QuerySet(lines, self)

    @classmethod
    def open(cls, filename, line_parser=None):
        """Open this file and parse it."""
        f = open(filename, "r")
        parsed = cls(f, line_parser)
        f.close()
        return parsed

    def all(self):
        """Return a queryset with all lines."""
        return self.lines
