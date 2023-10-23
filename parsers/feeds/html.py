from __future__ import annotations
from misc import utils
import asyncio
import itertools
from parsers.feeds.sources import url
from collections import defaultdict
import bs4
import json
from typing import TYPE_CHECKING


# to avoid circular import due to type hint
if TYPE_CHECKING:
    from parsers.feeds.feed import Feed


class HTMLContentRetriever:
    """Processor for html data of papers."""
    def __init__(self, feeds: list[Feed]) -> None:
        self.feeds = feeds
        self.request_domain_urls = {}
        self.request_domain_headers = {}
        self.source_grouped_papers = defaultdict(list)

        # order that maps global index to the list of papers that is created for each domain in source_grouped_papers
        self.input_order_indices = defaultdict(list)

        self.content_indices = []
        self.contents = []

    def get_content(self) -> None:
        """Get the html content for all papers and assign it to each one."""
        self.get_source_grouped_papers()
        self.build_request_urls()
        self.request_contents()
        self.split_contents()
        self.assign_contents()

    def get_source_grouped_papers(self) -> None:
        """Group papers of all feeds according to their publishers to allow combined (optimized) requests later."""
        papers = list(itertools.chain.from_iterable(list(map(lambda x: x.papers, self.feeds))))
        for idx, paper in enumerate(papers):
            if not paper.parsed:  # only check papers that have not been parsed before (in the preexisting feed file)
                self.source_grouped_papers[paper.domain].append(paper)
                self.input_order_indices[paper.domain].append(idx)

    def build_request_urls(self) -> None:
        """Build the request urls (and headers) based on the publisher."""
        for domain, papers in self.source_grouped_papers.items():
            url_handler = None
            if domain == utils.arxiv_domain:
                url_handler = url.ArxivUrlHandler.create_handler(papers)
            elif domain == utils.ieee_domain:
                url_handler = url.IEEEUrlHandler.create_handler(papers)
            elif domain == utils.elsevier_domain:
                url_handler = url.ElsevierUrlHandler.create_handler(papers)
            elif domain in [utils.springer_domain, utils.nature_domain]:
                url_handler = url.SpringerUrlHandler.create_handler(papers, domain=domain)

            if url_handler:
                indices = self.input_order_indices[domain]
                self.content_indices += indices
                self.request_domain_urls[domain] = url_handler.get_request_urls()
                self.request_domain_headers[domain] = url_handler.get_request_headers()

    def request_contents(self) -> None:
        """Request all html contents with aiohttp based on the request urls and headers."""
        loop = asyncio.get_event_loop()
        request_urls = list(itertools.chain.from_iterable(self.request_domain_urls.values()))
        request_headers = list(itertools.chain.from_iterable(self.request_domain_headers.values()))
        self.contents = loop.run_until_complete(utils.get_paper_html_content(request_urls, request_headers))

    def split_contents(self) -> None:
        """Split the contents of the combined requests to ensure that each content contains only information of a
        single papers."""
        split_contents = []
        domains = itertools.chain.from_iterable([[domain] * len(self.request_domain_urls[domain])
                                                 for domain in self.request_domain_urls.keys()])
        for content, domain in zip(self.contents, domains):
            if domain == utils.arxiv_domain:
                content = bs4.BeautifulSoup(content, features="xml")
                split_content = content.find_all("entry")
                split_contents += map(str, split_content)
            elif domain in [utils.springer_domain, utils.nature_domain]:
                split_contents += map(lambda x: json.dumps(x), json.loads(content)["records"])
            else:
                split_contents.append(content)

        self.contents = split_contents

    def assign_contents(self) -> None:
        """Assign the split contents to the original papers."""
        # get paper references from feeds
        papers = list(itertools.chain.from_iterable(map(lambda x: x.papers, self.feeds)))

        for idx, content in zip(self.content_indices, self.contents):
            paper = papers[idx]
            paper.html_content = content
