import sys
import os
import json
import sqlite3
import csv
from pathlib import Path
import rtoml
from tqdm import tqdm
import uuid
from typing import List, NamedTuple, Dict, Union
from collections.abc import Iterator, Iterable
import re
import argparse


class VerseRange(NamedTuple):
    start_chapter: int
    start_verse: int
    end_chapter: int
    end_verse: int


def string_to_verse_range(verse_string: str) -> VerseRange:
    """

    :param verse_string: A verse string i.e. 1_57-58 or 1_57-2_32
    :return:
    """
    verse_pieces = re.split('[_-]', verse_string)
    start_chapter = verse_pieces[0]
    start_verse = verse_pieces[1]
    if len(verse_pieces) == 2:
        # i.e. 1_56
        end_chapter = start_chapter
        end_verse = start_verse
    elif len(verse_pieces) == 3:
        # i.e. 1_57-57
        end_chapter = start_chapter
        end_verse = verse_pieces[2]
    elif len(verse_pieces) == 4:
        # i.e. 1_57-2_32
        end_chapter = verse_pieces[2]
        end_verse = verse_pieces[3]
    else:
        raise ValueError(f'Unexpected format of verse_string: {verse_string}')

    return VerseRange(
        start_chapter=int(start_chapter),
        start_verse=int(start_verse),
        end_chapter=int(end_chapter),
        end_verse=int(end_verse)
    )


def encode_chapter_verse(chapter: int, verse: int) -> int:
    return (chapter * 1000000) + verse


class PathMetadata(NamedTuple):
    father_name: str
    bible_book_name: str
    bible_verse_range: VerseRange


def path_to_metadata(toml_path: Path) -> PathMetadata:
    father_name = toml_path.parent.name

    fn_pieces = toml_path.stem.split(" ")
    book_name = " ".join(fn_pieces[:-1])
    verse_range = string_to_verse_range(fn_pieces[-1])

    return PathMetadata(father_name, book_name, verse_range)


def commentary_date(father_name: str, father_meta_data: Dict, commentary: Dict, default=9999999) -> int:
    """Calculates the date of the commentary"""
    date = default
    if father_name in father_meta_data:
        date = father_meta_data[father_name]['default_year']
    date = commentary.get('time', date)
    return date


class Commentary(NamedTuple):
    filename: str
    father_name: str
    bible_book_name: str
    bible_verse_range: VerseRange
    source_url: str
    source_title: str
    date: int
    append_to_author_name: str
    txt: str


def process_toml_file(toml_path: Path, father_meta_data) -> Union[Iterator[Commentary], None]:
    """Extracts all the commentaries from a toml file"""
    path_metadata = path_to_metadata(toml_path)

    toml_str = toml_path.read_text(encoding='utf-8')
    try:
        toml_obj = rtoml.load(toml_str)
    except rtoml.TomlParsingError as e:
        print(f"{toml_path} failed because:", e)
        return iter(())

    for commentary in toml_obj['commentary']:
        source_url = commentary['sources'][0]['url'] if 'sources' in commentary else ""
        source_title = commentary['sources'][0]['title'] if 'sources' in commentary else ""
        date = commentary_date(path_metadata.father_name, father_meta_data, commentary)
        append_to_author_name: str = commentary.get('append_to_author_name', '')

        yield Commentary(
            filename=toml_path.name,
            father_name=path_metadata.father_name.strip(),
            bible_book_name=path_metadata.bible_book_name.strip(),
            bible_verse_range=path_metadata.bible_verse_range,
            source_url=source_url.strip(),
            source_title=source_title.strip(),
            date=date,
            append_to_author_name=append_to_author_name.strip(),
            txt=commentary['quote'].strip()
        )


def commentary_to_row(commentary: Commentary) -> List:
    location_start = encode_chapter_verse(commentary.bible_verse_range.start_chapter, commentary.bible_verse_range.start_verse)
    location_end = encode_chapter_verse(commentary.bible_verse_range.end_chapter, commentary.bible_verse_range.end_verse)
    return [
        str(uuid.uuid4()),
        commentary.father_name,
        commentary.filename,
        commentary.append_to_author_name,
        commentary.date,
        commentary.bible_book_name.lower().replace(" ", ""),
        location_start,
        location_end,
        commentary.txt,
        commentary.source_url,
        commentary.source_title
    ]


def generate_father_metadata(metadata_tomls: Iterable[Path]) -> Dict[str, Dict]:
    father_meta_data = {}
    for file in metadata_tomls:
        toml_str = file.read_text()
        toml_obj = rtoml.load(toml_str)
        father_meta_data[file.parent.name] = toml_obj
    return father_meta_data


