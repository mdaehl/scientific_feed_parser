from misc import utils, generator
import os
from parsers.feeds import html, parser
from parsers.feeds.sources import process
from tqdm import tqdm


class Feed:
    """Class to handle the feed related tasks."""
    def __init__(self, source: str, target: str, online: bool, appending: bool) -> None:
        self.source = source
        self.target = target
        self.online = online
        self.appending = appending
        self.feed_parser = self.init_feedparser()
        self.papers = []

    def init_feedparser(self) -> parser.FeedParser:
        """Initialize the feed parser which processes the source file."""
        if not self.online and not os.path.isfile(self.source):
            raise FileNotFoundError(f"Could not fine the file with path {self.source}")
        else:
            return parser.FeedParser(self.source, self.target, self.online, self.appending)

    def get_papers(self) -> None:
        """Retrieve all papers from the feed file."""
        self.papers = self.feed_parser.get_papers()

    def content_based_update(self) -> None:
        """Update the information of the paper based on the content retrieved from the content processors."""
        for paper in self.papers:
            if not paper.parsed:  # if the paper has already been parsed, there is no content update necessary
                content_processor = None
                domain = paper.domain
                content = paper.html_content
                if domain == utils.arxiv_domain:
                    content_processor = process.ArxivContentProcessor(content)
                elif domain == utils.ieee_domain:
                    content_processor = process.IEEEContentProcessor(content)
                elif domain == utils.elsevier_domain:
                    content_processor = process.ElsevierContentProcessor(content)
                elif domain in [utils.springer_domain, utils.nature_domain]:
                    content_processor = process.SpringerContentProcessor(content)

                if content_processor:
                    title, abstract, authors = content_processor.get_paper_meta_data()
                    paper.title = title
                    paper.abstract = abstract
                    paper.authors = authors

    def save_feed(self) -> None:
        """Store the papers of the feed in a file."""
        generator.create_atom_feed(self.papers, result_file_name=self.target)


class FeedList:
    """Class to store all feeds in a comprehended structure and to allow combined processing."""
    def __init__(self, sources: list[str], targets: list[str], onlines: list[bool], appendings: list[bool]) -> None:
        self.sources = sources
        self.targets = targets
        self.onlines = onlines
        self.appendings = appendings
        self.content_retriever = None
        self.feeds = self.init_feeds()

    def init_feeds(self) -> list[Feed]:
        """Initialize all feeds with the input parameters."""
        print("Initializing feeds.")
        feeds = []
        for source, target, online, appending in tqdm(zip(self.sources, self.targets, self.onlines, self.appendings),
                                                      total=len(self.sources)):
            feeds.append(Feed(source, target, online, appending))
        return feeds

    def build_feeds(self) -> None:
        """Build the feeds by retrieving all papers based on the source files."""
        for feed in self.feeds:
            feed.get_papers()

    def remove_duplicates(self) -> None:
        """Remove all duplicates papers across the different feeds in the feed list. The first occurrence is kept and
        all following items are removed."""
        id_sets = set()
        for feed in self.feeds:
            # read out existing ids
            id_list = list(map(lambda x: x.link, feed.papers))
            id_set = set(id_list)
            # get duplicates
            duplicates = id_sets.intersection(id_set)
            # update id list
            id_sets = id_sets.union(id_set)

            if duplicates:
                for duplicate in duplicates:
                    duplicate_idx = id_list.index(duplicate)
                    # delete from id_list
                    del id_list[duplicate_idx]
                    # delete paper from feed
                    del feed.papers[duplicate_idx]

    def refine_feeds(self) -> None:
        """Refine the paper information in all feeds based on the stored html contents."""
        self.get_paper_html_contents()
        for feed in self.feeds:
            feed.content_based_update()

    def get_paper_html_contents(self) -> None:
        """Retrieve the html content for the papers (if the publisher is supported) of all feeds in the feed list."""
        self.content_retriever = html.HTMLContentRetriever(self.feeds)
        self.content_retriever.get_content()

    def save_feeds(self) -> None:
        """Save the papers of each feed in the feed list."""
        print("Generate and save atom feeds.")
        for feed in tqdm(self.feeds, total=len(self.feeds)):
            feed.save_feed()
