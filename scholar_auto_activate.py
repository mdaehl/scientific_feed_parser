import argparse
from misc import config
from tqdm import tqdm
import re
import requests
from fake_useragent import UserAgent


def load_file(file_path: str) -> str:
    """Load feed file and get it's content."""
    try:
        content = requests.get(file_path, proxies=config.proxies, verify=config.verify_ssl).content.decode("utf-8")
    except requests.exceptions.InvalidSchema:
        raise ValueError(f"{file_path} is no valid URL.")
    return content


def get_link(content: str) -> str:
    """Extract confirmation link from feed content."""
    match = re.search(
        r"(?P<link>http://scholar.google.com/scholar_alerts\?update_op=confirm_alert.*?alert_id.*?)&#x22;",
        content
    )
    link = match.group("link")
    link = link.replace("amp;", "&").replace(";", "").replace("#", "")
    return link


def activate(args: argparse.Namespace) -> None:
    """Activate the Google Scholar feeds automatically by extracting the confirmation link and opening it via requests
    and a header to emulate a user. Basic request calls are blocked by Google. Google Scholar does NOT send out a mail
    if the confirmation was completed successful. Instead, you should get recommendations in your feed as soon as Google
    Scholar sends out a mail notification (usually every few days based on your keywords)."""
    print("Activating google scholar feeds.")
    files = args.files

    user_agent = UserAgent()
    headers = {'User-Agent': user_agent.chrome}
    for file in tqdm(files):
        content = load_file(file)
        link = get_link(content)
        response = requests.get(link, proxies=config.proxies, headers=headers, verify=config.verify_ssl)
        if response.status_code != 200:
            raise Warning(f"Google seems to block the automatic activation. You can either try to wait or open the link {link} manually.")


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--files", "-f", nargs='+', help="Path/s to the xml file/s.")
    input_args = arg_parser.parse_args()
    activate(input_args)
