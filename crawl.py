from urllib.parse import urlsplit, urljoin
from bs4 import BeautifulSoup, Tag
from typing import TypedDict
import requests
from asyncio import Lock, Semaphore
import aiohttp

class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]

class AsyncCrawler():
    def __init__(self, base_url: str, max_concurrency: int = 3):
        self.base_url = base_url
        self.base_domain = normalize_url(base_url)
        self.page_data = None
        self.lock = Lock()
        self.max_concurrency = max_concurrency
        self.semaphore = Semaphore(max_concurrency)
        self.session = aiohttp.ClientSession()
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session is not None:
            await self.session.close()

    async def add_page_visit(self, normalized_url: str) -> bool:

        async with self.lock:
            if normalized_url in self.page_data:
                return False # Page already visited 
            else:
                return True

    async def get_html(self, url: str) -> str | None:

        if self.session is None:
            return None

        try:
            async with self.session.get(
                url, headers={"User-Agent": "BootCrawler/1.0"}
            ) as response:
                if response.status > 399:
                    print(f"Error: HTTP {response.status} for {url}")
                    return None

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    print(f"Error: Non-HTML content {content_type} for {url}")
                    return None

                return await response.text()
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None 

    async def crawl_page(self, base_url: str, current_url: str = None, page_data: dict[str:PageData] = None) -> dict[str:PageData] | None:
        
        if current_url is None:
            current_url = base_url
        if page_data is None:
            page_data = {}

        print(current_url)

        if not self.add_page_visit(current_url):
            return page_data
            
        if urlsplit(current_url).netloc != urlsplit(base_url).netloc: # Make sure we are on the same domain
            return page_data
 
        async with self.semaphore:

            norm_current_url = normalize_url(current_url)
            
            html = get_html(current_url)
            print(f'Getting HTML for {current_url}...')

            if html is None:
                return page_data

            async with self.lock:
                page_data[f'{norm_current_url}'] = extract_page_data(html, current_url)

            for url in page_data[f'{norm_current_url}']['outgoing_links']:
                crawl_page(base_url = base_url, current_url = url, page_data = page_data)

            return page_data

    async def crawl(self):

        return await self.crawl_page(self.base_url)



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

async def crawl_site_async(base_url: str) -> PageData:

    crawler = AsyncCrawler(base_url, 10)

    
    async with crawler as c:
       return await c.crawl()

