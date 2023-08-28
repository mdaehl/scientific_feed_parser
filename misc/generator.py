from xml.sax.saxutils import escape
from misc import config


def escape_xml(text):
    return escape(
        text,
        entities={"'": "&apos;", "\"": "&quot;"}
    )


def gen_entry(page):
    authors_entry = ""
    for author in page.authors:
        authors_entry += f"<author><name> {author} </name></author>"

    return f'<entry> ' \
           f'<id> {page.link} </id>' \
           f'<title> {escape_xml(page.title)} </title> ' \
           f'<summary>{escape_xml(page.abstract)} </summary> ' \
           f'{authors_entry} ' \
           f'<link href="{page.link}" rel="alternate" type="text/html"/>  ' \
           f'<link title="pdf" href="{page.link}" rel="related" type="application/pdf"/>' \
           f'</entry>'


def gen_atom_feed(papers):
    entries = []
    for paper in papers:
        entries.append(gen_entry(paper))

    entries = "\n".join(entries)

    return f'<?xml version="1.0" encoding="UTF-8"?> ' \
           f'<feeds xmlns="http://www.w3.org/2005/Atom"> ' \
           f'{entries} ' \
           f'</feeds>'


def create_atom_feed(papers, conference=None, year=None):
    print("Generate and save atom feeds.")
    atom_feed = gen_atom_feed(papers)

    if conference and year:
        file_name = f"{conference}_{year}"
    else:
        file_name = "feeds"

    with open(f"{config.result_feed_folder}/{file_name}.xml", "w", encoding="utf-8") as f:
        f.write(atom_feed)

