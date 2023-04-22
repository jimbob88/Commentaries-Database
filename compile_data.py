import sys
import os
import json
import sqlite3
import csv
from pathlib import Path
import rtoml
import uuid


def process_toml():
    file_list = [path for path in Path.cwd().glob('**/*') if path.is_file() and path.suffix == '.toml']

    father_meta_data = {}

    # First loop through all metadata files, build them up into default lookup table
    total_file_count = 0
    for file in file_list:
        # Pseudo-Jerome/Mark 6_35-44.toml
        short_file_name = file.relative_to(Path.cwd())
        if short_file_name.name == 'metadata.toml':
            toml_str = file.read_text()
            toml_obj = rtoml.load(toml_str)
            father_meta_data[file.parent.name] = toml_obj
        elif file.suffix == '.toml':
            total_file_count += 1

    data_values = []

    # Then loop through all files, load them into an object
    current_file_count = 0
    for file in file_list:
        try:
            if file.name == 'metadata.toml':
                continue

            for i in range(10):
                if current_file_count == int(total_file_count * (0.1 * i)):
                    print(f"{i}0% done ({current_file_count} / {total_file_count})")
            current_file_count += 1
            father_name = file.parent.name
            fn = file.stem
            fn_pieces = fn.split(" ")
            verse_pieces = fn_pieces[-1].split("-")
            book_name = " ".join(fn_pieces[:-1])

            start_verse = verse_pieces[0]
            start_verse_pieces = start_verse.split("_")
            start_verse_CHAPTER = start_verse_pieces[0]
            start_verse_VERSE = start_verse_pieces[1]
            end_verse_CHAPTER = start_verse_pieces[0]
            end_verse_VERSE = start_verse_pieces[1]

            if len(verse_pieces) > 1:
                # There is an ending verse
                endverse_pieces = verse_pieces[1].split("_")
                if len(endverse_pieces) == 2:
                    # 19_24
                    end_verse_CHAPTER = endverse_pieces[0]
                    end_verse_VERSE = endverse_pieces[1]
                else:
                    # 19, borrows chapter from starting verse
                    end_verse_VERSE = endverse_pieces[0]

            location_start = (int(start_verse_CHAPTER) * 1000000) + int(start_verse_VERSE)
            location_end = (int(end_verse_CHAPTER) * 1000000) + int(end_verse_VERSE)

            # print(father_name + " / " + book_name + " / " + start_verse_CHAPTER + " / " + start_verse_VERSE + " / " + end_verse_CHAPTER + " / " + end_verse_VERSE + "|||" + str(location_start) + "/" + str(location_end))

            toml_str = file.read_text(encoding='utf-8')
            toml_obj = rtoml.load(toml_str)

            for c in toml_obj['commentary']:
                source_url = ""
                source_title = ""
                if 'sources' in c:
                    source_url = c['sources'][0]['url']
                    source_title = c['sources'][0]['title']

                time = 9999999
                if father_name in father_meta_data:
                    time = father_meta_data[father_name]['default_year']
                if 'time' in c:
                    time = c['time']

                append_to_author_name = ""
                if 'append_to_author_name' in c:
                    append_to_author_name = c['append_to_author_name']
                data_values.append([
                    str(uuid.uuid4()),
                    father_name,
                    file.name,
                    append_to_author_name,
                    time,
                    book_name.lower().replace(" ", ""),
                    location_start,
                    location_end,
                    c['quote'],
                    source_url,
                    source_title
                ])
        except BaseException as error:
            print("******Error in", file)
            print("Error Reads: ", error)
            raise
    print("*Files processed: " + str(current_file_count))
    formatted_father_meta_data = []
    for fn in father_meta_data:
        formatted_father_meta_data.append([
            fn,
            father_meta_data[fn]['default_year'],
            father_meta_data[fn]['wiki'],
        ])
    return {
        "father_meta_data": formatted_father_meta_data,
        "commentary_data": data_values
    }


def output_sqlite():
    database_file_location = 'data.sqlite'
    if os.path.isfile(database_file_location):
        os.remove(database_file_location)

    try:
        sqliteConnection = sqlite3.connect(database_file_location)
        cursor = sqliteConnection.cursor()

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

        toml_data = process_toml()
        sqlite_insert_query = """INSERT INTO father_meta
                            (name, default_year, wiki_url) 
                            VALUES (?, ?, ?);"""
        cursor.executemany(sqlite_insert_query, toml_data['father_meta_data'])
        sqlite_insert_query = """INSERT INTO commentary
                            (id, father_name, file_name, append_to_author_name, ts, book, location_start, location_end, txt, source_url, source_title) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
        cursor.executemany(sqlite_insert_query, toml_data['commentary_data'])
        sqliteConnection.commit()
        print("Total", cursor.rowcount, "Records inserted successfully")
        sqliteConnection.commit()
        cursor.close()

    except sqlite3.Error as error:
        print("Error:", error)
    finally:
        if sqliteConnection:
            sqliteConnection.close()


def output_json():
    final_data = []
    for d in process_toml()['commentary_data']:
        final_data.append({
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
        })
    with open('data.json', 'w') as f:
        json.dump(final_data, f)


def output_csv():
    data = process_toml()['commentary_data']
    writer = csv.writer(Path('data.csv').open('w', encoding='utf-8'))
    writer.writerow(["id", "father_name", "file_name", "append_to_author_name", "ts", "book", "location_start", "location_end", "txt", "source_url",
                     "source_title"])
    for row in data:
        writer.writerow(row)


def main():
    if len(sys.argv) != 2:
        print(f'Usage: python3 {sys.argv[0]} <output_format>')
        print("\t[Where output_format is one of: SQLITE, JSON, CSV, DRYRUN]")
        return

    output_format = sys.argv[1].lower().strip()
    if (output_format == 'json'):
        print("Compiling into JSON...")
        output_json()
    elif (output_format == 'csv'):
        print("Compiling into CSV...")
        output_csv()
    elif (output_format == 'sqlite'):
        print("Compiling into SQLITE...")
        output_sqlite()
    else:  # dryrun
        print("Dryrun...")
        process_toml()


if __name__ == '__main__':
    main()
