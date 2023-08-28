from misc import utils
import bs4
import asyncio
from parsers.conferences import base


class ICMLParser(base.Parser):
    """Parser for the ICML."""
    def __init__(self, conference: str, year: int):
        super().__init__(conference, year)
        self.url = self.get_yearly_url()
        self.content = utils.get_content(self.url)

    def get_yearly_url(self) -> str:
        if self.year == 2023:
            conference_id = "v217"
        elif self.year == 2022:
            conference_id = "v162"
        elif self.year == 2021:
            conference_id = "v139"
        elif self.year == 2020:
            conference_id = "v119"
        elif self.year == 2019:
            conference_id = "v97"
        else:
            raise ValueError(f"ICML is supported from 2019. Check on {self.base_url} and add the id in the parsing "
                             f"'method get_yearly_url'.")

        return f"{self.base_url}/{conference_id}"

    def get_url_container(self) -> bs4.element.ResultSet:
        soup = bs4.BeautifulSoup(self.content, features="html.parser")
        return soup.select("p.links")

    def parse_papers(self) -> None:
        loop = asyncio.get_event_loop()
        html_contents = loop.run_until_complete(utils.get_paper_html_content(self.links))

        print("Processing paper data.")
        for content, html_link in zip(html_contents, self.links):
            try:
                soup = bs4.BeautifulSoup(content, "html.parser")

                # relevant infos
                title = soup.find("h1").getText()
                authors = list(map(lambda x: x["content"], soup.find_all("meta", attrs={"name": "citation_author"})))
                abstract = soup.select("#abstract")[0].get_text()
                abstract = abstract.strip()
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
