import requests
import bs4


def get_data(link):
    arxiv_id = link.split("/")[-1]
    link = f"https://export.arxiv.org/api/query?id_list={arxiv_id}"
    content = requests.get(link).content
    soup = bs4.BeautifulSoup(content, features="xml")

    title = soup.select("entry >title")[0].text

    abstract = soup.find("summary").text
    abstract = abstract.replace("\n", " ").strip()

    authors = soup.select("author >name")
    authors = list(map(lambda x: x.text, authors))

    return title, authors, abstract
