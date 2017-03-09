# pyfwf3 - Fixed-Width Field File Format parser and tools

Lib to help you handle those files that joins all data relying only on the lenght of each field.
I made this for myself because I was having some bad times to filter and debug data from some huge stock market files with hundreds of thousands of lines.


### When should I use this?

When you have files like this:
```
USAR19570526Fbe56008be36eDianne Mcintosh WhateverMedic        
USMI19940213M706a6e0afc3dRosalyn Clark   WhateverComedian     
USWI19510403M451ed630accbShirley Gray    WhateverComedian     
USMD20110508F7e5cd7324f38Georgia Frank   WhateverComedian     
USPA19930404Mecc7f17c16a6Virginia LambertWhateverShark tammer 
USVT19770319Fd2bd88100facRichard Botto   WhateverTime traveler
USOK19910917F9c704139a6e3Alberto Giel    WhateverStudent      
USNV20120604F5f02187599d7Mildred Henke   WhateverSuper hero   
USRI19820125Fcf54b2eb5219Marc Kidd       WhateverMedic        
USME20080503F0f51da89a299Kelly Crose     WhateverComedian     
...
```
where each line represents one dataset and the data is concatenated on that line.

### Why should I use this?

Even though parsing this kind of file is pretty easy you may want to filter some of its data. Also this lib helps you to visualize you data and play with it directly on python shell.
So that file will easily become this:
```
+------------------+--------+------------+----------+-------+----------+---------------+-----+
| name             | gender | birthday   | location | state | universe | profession    | age |
+------------------+--------+------------+----------+-------+----------+---------------+-----+
| Dianne Mcintosh  | F      | 1957-05-26 | US       | AR    | Whatever | Medic         | 60  |
| Rosalyn Clark    | M      | 1994-02-13 | US       | MI    | Whatever | Comedian      | 23  |
| Shirley Gray     | M      | 1951-04-03 | US       | WI    | Whatever | Comedian      | 66  |
| Georgia Frank    | F      | 2011-05-08 | US       | MD    | Whatever | Comedian      | 6   |
| Virginia Lambert | M      | 1993-04-04 | US       | PA    | Whatever | Shark tammer  | 24  |
| Richard Botto    | F      | 1977-03-19 | US       | VT    | Whatever | Time traveler | 40  |
| Alberto Giel     | F      | 1991-09-17 | US       | OK    | Whatever | Student       | 26  |
| Mildred Henke    | F      | 2012-06-04 | US       | NV    | Whatever | Super hero    | 5   |
| Marc Kidd        | F      | 1982-01-25 | US       | RI    | Whatever | Medic         | 35  |
| Kelly Crose      | F      | 2008-05-03 | US       | ME    | Whatever | Comedian      | 9   |
+------------------+--------+------------+----------+-------+----------+---------------+-----+
```

