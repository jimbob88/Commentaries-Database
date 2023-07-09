# Commentaries-Database

To compile these files into a single data object, use the "compile_data.py" script in this repository. It's a python3 script, and requires you
to `pip install rtoml` first. You can select CSV, SQLITE, or JSON as the output format (resulting in a new file called data.json, data.csv, or
data.sqlite).

Invoke it like so:

```
python3 compile_data.py csv -o data.csv
python3 compile_data.py sqlite -o data.sqlite
python3 compile_data.py json -o data.json
```

The full argument system can be seen here:

```commandline
$ python compile_data.py --help
usage: CompileData [-h] [-o OUT] {json,csv,sqlite,dryrun}

Compiles the Commentaries Database into various formats

positional arguments:
  {json,csv,sqlite,dryrun}

optional arguments:
  -h, --help            show this help message and exit
  -o OUT, --out OUT
```

[Here is our reference implementation](https://github.com/HistoricalChristianFaith/Commentaries-Interface) of the sqlite file being utilized in a
simple PHP app to show commentaries for a user-specified passage of the Bible.

Want to make a contribution to the repository? See below for details on file formats, and
see [this pull request](https://github.com/HistoricalChristianFaith/Commentaries-Database/pull/1) for an example. We use the pull request feature to
add notes/discussion about sources and such.

## Creating a SWORD Module

If you wish to create a module which works on [SWORD-based applications](https://crosswire.org/applications/), you can generate an OSIS file
using `compile_osis.py`. This can then export an OSIS xml `python compile_osis.py -o data.xml`.

Then create a new folder hierarchy like so:

```
module/
├─ RC_HistoricalChristianCommentaries/
├─ data.xml
```

Move into the `module` directory with a terminal and execute (if you do not have a copy of `osis2mod` you can download a copy
of [Xiphos](https://xiphos.org/) on Windows, or install it from your linux package repository):

```commandline
$ osis2mod ./RC_HistoricalChristianCommentaries data.xml -e 1
OR
>  osis2mod.exe .\RC_HistoricalChristianCommentaries\ .\data.xml -e 1
```

You should now have a folder hierarchy like so:

```
module/
├─ RC_HistoricalChristianCommentaries/
│  ├─ nt
│  ├─ nt.vss
│  ├─ ot
│  ├─ ot.vss
├─ data.xml
```

Move these files into a new directory path `RC_HistoricalChristianCommentaries->modules->comments->rawcom->RC_HistoricalChristianCommentaries` like
so:

```
module/
├─ RC_HistoricalChristianCommentaries/
│  ├─ modules/
│  │  ├─ comments/
│  │  │  ├─ rawcom/
│  │  │  │  ├─ RC_HistoricalChristianCommentaries/
│  │  │  │  │  ├─ ot.vss
│  │  │  │  │  ├─ ot
│  │  │  │  │  ├─ nt.vss
│  │  │  │  │  ├─ nt
├─ data.xml
```

Now create a new directory in the `RC_HistoricalChristianCommentaries` directory called `mods.d` and an empty file in it
called `RC_HistoricalChristianCommentaries.conf`.

```
module/
├─ RC_HistoricalChristianCommentaries/
│  ├─ modules/
│  │  ├─ comments/
│  │  │  ├─ rawcom/
│  │  │  │  ├─ RC_HistoricalChristianCommentaries/
│  │  │  │  │  ├─ ot.vss
│  │  │  │  │  ├─ ot
│  │  │  │  │  ├─ nt.vss
│  │  │  │  │  ├─ nt
│  ├─ mods.d/
│  │  ├─ RC_HistoricalChristianCommentaries.conf
├─ data.xml
```

Edit `RC_HistoricalChristianCommentaries.conf` and write:

```ini
[RC_HistoricalChristianCommentaries]
DataPath=./modules/comments/rawcom/RC_HistoricalChristianCommentaries/
ModDrv=RawCom
SourceType=OSIS
Lang=en
Description=The Historical Christian Commentaries database ported to SWORD
About=Various Christian Commentaries
LCSH=Bible--Commentaries.
Version=1.0
Encoding=UTF-8
```

Then either zip the `RC_HistoricalChristianCommentaries` folder and install it with a SWORD manager or copy the `modules` and `mods.d` folders to your SWORD modules directory.

## FILE NAME FORMATS:

```
[Father-Name]/[Book-Name] Chapter_Verse.toml
[Father-Name]/[Book-Name] Chapter_Verse-Verse.toml
[Father-Name]/[Book-Name] Chapter_Verse-Chapter_Verse.toml
```

Examples:

- A commentary by Augustine on Matthew 23:35 = Filename: `Augustine/Matthew 23_35.toml`
- A commentary by Jerome on Matthew 23:35-41 = Filename: `Jerome/Matthew 23_35-41.toml`
- A commentary by Basil of Caesarea on 1 Kings 19:10-20:3 = Filename: `Basil of Caesarea/1 Kings 19_10-20_3.toml`

So the basic rule is write the 'long form' name of everything (books/people), and replace colons (:) with underscores (_). That's it.

<details>
    <summary><b>Why do we use the long form of people's names? Why Augustine of Hippo, rather than just Augustine?</b></summary>

The reason for this is simple enough - In his Catena Aurea, Aquinas lists "Maximus" as the author for several commentaries.

On a Maximus commentary of Luke 3:7-9, Aquinas prefixes the quotation with "lib. Ascet.", which easily enough points to Liber Asceticus, a writing
by [Maximus the Confessor](https://en.wikipedia.org/wiki/Maximus_the_Confessor#Writings).

However on a Maximus commentary on Luke 2:8-12 and Matthew 3:1-3, Aquinas prefixes the quotations with "in Serm. Nativ. 4." and "Hom. in Joan. Bap.
nat. 1." - and it does not appear Maximus the Confessor left us any sermons or
homilies [among his writings](https://en.wikipedia.org/wiki/Maximus_the_Confessor#Writings). However Maximus of
Turin [left many of both](https://en.wikipedia.org/wiki/Maximus_of_Turin#Works), and is likely these source for these commentaries Aquinas quoted.

Having to dig into problems like that increase the rate at which my gray hair grows, therefore we seek the most descriptive names possible for each
person in this repo.

We also accept that for some people, it is not possible/necessary. For example, `Jerome` is universally understood to refer to a single man, and he
doesn't have any kind of commonly known longer-form name. However, while `Augustine` is universally understood to refer to a single man, he does have
a common longer-form name which we therefore use, `Augustine of Hippo`.
</details>

Why Psalms instead of Psalm?

We're standardizing on [these names](https://github.com/HistoricalChristianFaith/Example-Commentary-Api/blob/master/func.php#L82), which are basically
just based off of [this Logos page](https://www.logos.com/bible-book-abbreviations).

## File Contents Format

Each file is in a format called [TOML](https://github.com/toml-lang/toml). This format fits well, as it's a nice balance of human readable/editable
and machine-readable.

A single file can contain multiple "commentaries".

A "commentary" consists of:

- Mandatory keys
    - `quote`: The source quotation, can include unicode as HTML entities but should not include any html
    - `sources`: One or more "url" and "title" values, should always include at least one source.
- Optional keys
    - `append_to_author_name`: Use this for things like when you are quoting from a secondary source, e.g. if Aquinas said that Jerome said something,
      put the quote under Jerome, but in append_to_author_name put the value " (as quoted by Aquinas, AD 1274)"
    - `time`: The year A.D. that the writing was written. Use a negative value for B.C. Should be just a single numerical value. If not supplied,
      defaults to metadata.toml's value (which is often the death year of the Church Father)

Minimal Example:

```
[[commentary]]
quote = '''
commentary by a church father goes here.
'''
[[commentary.sources]]
url = 'https://example.com'
title = 'Name of book church father wrote'
```

Kitchen-Sink Example:

```
[[commentary]]
quote = '''
short quotation from a church father with multiple sources
'''
append_to_author_name = ' (as quoted by Aquinas, AD 1274)'

[[commentary.sources]]
url='https://www.ecatholic2000.com/catena/untitled-111.shtml'
title='Catena Aurea by Aquinas'

[[commentary.sources]]
url='https://ccel.org/ccel/aquinas/catena1/catena1.i.html'
title='Catena Aurea by Aquinas'

[[commentary]]
quote = '''
Long quotation from a church father

This text is on a new line
'''
time = 383

[[commentary.sources]]
url = 'https://www.newadvent.org/fathers/3007.htm'
title = 'Against Helvidius'
```

## Useful Tools

#### Sites that have many church father texts available for free online:

* https://www.ccel.org/
* https://www.newadvent.org/fathers/
* https://www.tertullian.org/fathers/ and https://www.tertullian.org/fathers2/
* https://earlychristianwritings.com/churchfathers.html
* https://catholiclibrary.org/library/browse/ [*Contains many Latin versions not available in English]
* https://www.mlat.uzh.ch/browser?path=/38 [Migne's Patrologia Latina] [Link2](https://www.roger-pearse.com/weblog/patrologia-latina-pl-volumes-available-online/) [Link3](https://docs.google.com/spreadsheets/d/e/2PACX-1vRkUFBfVVqv5Tr2aZS4apFNpTJ-ys6VqeQxgsAI1v7cH5putIgchYWJAVGHuu0lWGmdD2DU7Vb1o7XH/pubhtml#)
* https://roger-pearse.com/wiki/index.php?title=Main_Page [Encyclopedia of Syriac Literature]
* https://github.com/OpenGreekAndLatin/csel-dev/ [Corpus Scriptorum Ecclesiasticorum Latinorum: a machine-corrected EpiDoc version of public domain volumes of the monumental collection of Latin Church Fathers]

#### Other Electronic Catenas

* https://catenabible.com/mt/1/1
* https://www.biblindex.org/en/story
* https://www.earlychristianwritings.com/e-catena/
* https://www.catholiccrossreference.online/fathers/index.php/matthew%201:1
* [$$$] https://www.logos.com/product/31152/ancient-christian-commentary-on-scripture-complete-set-updated-edition-accs
