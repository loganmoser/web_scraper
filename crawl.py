from urllib.parse import urlsplit, urljoin
from bs4 import BeautifulSoup, Tag
from typing import TypedDict
import requests

class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]


def get_html(url):
    
    r = requests.get(url, headers={"User-Agent": "BootCrawler/1.0"})

    r.raise_for_status() # Throw error if response is 400+

    return r.text

def normalize_url(url: str) -> str:

    url_split = urlsplit(url)

    path = f"{url_split.netloc}{url_split.path}".rstrip("/").lower()  

    return path

def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, 'html.parser')

    h_tag = soup.find("h1") or soup.find("h2")

    return h_tag.get_text(strip=True) if isinstance(h_tag, Tag) else ""
   
def get_first_paragraph_from_html(html: str) -> str:

    soup = BeautifulSoup(html, 'html.parser')

    main_section = soup.find("main")

    if isinstance(main_section, Tag):
        first_p = main_section.find("p")
    else:
        first_p = soup.find("p")

    return first_p.get_text(strip=True) if isinstance(first_p, Tag) else "" 

def get_urls_from_html(html: str, base_url: str) -> list[str]:

    soup = BeautifulSoup(html, 'html.parser')

    anchors = [anchor for anchor in soup.find_all('a', href=True)]
    links = [urljoin(base_url, anchor['href']) for anchor in anchors]
    
    return links

def get_images_from_html(html: str, base_url: str) -> list[str]:

    soup = BeautifulSoup(html, 'html.parser')

    images = soup.find_all('img')

    sources = [urljoin(base_url, image['src']) for image in images]

    return sources

def extract_page_data(html: str, page_url: str) -> PageData:

    soup = BeautifulSoup(html, 'html.parser')

    return {
        "url": page_url,
        "heading": get_heading_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, page_url),
        "image_urls": get_images_from_html(html, page_url)
        }

def crawl_page(base_url: str, current_url: str = None, page_data: dict[str:PageData] = None) -> dict[str:PageData] | None:

    if current_url is None:
        current_url = base_url
    if page_data is None:
        page_data = {}

    if urlsplit(current_url).netloc != urlsplit(base_url).netloc: # Make sure we are on the same domain
        return page_data

    norm_current_url = normalize_url(current_url)

    if norm_current_url in page_data:
        return page_data

    html = get_html(current_url)
    print(f'Getting HTML for {current_url}...')

    if html is None:
        return page_data

    page_data[f'{norm_current_url}'] = extract_page_data(html, current_url)

    for url in page_data[f'{norm_current_url}']['outgoing_links']:
        crawl_page(base_url = base_url, current_url = url, page_data = page_data)

    return page_data

