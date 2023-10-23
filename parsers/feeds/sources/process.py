import bs4
import abc
import json
from typing import Any


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
        title = self.content.find("meta", property="og:title")["content"]
        abstract = self.content.find("meta", property="og:description")["content"]
        authors = self.content.find("meta", attrs={"name": "parsely-author"})["content"]
        authors = authors.split(";")
        return title, abstract, authors


class ElsevierContentProcessor(ContentProcessor):
    """Process the content related to elsevier/sciencedirect papers."""
    def __init__(self, content: str) -> None:
        content = json.loads(content)
        super().__init__(content)

    def get_paper_meta_data(self) -> tuple[str, str, list[str]]:
        data = self.content["full-text-retrieval-response"]["coredata"]

        title = data["dc:title"]
        authors_item = data["dc:creator"]
        authors = list(map(lambda x: x["$"], authors_item))
        abstract = data["dc:description"]
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
