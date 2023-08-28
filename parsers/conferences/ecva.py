import bs4
import asyncio
from misc import utils
from parsers.conferences import base


class ECVAParser(base.Parser):
    """Parser for the ECCV which is held by the ECVA."""
    def __init__(self, conference, year):
        super().__init__(conference, year)
        self.url = self.get_yearly_url()
        self.content = utils.get_content(self.url)

    def get_yearly_url(self) -> str:
        if self.year < 2018:
            raise ValueError("The conference ECCV is only available from 2018.")
        return f"{self.base_url}/papers.php"

    def get_url_container(self) -> bs4.element.ResultSet:
        soup = bs4.BeautifulSoup(self.content, features="html.parser")
        return soup.select("dt.ptitle")

    def parse_papers(self) -> None:
        loop = asyncio.get_event_loop()
        self.links = [f"{self.base_url}/{link}" for link in self.links]
        html_contents = loop.run_until_complete(utils.get_paper_html_content(self.links))

        print("Processing paper data.")
        for content, html_link in zip(html_contents, self.links):
            if f"ECCV_{self.year}" in html_link:
                try:
                    soup = bs4.BeautifulSoup(content, "html.parser")
                    # relevant infos
                    title = soup.select("#papertitle")[0].get_text()
                    title = title.strip()
                    authors = soup.select("#authors >b >i")[0].get_text().split(",")
                    abstract = soup.select("#abstract")[0].get_text()
                    abstract = abstract.strip()
                    sub_link = next(filter(lambda x: "pdf" in x.get_text(), soup.select("a"))).get("href")
                    sub_link = sub_link.replace("../", "")
                    link = f"{self.base_url}/{sub_link}"

                    # build and append paper
                    paper = utils.Paper(title, authors, abstract, link)
                    self.papers.append(paper)
                except IndexError:
                    print(f"The paper with the link {self.base_url}/{html_link} could not be found.")

    def get_papers(self):  # -> list[utils.Paper]
        container = self.get_url_container()
        self.links = super().get_paper_links(container)
        self.parse_papers()
        return self.papers
