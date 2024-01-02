import bs4
from misc import config
import aiohttp
import requests
from tqdm.asyncio import tqdm_asyncio
from datetime import datetime
from dataclasses import dataclass
import ssl
import certifi


@dataclass
class Paper:
    title: str
    authors: list[str]
    abstract: str
    link: str
    domain: str = None
    html_content: str = None
    parsed: bool = False


base_urls = {
    "CVPR": "https://openaccess.thecvf.com",
    "WACV": "https://openaccess.thecvf.com",
    "ICCV": "https://openaccess.thecvf.com",
    "ECCV": "https://www.ecva.net",
    "ICML": "https://proceedings.mlr.press",
    "NIPS": "https://papers.nips.cc"
}

arxiv_domain = "arxiv.org"
ieee_domain = "ieee.org"
elsevier_domain = "sciencedirect.com"
springer_domain = "springer.com"
nature_domain = "nature.com"

request_limit = 25  # number of simultaneously opened connections


def check_year(year: int) -> None:
    """Guarantee that years that are in the future are not allowed."""
    if year > datetime.now().year:
        raise ValueError("The selected year lies in the future and is therefore invalid.")


def get_link(item: bs4.element.Tag) -> str:
    """Get the link of a bs4 element tag."""
    return item.find("a")["href"]


async def fetch_url(session: aiohttp.client.ClientSession, url: str, header: str | None) -> str:
    """Fetch URL using an aiohttp Session to allow asynchronous execution."""
    async with session.get(url, headers=header, proxy=config.http_proxy) as response:
        return await response.text()


async def get_paper_html_content(links: list[str], headers: list[dict] = None) -> list[str]:
    """Get the html content of all links."""
    print("Retrieving paper data.")

    if not headers:
        headers = len(links) * [None]

    # usually this works, but in case the requests fail, check https://stackoverflow.com/questions/51248714/aiohttp-client-exception-serverdisconnectederror-is-this-the-api-servers-issu
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(limit=request_limit, ssl=ssl_context)
    async with aiohttp.ClientSession(trust_env=True, connector=connector) as session:
        tasks = [fetch_url(session, url, header) for url, header in zip(links, headers)]
        html_contents = await tqdm_asyncio.gather(*tasks)
        return html_contents


def get_soup(url: str) -> bs4.BeautifulSoup:
    """Compact class to retrieve url and pass it into bs4."""
    content = requests.get(url, proxies=config.proxies).content.decode("utf-8")
    soup = bs4.BeautifulSoup(content, parser="html.parser", features="lxml")
    return soup


def decode_xml_soup(soup: bs4.BeautifulSoup) -> tuple[list[str], list[list[str]], list[str], list[str]]:
    titles = list(map(lambda x: x.text, soup.select("entry >title")))
    all_authors = list(map(lambda x: list(map(lambda y: y.text, x.select("author"))), soup.select("entry")))
    abstracts = list(map(lambda x: x.text, soup.select("entry >summary")))
    links = list(map(lambda x: x.text, soup.select("entry >id")))
    return titles, all_authors, abstracts, links
