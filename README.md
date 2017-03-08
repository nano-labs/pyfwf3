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
- Vizualization as table
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


## Usage

### Setting you parser
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
and so on. But I only what name, birthday and gender so let's write it's model

```python
from pyfwf3 import BaseLineParser

class Human(BaseLineParser):

    _map = {"name": slice(32, 56),
            "gender": slice(19, 20),
            "birthday": slice(11, 19)}
```

The slices represents the start and finnish positions of each information in the line.
Thats the most basic line parser you need. Now we are going to use it with the file parser.

```python
from pytwt3 import BaseFileParser

parsed = BaseFileParser.open("example/humnas.txt", line_parser=Human)
```

That's it. Your file is parsed and now usable. Let's put it together:

```python
from pyfwf3 import BaseLineParser, BaseFileParser

class Human(BaseLineParser):

    _map = {"name": slice(32, 56),
            "gender": slice(19, 20),
            "birthday": slice(11, 19)}

parsed = BaseFileParser.open("example/humnas.txt", line_parser=Human)
```
or even
```python
from pyfwf3 import BaseLineParser, BaseFileParser

class Human(BaseLineParser):

    _map = {"name": slice(32, 56),
            "gender": slice(19, 20),
            "birthday": slice(11, 19)}

class HumanFileParser(BaseFileParser):

    _line_parser = Human

parsed = HumanFileParser.open("example/humnas.txt")
```
