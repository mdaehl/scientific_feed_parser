from __future__ import annotations
import warnings
import bs4
import abc
import json
from typing import Any
import yaml
from misc import config


class ContentProcessor(abc.ABC):
    """Abstract content processor, which is used to process the html content."""
    def __init__(self, content: Any) -> None:  # content is either a json like object or a bs4 element
        self.content = content

    @abc.abstractmethod
    def get_paper_meta_data(self) -> tuple[str, str, list[str]]:
        """Retrieve the metadata (title, abstract, authors) from the content."""
        pass


class ArxivContentProcessor(ContentProcessor):
    """Process the content related to arxiv papers."""
    def __init__(self, content: str) -> None:
        content = bs4.BeautifulSoup(content, features="xml")
        super().__init__(content)

    def get_paper_meta_data(self) -> tuple[str, str, list[str]]:
        title = self.content.select("entry >title")[0].text
        abstract = self.content.find("summary").text
        abstract = abstract.replace("\n", " ").strip()
        authors = self.content.select("author >name")
        authors = list(map(lambda x: x.text, authors))
        return title, abstract, authors


class IEEEContentProcessor(ContentProcessor):
    """Process the content related to IEEE papers."""
    def __init__(self, content: str) -> None:
        content = bs4.BeautifulSoup(content, features="lxml")
        super().__init__(content)

    def get_paper_meta_data(self) -> tuple[str, str, list[str]]:
        if self.content.title.text == "Request Rejected":
            raise ValueError("The request to the IEEE API was rejected. This usually occurs after a large amount of "
                             "requests. However, connecting and disconnection from a WIFI/Lan connection seems to fix "
                             "this problem. If this problem persists or occurs frequently, please consider using "
                             "reducing the number of simultaneously opened connections in utils.py.")
        title = self.content.find("meta", property="og:title")["content"]
        abstract = self.content.find("meta", property="og:description")["content"]
        authors = self.content.find("meta", attrs={"name": "parsely-author"})["content"]
        authors = authors.split(";")
        return title, abstract, authors


class ElsevierContentProcessor(ContentProcessor):
    """Process the content related to elsevier/sciencedirect papers."""
    def __init__(self, content: str) -> None:
        self.api_key = yaml.safe_load(open(config.config_file)).get("elsevier_api_key")
        if self.api_key:
            content = json.loads(content)
        else:
            content = bs4.BeautifulSoup(content, features="lxml")
        super().__init__(content)

    def get_paper_meta_data(self) -> tuple[str, str, list[str]]:
        if self.api_key:
            if self.content.get("error-response") is not None:
                raise ValueError(
                    "The request to the Elsevier API was rejected. This usually occurs after a large amount "
                    "of requests. If this problem persists or occurs frequently, please consider using reducing the "
                    "number of simultaneously opened connections in utils.py.")

            data = self.content["full-text-retrieval-response"]["coredata"]
            title = data["dc:title"]
            authors_item = data["dc:creator"]
            authors = list(map(lambda x: x["$"], authors_item))
            abstract = data["dc:description"]
        else:
            try:
                abstract = self.content.find("h2", string="Abstract").find_next_sibling().text
                title = self.content.find("meta", property="og:title")["content"]
                names = self.content.find_all("span", {"class": "given-name"})
                surnames = self.content.find_all("span", {"class": "text surname"})
                authors = [f"{name.text} {surname.text}" for name, surname in zip(names, surnames)]
            except AttributeError:
                url = self.content.link["href"]
                warnings.warn(f"The elsevier paper could not be parsed correctly. This occurs if papers are withdrawn "
                              f"or have a special format. Consider manually checking the webpage {url}.")
                title = ""
                abstract = ""
                authors = []

        return title, abstract, authors


class SpringerContentProcessor(ContentProcessor):
    """Process the content related to springer/nature papers."""
    def __init__(self, content: str) -> None:
        content = json.loads(content)
        super().__init__(content)

    def get_paper_meta_data(self) -> tuple[str, str, list[str]]:
        title = self.content["title"]
        abstract = self.content["abstract"]
        authors = self.content["creators"]
        authors = list(map(lambda x: x["creator"], authors))
        return title, abstract, authors
