from xml.sax.saxutils import escape
from misc import config
from misc.utils import Paper


def escape_xml(text: str) -> str:
    """Escape special characters in the text in order to support the xml format."""
    return escape(
        text,
        entities={"'": "&apos;", "\"": "&quot;"}
    )


def gen_entry(paper: Paper) -> str:
    """Convert a paper into a xml style paper entry."""
    authors_entry = ""
    for author in paper.authors:
        authors_entry += f"<author><name>{author}</name></author>"

    return f'<entry> ' \
           f'<id>{escape_xml(paper.link)}</id>' \
           f'<title>{escape_xml(paper.title)}</title> ' \
           f'<summary>{escape_xml(paper.abstract.strip())} </summary> ' \
           f'{authors_entry} ' \
           f'<link href="{escape_xml(paper.link)}" rel="alternate" type="text/html"/>  ' \
           f'<link title="pdf" href="{escape_xml(paper.link)}" rel="related" type="application/pdf"/>' \
           f'</entry>'


def gen_atom_feed(papers: list[Paper]) -> str:
    """Generate the atom feed based on the paper list."""
    entries = []
    for paper in papers:
        entries.append(gen_entry(paper))

    entries = "\n".join(entries)

    return f'<?xml version="1.0" encoding="UTF-8"?> ' \
           f'<feed xmlns="http://www.w3.org/2005/Atom"> ' \
           f'{entries} ' \
           f'</feed>'


def create_atom_feed(papers: list[Paper], result_file_name=None, conference=None, year=None) -> None:
    """Create an atom feed file (xml format) and store it."""
    atom_feed = gen_atom_feed(papers)

    if result_file_name:
        file_name = result_file_name
    elif conference and year:
        file_name = f"{conference}_{year}.xml"
    else:
        file_name = "feed.xml"

    with open(f"{config.result_feed_folder}/{file_name}", "w", encoding="utf-8") as f:
        f.write(atom_feed)