def process_tomls_to_rows():
    file_list = [path for path in Path.cwd().glob('**/*') if path.is_file() and path.suffix == '.toml']
    father_meta_data = generate_father_metadata(file for file in file_list if file.name == 'metadata.toml')

    # Then loop through all files, load them into an object
    commentary_data = [commentary_to_row(commentary)
                       for toml in file_list if toml.name != 'metadata.toml'
                       for commentary in process_toml_file(toml, father_meta_data)
                       ]

    formatted_father_meta_data = [
        [
            fn,
            father_meta_data[fn]['default_year'],
            father_meta_data[fn]['wiki'],
        ] for fn in father_meta_data
    ]
    return {
        "father_meta_data": formatted_father_meta_data,
        "commentary_data": commentary_data
    }


def to_sqlite(toml_data: Dict, out_path: Path):
    if out_path.is_file():
        os.remove(out_path)

    sqlite_connection = None

    try:
        sqlite_connection = sqlite3.connect(out_path)
        cursor = sqlite_connection.cursor()

        cursor.execute('''CREATE TABLE IF NOT EXISTS "father_meta" (
            "name" VARCHAR,
            "default_year" VARCHAR,
            "wiki_url" VARCHAR
        )
        ;''')
        cursor.execute('''CREATE UNIQUE INDEX idx_father_meta_name ON father_meta (name);''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS "commentary" (
            "id" VARCHAR,
            "father_name" VARCHAR,
            "file_name" VARCHAR,
            "append_to_author_name" VARCHAR,
            "ts" INTEGER,
            "book" VARCHAR,
            "location_start" INTEGER,
            "location_end" INTEGER,
            "txt" TEXT,
            "source_url" VARCHAR,
            "source_title" VARCHAR
        )
        ;''')
        cursor.execute('''CREATE UNIQUE INDEX idx_commentary_id ON commentary (id);''')
        cursor.execute('''CREATE INDEX idx_commentary_book ON commentary (book);''')
        cursor.execute('''CREATE INDEX idx_commentary_location_start ON commentary (location_start);''')
        cursor.execute('''CREATE INDEX idx_commentary_location_end ON commentary (location_end);''')

        sqlite_insert_query = """INSERT INTO father_meta
                            (name, default_year, wiki_url) 
                            VALUES (?, ?, ?);"""
        cursor.executemany(sqlite_insert_query, toml_data['father_meta_data'])
        sqlite_insert_query = """INSERT INTO commentary
                            (id, father_name, file_name, append_to_author_name, ts, book, location_start, location_end, txt, source_url, source_title) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        cursor.executemany(sqlite_insert_query, toml_data['commentary_data'])
        sqlite_connection.commit()
        print("Total", cursor.rowcount, "Records inserted successfully")
        sqlite_connection.commit()
        cursor.close()

    except sqlite3.Error as error:
        print("Error:", error)
    finally:
        if sqlite_connection:
            sqlite_connection.close()


def to_json(toml_data: Dict, out_path: Path):
    final_data = [
        {
            "id": d[0],
            "father_name": d[1],
            "file_name": d[2],
            "append_to_author_name": d[3],
            "ts": d[4],
            "book": d[5],
            "location_start": d[6],
            "location_end": d[7],
            "txt": d[8],
            "source_url": d[9],
            "source_title": d[10],
        }
        for d in toml_data['commentary_data']
    ]
    json.dump(final_data, out_path.open('w'))


def to_csv(toml_data: Dict, out_path: Path):
    data = toml_data['commentary_data']
    writer = csv.writer(out_path.open('w', encoding='utf-8'))
    writer.writerow(["id", "father_name", "file_name", "append_to_author_name", "ts", "book", "location_start", "location_end", "txt", "source_url",
                     "source_title"])
    for row in data:
        writer.writerow(row)


def parse_arguments():
    parser = argparse.ArgumentParser(
        prog='CompileData',
        description='Compiles the Commentaries Database into various formats'
    )

    parser.add_argument('output_format', choices=['json', 'csv', 'sqlite', 'dryrun'], default='dryrun')
    parser.add_argument('-o', '--out', type=Path, default=Path('data.out'))
    return parser.parse_args()


def main():
    args = parse_arguments()

    print('Starting to Compile')
    toml_data = process_tomls_to_rows()
    if args.output_format == 'json':
        print("Saving into JSON...")
        to_json(toml_data, args.out)
    elif args.output_format == 'csv':
        print("Saving into CSV...")
        to_csv(toml_data, args.out)
    elif args.output_format == 'sqlite':
        print("Saving into SQLITE...")
        to_sqlite(toml_data, args.out)
    else:  # dryrun
        print("Dryrun finished")


if __name__ == '__main__':
    main()
