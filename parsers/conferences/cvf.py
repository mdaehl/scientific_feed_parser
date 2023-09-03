from misc import utils
import bs4
import asyncio
from parsers.conferences import base
from itertools import chain
from misc.utils import Paper


class CVFParser(base.Parser):
    """Parser for the CVPR, WACV and ICCV which is held by the CVF."""
    def __init__(self, conference: str, year: int):
        super().__init__(conference, year)
        self.url = self.get_yearly_url()

    def get_yearly_url(self) -> str:
        """Get the conference url of the desired year."""
        if self.year < 2013:
            raise ValueError("The CVF conferences are only available from 2013.")
        elif self.year < 2020 and self.conference == "WACV":
            raise ValueError("The conference WACV is only available from 2020.")
        elif self.year % 2 == 0 and self.conference == "ICCV":
            raise ValueError("The ICCV is only held every second year.")
        else:
            return f"{self.base_url}/{self.conference}{self.year}"

    def get_url_container(self) -> bs4.element.ResultSet:
        """Get the html containers that contain the papers."""
        # if papers are directly available
        soup = utils.get_soup(self.url)
        container = soup.select("dt.ptitle")
        if len(container) == 0:
            # if all day site exists
            all_day_url = f"{self.url}?day=all"
            all_day_soup = utils.get_soup(all_day_url)
            container = all_day_soup.select("dt.ptitle")
            if len(container) == 0:
                # if individual dates only exist
                container_urls = [f"{self.base_url}/{item['href']}" for item in soup.select("dd >a")]
                container = list(
                    chain.from_iterable((map(lambda x: x.select("dt.ptitle"), map(utils.get_soup, container_urls)))))

        return container

    def parse_papers(self) -> None:
        """Parse all papers by retrieving the html content and process it to get the relevant information."""
        loop = asyncio.get_event_loop()
        self.links = [f"{self.base_url}/{link}" for link in self.links]
        html_contents = loop.run_until_complete(utils.get_paper_html_content(self.links))

        print("Processing paper data.")
        for content, html_link in zip(html_contents, self.links):
            try:
                soup = bs4.BeautifulSoup(content, "html.parser")

                # relevant infos
                title = soup.select("#papertitle")[0].get_text()
                title = title.strip()
                authors = soup.select("#authors >b >i")[0].get_text().split(",")
                abstract = soup.select("#abstract")[0].get_text()
                abstract = abstract.strip()
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
