from parsers.conferences import base
import bs4
from misc import utils
import asyncio
from tqdm import tqdm
from misc.utils import Paper
from misc import config
import requests


class NIPSParser(base.Parser):
    """Parser for NIPS."""
    def __init__(self, conference: str, year: int):
        super().__init__(conference, year)
        self.url = self.get_yearly_url()
        self.content = requests.get(self.url, proxies=config.proxies).content.decode("utf-8")

    def get_yearly_url(self) -> str:
        """Get the conference url of the desired year."""
        if self.year < 1987:
            raise ValueError("The conferences NIPS is only available until 1987.")
        return f"{self.base_url}/paper_files/paper/{self.year}"

    def get_url_container(self) -> bs4.element.ResultSet | list:
        """Get the html containers that contain the papers."""
        soup = bs4.BeautifulSoup(self.content, features="html.parser")
        sub_result = soup.find("ul", {"class": "paper-list"})
        if sub_result:
            return sub_result.select("li", {"class": "none"})
        else:
            return []

    def parse_papers(self) -> None:
        """Parse all papers by retrieving the html content and process it to get the relevant information."""
        self.links = [f"{self.base_url}/{link}" for link in self.links]

        # The parallel loop fails most of the time, as NIPS is strict regarding potential ddos attacks.
        # loop = asyncio.get_event_loop()
        # html_contents = loop.run_until_complete(utils.get_paper_html_content(self.links))

        html_contents = []
        for link in tqdm(self.links):
            content = requests.get(link, proxies=config.proxies).content.decode("utf-8")
            soup = bs4.BeautifulSoup(content, parser="html.parser", features="lxml")
            html_contents.append(soup)

        print("Processing paper data.")
        for content, html_link in zip(html_contents, self.links):
            try:
                soup = bs4.BeautifulSoup(content, "html.parser")

                title = soup.find("title").text
                authors = soup.select("p >i")[0].text.split(",")
                abstract = soup.select("p >p")[0].text
                link = soup.find("meta", attrs={"name": "citation_pdf_url"})["content"]

                # build and append paper
                paper = utils.Paper(title, authors, abstract, link)
                self.papers.append(paper)
            except IndexError:
                print(f"The paper with the link {self.base_url}/{html_link} could not be found.")

    def get_papers(self) -> list[Paper]:
        """Get all papers from the conference."""
        container = self.get_url_container()
        self.links = super().get_paper_links(container)
        self.parse_papers()
        return self.papers
