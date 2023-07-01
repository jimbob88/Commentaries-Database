import argparse
from collections.abc import Iterable
from pathlib import Path

from compile_data import Commentary, VerseRange, generate_father_metadata, process_toml_file
from string import Template

ot_abbr = {
    "Genesis": "Gen",
    "Exodus": "Exod",
    "Leviticus": "Lev",
    "Numbers": "Num",
    "Deuteronomy": "Deut",
    "Joshua": "Josh",
    "Judges": "Judg",
    "Ruth": "Ruth",
    "1 Samuel": "1Sam",
    "2 Samuel": "2Sam",
    "1 Kings": "1Kgs",
    "2 Kings": "2Kgs",
    "1 Chronicles": "1Chr",
    "2 Chronicles": "2Chr",
    "Ezra": "Ezra",
    "Nehemiah": "Neh",
    "Esther": "Esth",
    "Job": "Job",
    "Psalms": "Ps",
    "Psalm": "Ps",
    "Proverbs": "Prov",
    "Ecclesiastes": "Eccl",
    "Song of Solomon": "Song",
    "Isaiah": "Isa",
    "Jeremiah": "Jer",
    "Lamentations": "Lam",
    "Ezekiel": "Ezek",
    "Daniel": "Dan",
    "Hosea": "Hos",
    "Joel": "Joel",
    "Amos": "Amos",
    "Obadiah": "Obad",
    "Jonah": "Jonah",
    "Micah": "Mic",
    "Nahum": "Nah",
    "Habakkuk": "Hab",
    "Zephaniah": "Zeph",
    "Haggai": "Hag",
    "Zechariah": "Zech",
    "Malachi": "Mal"
}

nt_abbr = {
    "Matthew": "Matt",
    "Mark": "Mark",
    "Luke": "Luke",
    "John": "John",
    "Acts": "Acts",
    "Romans": "Rom",
    "1 Corinthians": "1Cor",
    "2 Corinthians": "2Cor",
    "Galatians": "Gal",
    "Ephesians": "Eph",
    "Philippians": "Phil",
    "Colossians": "Col",
    "1 Thessalonians": "1Thess",
    "2 Thessalonians": "2Thess",
    "1 Timothy": "1Tim",
    "2 Timothy": "2Tim",
    "Titus": "Titus",
    "Philemon": "Phil",
    "Hebrews": "Heb",
    "James": "Jas",
    "1 Peter": "1Pet",
    "2 Peter": "2Pet",
    "1 John": "1John",
    "2 John": "2John",
    "3 John": "3John",
    "Jude": "Jude",
    "Revelation": "Rev"
}

dc_abbr = {
    "Tobit": "Tob",
    "Judith": "Jdt",
    "Wisdom": "Wis",
    "Sirach": "Sir",
    "Baruch": "Bar",
    "1 Maccabees": "1Macc",
    "2 Maccabees": "2Macc",
    "3 Maccabees": "3Macc",
    "4 Maccabees": "4Macc",
    "1 Esdras": "1Esd",
    "2 Esdras": "2Esd",
    "Prayer of Azariah": "PrAzar"
}

all_abbr = {**ot_abbr, **nt_abbr, **dc_abbr}

osis_text = Template("""
<?xml version="1.0" encoding="UTF-8"?>
<osis
	xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
	xmlns="http://www.bibletechnologies.net/2003/OSIS/namespace"
	xmlns:osis="http://www.bibletechnologies.net/2003/OSIS/namespace"
	xsi:schemaLocation="http://www.bibletechnologies.net/2003/OSIS/namespace http://www.bibletechnologies.net/osisCore.2.1.1.xsd">
	<osisText osisIDWork="historicalChristianFaith" osisRefWork="Commentary" xml:lang="en" canonical="true">
		<header>
			<titleHistorical Christian Commentaries</title>
		</header>
		<div type="bookGroup">
			$commentaries
		</div>
	</osisText>
</osis>
""")


def verse_range_to_annotate_ref(book_name: str, vr: VerseRange) -> str:
    book_abbr = all_abbr[book_name.strip()]
    if vr.start_chapter == vr.end_chapter and vr.start_verse == vr.end_verse:
        return f"{book_abbr}.{vr.start_chapter}.{vr.start_verse}"

    return f"{book_abbr}.{vr.start_chapter}.{vr.start_verse}-{book_abbr}.{vr.end_chapter}.{vr.end_verse}"


def verse_range_to_reference(book_name: str, vr: VerseRange) -> str:
    """Converts a verse range and book name to John 3:16-17 or John 4:11-5:1"""
    if vr.start_chapter == vr.end_chapter:
        if vr.start_verse == vr.end_verse:
            return f"{book_name.strip()} {vr.start_chapter}:{vr.start_verse}"
        return f"{book_name.strip()} {vr.start_chapter}:{vr.start_verse}-{vr.end_verse}"

    return f"{book_name.strip()} {vr.start_chapter}:{vr.start_verse}-{vr.end_chapter}:{vr.end_verse}"


def commentary_to_title_xml(commentary: Commentary) -> str:
    c_text = '<title type="sub">'
    if commentary.date > 0:
        c_text += f"<i>[{commentary.date} AD]</i> "
    elif commentary.date < 0:
        c_text += f"<i>[BC {commentary.date}]</i> "

    c_text += f'{commentary.father_name}'
    if commentary.append_to_author_name:
        c_text += f" {commentary.append_to_author_name}"
    c_text += f" on {verse_range_to_reference(commentary.bible_book_name, commentary.bible_verse_range)}"
    c_text += '</title>'
    return c_text


def commentary_to_xml(commentary: Commentary) -> str:
    c_text = ""
    try:
        c_text += f'<div type="section" annotateType="commentary" annotateRef="{verse_range_to_annotate_ref(commentary.bible_book_name, commentary.bible_verse_range)}">'
    except BaseException as e:
        print(commentary, e)

    c_text += commentary_to_title_xml(commentary)

    c_text += f'<p>{commentary.txt}</p>'

    if commentary.source_title.strip():
        c_text += f'<p>{commentary.source_title.strip()}</p>'
    
    c_text += '</div>'
    return c_text


def to_osis(commentaries: Iterable[Commentary]) -> str:
    """Converts a `list` of commentaries to the xml main div in an OSIS file."""
    return '\n'.join(commentary_to_xml(commentary) for commentary in commentaries)


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog='CompileOsis',
        description='Compiles the Commentaries Database into the OSIS format'
    )
    parser.add_argument('-o', '--out', type=Path, default=Path('data.xml'))
    return parser.parse_args()


def main(out: Path):
    file_list = [path for path in Path.cwd().glob('**/*') if path.is_file() and path.suffix == '.toml']
    father_meta_data = generate_father_metadata(file for file in file_list if file.name == 'metadata.toml')

    # Then loop through all files, load them into an object
    commentary_data = [commentary
                       for toml in file_list if toml.name != 'metadata.toml'
                       for commentary in process_toml_file(toml, father_meta_data)
                       ]
    commentaries_osis = to_osis(commentary_data)
    out.write_text(osis_text.substitute(commentaries=commentaries_osis), encoding='utf-8')


if __name__ == '__main__':
    args = parse_arguments()
    main(args.out)
