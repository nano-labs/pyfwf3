#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Parsers for fixed width fields file format."""

from decimal import Decimal
from collections import OrderedDict
from terminaltables import AsciiTable


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

    map = OrderedDict()

    def __init__(self, line, line_number=None):
        """Parse and objectify this line."""
        self._original_line = line
        self._line_number = str(line_number) if line_number else None
        self.before_parse()
        for k, v in self.map.items():
            self.__setattr__(k, self._original_line[v].rstrip())
        self.after_parse()

    def before_parse(self):
        """Method called before any parse is done."""
        pass

    def after_parse(self):
        """Method called after parsing is done."""
        pass

    def __repr__(self):
        """Shell line representation."""
        return repr(ValuesList([self.values()], headers=self.map.keys()))

    def values(self, *args):
        """Return a value or list of values of this line."""
        args = args or self.map.keys()
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
            args = args or self._parent_.line_parser.map.keys()
            if len(args) == 1:
                data = [l.__getattribute__(args[0]) for l in self.lines]
            else:
                data = [l.values(*args) for l in self.lines]
            return ValuesList(data, headers=args)

        def filter(self, **kwargs):
            """Filter lines based on fields.

            Special filter may be used with __ notation.
                Available special filters:
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
                or any of "issomething" methods of string objects such as
                    __isdigit, __issupper, __isalnum
            Ex:
                Get people that name is not empty and are 18 years old or older
                    people = persons.filter(name__ne="", age__gte=18)
                Now from those people get only womens
                    womens = people.filter(sex="F")
                And from those get the ones who lives in Texas or New York
                    womens = womens.filter(state__in=["TX", "NY"])
            """
            matches = self._filter_validations(kwargs)
            return self.new([l for l in self.lines
                             if all([v(l.__getattribute__(k))
                                     for k, v in matches])])

        def exclude(self, **kwargs):
            """Filter lines that DO NOT match the kwargs."""
            matches = self._filter_validations(kwargs)
            return self.new([l for l in self.lines
                             if not any([v(l.__getattribute__(k))
                                         for k, v in matches])])

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

        def __getitem__(self, *args, **kwargs):
            """Allow to get queryset slices."""
            return self.lines.__getitem__(*args, **kwargs)

        def __len__(self, *args, **kwargs):
            """Size of queryset."""
            return self.lines.__len__(*args, **kwargs)

        def __repr__(self):
            """Screen representation."""
            return repr(self.values())

        @staticmethod
        def _filter_validations(keywords):
            """Create a validation dict using filter keywords.

            Transform every key&value pair into a key&validation-lambda
            """
            matches = []
            for k, v in keywords.items():
                if "__" not in k:
                    matches.append((k, lambda x, v=v: x == v))
                    continue
                # else:
                field, method = k.split("__")
                keywords[field] = v
                keywords.pop(k)
                method = {"lte": "le", "gte": "ge"}.get(method, method)
                if method in ("len", "ne"):
                    method = "__{}__".format(method)
                    func = lambda x, v=v, m=method: x.__getattribute__(m)(v)

                elif method == "in":
                    func = lambda x, v=v: x in v

                elif method in ("gt", "lt", "le", "ge"):
                    method = "__{}__".format(method)
                    func = lambda x, v=v, m=method: Decimal(x).__getattribute__(m)(Decimal(v)) if x else False

                elif method.startswith("is") and isinstance(v, bool):
                    func = lambda x, v=v, m=method: x.__getattribute__(m)() == v

                else:
                    func = lambda x, v=v, m=method: x.__getattribute__(m)(v)

                matches.append((field, func))
            return matches

    line_parser = BaseLineParser

    def __init__(self, file_discriptor, line_parser=None):
        """Create instance using a file discriptor as input.

        May use a custom line parser object
        """
        self.line_parser = line_parser or self.line_parser
        line_number = 0
        lines = []
        for l in file_discriptor.readlines():
            line_number += 1
            if l:
                lines.append(self.line_parser(l, line_number))
        self.lines = lines

    @classmethod
    def open(cls, filename, line_parser=None):
        """Open this file and parse it."""
        f = open(filename, "r")
        parsed = cls(f, line_parser=None)
        f.close()
        return parsed

    def filter(self, *args, **kwargs):
        """Return a filtered queryset."""
        return self.QuerySet(self.lines, self).filter(*args, **kwargs)

    def exclude(self, *args, **kwargs):
        """Return a filtered queryset."""
        return self.QuerySet(self.lines).exclude(*args, **kwargs)

    def values(self, *args):
        """Return a list or list of lists that contains that values."""
        return self.QuerySet(self.lines).values(*args)

    def count(self):
        """Return given file line count."""
        return self.QuerySet(self.lines).count()

    def all(self):
        """Return a queryset with all lines."""
        return self.QuerySet(self.lines).filter(*args, **kwargs)

    def __getitem__(self, key):
        """Allow to get queryset slices."""
        if isinstance(key, slice):
            return self.QuerySet(self.lines.__getitem__(key))
        return self.lines.__getitem__(key)


class PROHLineParser(BaseLineParser):
    """Line Parser com mapa para o arquivo PROH."""

    map = {"event_type": slice(52, 54),
           "asset": slice(2, 14),
           "distribution_number": slice(14, 17),
           "value": slice(77, 95),
           "destination_asset": slice(113, 125),
           "new_distribution_number": slice(125, 128),
           "cod_isin_dir": slice(143, 155),
           "prec_pap_subs": slice(158, 176),
           "data_lim_subs": slice(176, 184),
           "payment_date": slice(184, 192),
           "execution_date": slice(333, 341),
           "sequence_number": slice(341, 348),
           "cod_neg": slice(17, 29),
           "cod_isin_ori": slice(128, 140)}


class PROHFileParser(BaseFileParser):
    """
    File Parser especifico para o PROH.

    Usage:
    In [1]: from utils.file_parsers import PROHFileParser
    In [2]: proh = PROHFileParser("/Users/nano/Desktop/PROH_07021720170208083359")
    In [3]: proh.filter(cod_neg__startswith="PETR").count()
    Out[3]: 415
    In [4]: proh.filter(cod_neg__startswith="PETR").exclude(cod_neg="PETR4").unique("event_type")
    Out[4]: ['40', '14', '16', '30', '94', '13', '10', '90']
    In [5]: proh.filter(cod_neg__startswith="PETR").filter(execution_date__gte=20030130, execution_date__lt=20030230).count()
    Out[5]: 1
    In [6]: proh.filter(cod_neg__startswith="PETR").filter(execution_date__gte=20030130)[2]
    Out[6]:
    Linha: 56013
                  prec_pap_subs : 000000000000000000
                sequence_number : 0000003
                     event_type : 10
                          asset : BRPETRACNOR9
                 execution_date : 20030328
                   cod_isin_dir :
            distribution_number : 146
                   payment_date : 20030505
                        cod_neg : PETR3
                          value : 000000053000000000
                   cod_isin_ori :
        new_distribution_number : 000
              destination_asset :
                  data_lim_subs : 40001231
    """

    line_parser = PROHLineParser
