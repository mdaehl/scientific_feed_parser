from parsers.conferences import base
import bs4
from misc import utils
import asyncio
import requests
from tqdm import tqdm


class NIPSParser(base.Parser):
    def __init__(self, conference, year):
        super().__init__(conference, year)
        self.url = self.get_yearly_url()
        self.content = utils.get_content(self.url)

    def get_yearly_url(self) -> str:
        if self.year < 1987:
            raise ValueError("The conferences NIPS is only available until 1987.")
        return f"{self.base_url}/paper_files/paper/{self.year}"

    def get_url_container(self) -> bs4.element.ResultSet:
        soup = bs4.BeautifulSoup(self.content, features="html.parser")
        sub_result = soup.find("ul", {"class": "paper-list"})
        return sub_result.select("li", {"class": "none"})

    def parse_papers(self) -> None:
        loop = asyncio.get_event_loop()
        self.links = [f"{self.base_url}/{link}" for link in self.links]

        html_contents = []
        for link in tqdm(self.links):
            content = requests.get(link).content.decode("utf-8")
            soup = bs4.BeautifulSoup(content, parser="html.parser", features="lxml")
            html_contents.append(soup)

        # html_contents = loop.run_until_complete(utils.get_paper_html_content(self.links))

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

    def get_papers(self):
        container = self.get_url_container()
        self.links = super().get_paper_links(container)
        self.parse_papers()
        return self.papers