### Features
- Parse and objectify your file
- Filter objects using a django-like syntax
- Reorganize your data
- Vizualization as table (thanks to [terminaltables](https://robpol86.github.io/terminaltables/))
- Order by column
- Add or remove columns
- Count a subset
- Uniqueness of data on a column

### TODOs
- Recursive special filters like: birthday__year__lt
- Filter with same line like: .filter(start_day=L("end_day"))
- Multi-column order like: .order_by("-age", "name")
- Values using special fields like: .values("name__len")
- Order using special fields like: .order_by("birthday__year")
- Export methods like: .sqlite file or .sql file
- Write a fixed-width field file (?)(why would someone write those files?)


# Usage

## Setting up your parser
First thing you need to know is the width of each column on your file. There's no magic here. You will need to find out.

Lets take [this file](https://github.com/nano-labs/pyfwf3/blob/master/examples/humans.txt) as example. Here its first line:
```
US       AR19570526Fbe56008be36eDianne Mcintosh         Whatever    Medic        
```
By testing, splitting, trying or whatever I know that:
- First 9 characters are reserved for that person location
- Next 2 characters are for her state
- Next 8 are her birthday
- Next 1 is her gender
- Next 12 I dont have a clue and I dont care
- Next 24 are her name

and so on. But I only want name, birthday and gender so let's write it's model

```python
from pyfwf3 import BaseLineParser


class Human(BaseLineParser):
    """Parser for each line of that humans.txt file."""

    _map = {"name": slice(32, 56),
            "gender": slice(19, 20),
            "birthday": slice(11, 19)}
```

The slices represents the first and last positions of each information in the line and that's the most basic line parser you need. Now we are going to use it with the file parser.

```python
from pytwt3 import BaseFileParser

parsed = BaseFileParser.open("examples/humnas.txt", line_parser=Human)
```

That's it. Your file is parsed and now usable but let's put it together:

```python
from pyfwf3 import BaseLineParser, BaseFileParser


class Human(BaseLineParser):
    """Parser for each line of that humans.txt file."""

    _map = {"name": slice(32, 56),
            "gender": slice(19, 20),
            "birthday": slice(11, 19)}


parsed = BaseFileParser.open("examples/humnas.txt", line_parser=Human)
```
or even
```python
from pyfwf3 import BaseLineParser, BaseFileParser


class Human(BaseLineParser):
    """Parser for each line of that humans.txt file."""

    _map = {"name": slice(32, 56),
            "gender": slice(19, 20),
            "birthday": slice(11, 19)}


class HumanFileParser(BaseFileParser):
    """Parser for that humans.txt file."""

    _line_parser = Human

parsed = HumanFileParser.open("examples/humans.txt")
```
We will discuss those classes in the [future](#BaseLineParser)


## Queryset

With your parsed file as a BaseFileParser instance you have all lines stored as a Queryset instance in ".lines" attribute. So:

```pycon
>>> parsed = HumanFileParser.open("examples/humans.txt")
>>> # slices returns a smaller queryset instance
>>> parsed.lines[0:5]
+------------------+----------+--------+
| name             | birthday | gender |
+------------------+----------+--------+
| Dianne Mcintosh  | 19570526 | F      |
| Rosalyn Clark    | 19940213 | M      |
| Shirley Gray     | 19510403 | M      |
| Georgia Frank    | 20110508 | F      |
| Virginia Lambert | 19930404 | M      |
+------------------+----------+--------+
>>> # while getting a specific item returns a parsed line instance
>>> parsed.lines[327]
+------------+----------+--------+
| name       | birthday | gender |
+------------+----------+--------+
| Jack Brown | 19490106 | M      |
+------------+----------+--------+
>>> # Note that the table is only a shell representation of the objects
>>> parsed.lines[327].name
'Jack Brown'
>>> parsed.lines[327].birthday
'19490106'
>>> parsed.lines[327].gender
'M'
>>> tuple(parsed.lines[327])
('M', 'Jack Brown', '19490106')
>>> list(parsed.lines[327])
['M', 'Jack Brown', '19490106']
>>> # To prevent the fields from changing order use OrderedDict instead of dict on _map. More about that later
```

### .filter(**kwargs)

Here is where the magic happens. A filtered queryset will always return a new queryset that can be filtered too and so and so
```pycon
>>> parsed = HumanFileParser.open("examples/humans.txt")
>>> first5 = parsed.lines[:5]
>>> # 'first5' is a Queryset instance just as 'parsed.lines' but with only a few lines
>>> firts5
+------------------+----------+--------+
| name             | birthday | gender |
+------------------+----------+--------+
| Dianne Mcintosh  | 19570526 | F      |
| Rosalyn Clark    | 19940213 | M      |
| Shirley Gray     | 19510403 | M      |
| Georgia Frank    | 20110508 | F      |
| Virginia Lambert | 19930404 | M      |
+------------------+----------+--------+
>>> # And it still can be filtered
>>> first5.filter(gender="F")
+------------------+----------+--------+
| name             | birthday | gender |
+------------------+----------+--------+
| Dianne Mcintosh  | 19570526 | F      |
| Georgia Frank    | 20110508 | F      |
+------------------+----------+--------+
>>> # with multiple keywords arguments
>>> firts5.filter(gender="M", birthday__gte="19900101")
+------------------+----------+--------+
| name             | birthday | gender |
+------------------+----------+--------+
| Rosalyn Clark    | 19940213 | M      |
| Virginia Lambert | 19930404 | M      |
+------------------+----------+--------+
>>> # or chained filters
>>> firts5.filter(name__endswith="k").filter(gender=F)
+------------------+----------+--------+
| name             | birthday | gender |
+------------------+----------+--------+
| Georgia Frank    | 20110508 | F      |
+------------------+----------+--------+
```
Some special filters may be used with __ notation. Here are some but not limited to:
- __in: value is in a list
- __lt: less than
- __lte: less than or equals
- __gt: greater than
- __gte: greater than or equals
- __ne: not equals
- __len: field lenght (without trailing spaces)
- __startswith: value starts with that string
- __endswith: value ends with that string

It will actually look for any attribute or method of the field object that matches with __'object.somefilter'__ or __'object.\_\_somefilter\_\_'__ and call it or compare with it. So let's say that you use the [_after_parse()](#_after_parse()) method to convert the __'birthday'__ field into __datetime.date__ instances you can now filter using, for example, __.filter(birthday\_\_year=1957)__

### .exclude(**kwargs)

Pretty much the opposite of [.filter()](#.filter(**kwargs))
```pycon
>>> parsed = HumanFileParser.open("examples/humans.txt")
>>> first5 = parsed.lines[:5]
>>> firts5
+------------------+----------+--------+
| name             | birthday | gender |
+------------------+----------+--------+
| Dianne Mcintosh  | 19570526 | F      |
| Rosalyn Clark    | 19940213 | M      |
| Shirley Gray     | 19510403 | M      |
| Georgia Frank    | 20110508 | F      |
| Virginia Lambert | 19930404 | M      |
+------------------+----------+--------+
>>> first5.exclude(gender="F")
+------------------+----------+--------+
| name             | birthday | gender |
+------------------+----------+--------+
| Rosalyn Clark    | 19940213 | M      |
| Shirley Gray     | 19510403 | M      |
| Virginia Lambert | 19930404 | M      |
+------------------+----------+--------+
```

### .order_by(field_name, reverse=False)

Reorder the whole queryset sorting by that given field
```pycon
>>> parsed = HumanFileParser.open("examples/humans.txt")
>>> parsed.lines[:5]
+------------------+----------+--------+
| name             | birthday | gender |
+------------------+----------+--------+
| Dianne Mcintosh  | 19570526 | F      |
| Rosalyn Clark    | 19940213 | M      |
| Shirley Gray     | 19510403 | M      |
| Georgia Frank    | 20110508 | F      |
| Virginia Lambert | 19930404 | M      |
+------------------+----------+--------+
>>> parsed.lines[:5].order_by("name")
+------------------+--------+----------+
| name             | gender | birthday |
+------------------+--------+----------+
| Dianne Mcintosh  | F      | 19570526 |
| Georgia Frank    | F      | 20110508 |
| Rosalyn Clark    | M      | 19940213 |
| Shirley Gray     | M      | 19510403 |
| Virginia Lambert | M      | 19930404 |
+------------------+--------+----------+
>>> parsed.lines[:5].order_by("name", reverse=True)
+------------------+--------+----------+
| name             | gender | birthday |
+------------------+--------+----------+
| Virginia Lambert | M      | 19930404 |
| Shirley Gray     | M      | 19510403 |
| Rosalyn Clark    | M      | 19940213 |
| Georgia Frank    | F      | 20110508 |
| Dianne Mcintosh  | F      | 19570526 |
+------------------+--------+----------+
```
TODO: Order by more than one field and order by special field


### .unique(field_name)

Return a list o unique values for that field. For this example I will use complete line parser for that humans.txt file
```python
from collections import OrderedDict
from pyfwf3 import BaseLineParser, BaseFileParser


class CompleteHuman(BaseLineParser):
    """Complete line parser for humans.txt example file."""

    _map = OrderedDict(
        [
            ("name", slice(32, 56)),
            ("gender", slice(19, 20)),
            ("birthday", slice(11, 19)),
            ("location", slice(0, 9)),
            ("state", slice(9, 11)),
            ("universe", slice(56, 68)),
            ("profession", slice(68, 81)),
        ]
    )


class CompleteHumanFileParser(BaseFileParser):
    """Complete file parser for humans.txt example file."""

    _line_parser = CompleteHuman

```
```pycon
>>> parsed = CompleteHumanFileParser.open("examples/humans.txt")
>>> parsed.lines[:5]
+------------------+--------+----------+----------+-------+----------+--------------+
| name             | gender | birthday | location | state | universe | profession   |
+------------------+--------+----------+----------+-------+----------+--------------+
| Dianne Mcintosh  | F      | 19570526 | US       | AR    | Whatever | Medic        |
| Rosalyn Clark    | M      | 19940213 | US       | MI    | Whatever | Comedian     |
| Shirley Gray     | M      | 19510403 | US       | WI    | Whatever | Comedian     |
| Georgia Frank    | F      | 20110508 | US       | MD    | Whatever | Comedian     |
| Virginia Lambert | M      | 19930404 | US       | PA    | Whatever | Shark tammer |
+------------------+--------+----------+----------+-------+----------+--------------+
>>> # Looking into all lines
>>> parsed.lines.unique("gender")
['F', 'M']
>>> parsed.lines.unique("profession")
['', 'Time traveler', 'Student', 'Berserk', 'Hero', 'Soldier', 'Super hero', 'Shark tammer', 'Artist', 'Hunter', 'Cookie maker', 'Comedian', 'Mecromancer', 'Programmer', 'Medic', 'Siren']
>>> parsed.lines.unique("state")
['', 'MT', 'WA', 'NY', 'AZ', 'MD', 'LA', 'IN', 'IL', 'WY', 'OK', 'NJ', 'VT', 'OH', 'AR', 'FL', 'DE', 'KS', 'NC', 'NM', 'MA', 'NH', 'ME', 'CT', 'MS', 'RI', 'ID', 'HI', 'NE', 'TN', 'AL', 'MN', 'TX', 'WV', 'KY', 'CA', 'NV', 'AK', 'IA', 'PA', 'UT', 'SD', 'CO', 'MI', 'VA', 'GA', 'ND', 'OR', 'SC', 'WI', 'MO']
```
TODO: Unique by special field

### .count()

Return how many lines there are on that queryset

```pycon
>>> parsed = CompleteHumanFileParser.open("examples/humans.txt")
>>> # Total
>>> parsed.lines.count()
10012
>>> # How many are women
>>> parsed.lines.filter(gender="F").count()
4979
>>> # How many womans from New York or California
>>> parsed.lines.filter(gender="F", state__in=["NY", "CA"]).count()
197
>>> # How many mens born on 1960 or later
>>> parsed.lines.filter(gender="M").exclude(birthday__lt="19600101").count()
4321
```

