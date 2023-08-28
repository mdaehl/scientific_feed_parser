import bs4
from misc import config
import collections
import aiohttp
import requests
from tqdm.asyncio import tqdm_asyncio


# paper base class
Paper = collections.namedtuple("Paper", ["title", "authors", "abstract", "link"])

base_urls = {
    "CVPR": "https://openaccess.thecvf.com",
    "WACV": "https://openaccess.thecvf.com",
    "ICCV": "https://openaccess.thecvf.com",
    "ECCV": "https://www.ecva.net",
    "ICML": "https://proceedings.mlr.press",
    "NIPS": "https://papers.nips.cc"
}


def get_link(item: bs4.element.Tag) -> str:
    return item.find("a")["href"]


async def fetch_url(session: aiohttp.client.ClientSession, url: str) -> str:
    """Fetch URL using an aiohttp Session to allow asynchronous execution."""
    async with session.get(url, proxy=config.http_proxy) as response:
        return await response.text()


def get_content(url: str) -> str:
    return requests.get(url, proxies=config.proxies).content.decode("utf-8")


async def get_paper_html_content(links: list) -> list:
    print("Retrieving paper data.")

    import asyncio
    semaphore = asyncio.Semaphore(20)
    import socket
    connector = aiohttp.TCPConnector(limit=10, verify_ssl=False, family=socket.AF_INET,)

    async with semaphore:
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = [fetch_url(session, url) for url in links]
            await asyncio.sleep(0.01)
            html_contents = await tqdm_asyncio.gather(*tasks)
            return html_contents


def get_soup(url: str) -> bs4.BeautifulSoup:
    content = requests.get(url).content.decode("utf-8")
    soup = bs4.BeautifulSoup(content, parser="html.parser", features="lxml")
    return soup
