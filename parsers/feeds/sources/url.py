from __future__ import annotations
import abc
import numpy as np
import math
from fake_useragent import UserAgent
import re
from misc import config, utils
import yaml


class UrlHandler(abc.ABC):
    """Abstract base url handler which is used to generate the urls and headers to request additional paper
    information."""
    def __init__(self, papers: list[utils.Paper]) -> None:
        self.papers = papers

    @classmethod
    def create_handler(cls, papers: list[utils.Paper], **kwargs) -> UrlHandler:
        """Handler to validate the initialization if required."""
        return cls(papers)

    @abc.abstractmethod
    def get_request_urls(self) -> list[utils.Paper]:
        """Build urls to retrieve the publisher related paper information."""
        pass

    def get_request_headers(self) -> list[None]:
        """Build headers to retrieve the publisher related paper information."""
        return len(self.papers) * [None]


class ArxivUrlHandler(UrlHandler):
    """Class to build headers/urls to retrieve arxiv paper data. Allows to group the requests into unified
    urls to reduce I/O time."""
    def __init__(self, papers: list[utils.Paper], max_request_size: int = 100) -> None:
        super().__init__(papers)
        self.max_request_size = max_request_size
        self.base_url = "https://export.arxiv.org/api/query?id_list"

    def get_request_urls(self) -> list[str]:
        arxiv_ids = list(map(lambda x: x.link.split("/")[-1], self.papers))

        # split request urls based on max_request size
        n_splits = math.ceil(len(arxiv_ids) / self.max_request_size)
        arxiv_id_splits = list(np.array_split(arxiv_ids, n_splits))

        urls = []
        for split in arxiv_id_splits:
            urls.append(f"{self.base_url}={','.join(split)}&max_results={self.max_request_size}")
        return urls

    def get_request_headers(self) -> list[None]:
        return math.ceil(len(self.papers) / self.max_request_size) * [None]


class IEEEUrlHandler(UrlHandler):
    """Class to build headers/urls to retrieve IEEE paper data."""
    def __init__(self, papers) -> None:
        super().__init__(papers)
        self.base_url = "https://ieeexplore.ieee.org/abstract/document"

    def get_request_urls(self) -> list[str]:
        urls = []
        for paper in self.papers:
            paper_link = paper.link
            if "abstract" in paper_link:  # not free paper
                doc_id = paper_link.split('/')[-2]
            else:  # free paper
                match = re.search(r"/(?P<id>\d*)\.pdf", paper_link)
                doc_id = match.group("id")

            urls.append(f"{self.base_url}/{doc_id}")

        return urls

    def get_request_headers(self) -> list[dict]:
        user_agent = UserAgent()
        headers = {"User-Agent": user_agent.firefox}
        return len(self.papers) * [headers]


class ElsevierUrlHandler(UrlHandler):
    """Class to build headers/urls to retrieve elsevier/sciencedirect paper data."""
    def __init__(self, papers: list[utils.Paper], api_key: str) -> None:
        super().__init__(papers)
        self.base_url = "https://api.elsevier.com/content/article/pii"
        self.api_key = api_key

    @classmethod
    def create_handler(cls, papers: list[utils.Paper], **kwargs) -> ElsevierUrlHandler | None:
        api_key = yaml.safe_load(open(config.config_file))["elsevier_api_key"]
        if api_key:
            return cls(papers, api_key)
        else:
            return None

    def get_request_urls(self) -> list[str]:
        urls = []
        for paper in self.papers:
            paper_link = paper.link
            match = re.search("pii/(?P<pii>.*)", paper_link)
            pii = match.group("pii")
            urls.append(f"{self.base_url}/{pii}?apiKey={self.api_key}")

        return urls

    def get_request_headers(self) -> list[dict]:
        headers = {"Accept": "application/json"}
        return len(self.papers) * [headers]


class SpringerUrlHandler(UrlHandler):
    """Class to build headers/urls to retrieve springer/nature paper data. Allows to group the requests into unified
    urls to reduce I/O time."""
    def __init__(self, papers: list[utils.Paper], api_key: str, domain: str, max_request_size: int = 1):
        # TODO check how the paper order can be preserved with multi request, until then request size is set to 1
        super().__init__(papers)
        self.base_url = "https://api.springernature.com/meta/v2/json"
        self.api_key = api_key
        self.domain = domain
        self.max_request_size = max_request_size  # api max support is 100

    @classmethod
    def create_handler(cls, papers: list[utils.Paper], **kwargs) -> SpringerUrlHandler | None:
        domain = kwargs["domain"]
        api_key = yaml.safe_load(open(config.config_file))["springer_api_key"]
        if api_key:
            return cls(papers, api_key, domain)
        else:
            return None

    def get_request_urls(self) -> list[str]:
        # split request urls based on max_request size
        n_splits = math.ceil(len(self.papers) / self.max_request_size)

        dois = []
        for paper in self.papers:
            paper_link = paper.link
            sub_doi = paper_link.split("/")[-1]
            sub_doi = sub_doi.split(".")[0]  # free articles have a ".pdf" at the end
            if self.domain == "nature.com":
                doi_preface = "10.1038"
            else:
                doi_preface = paper_link.split("/")[-2]

            doi = f"{doi_preface}/{sub_doi}"
            dois.append(doi)

        dois = list(map(lambda x: f"doi:{x}", dois))
        doi_splits = list(np.array_split(dois, n_splits))

        urls = []
        for split in doi_splits:
            doi_str = " OR ".join(split)
            urls.append(f"{self.base_url}?q=({doi_str})&api_key={self.api_key}&p={self.max_request_size}")

        return urls

    def get_request_headers(self) -> list[None]:
        return math.ceil(len(self.papers) / self.max_request_size) * [None]
