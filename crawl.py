from types import TracebackType
from typing import TypedDict
from urllib.parse import urljoin, urlsplit
import asyncio

import aiohttp
from bs4 import BeautifulSoup, Tag

class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str]
    image_urls: list[str]

def normalize_url(url: str) -> str:
    parsed_url = urlsplit(url)
    full_path = f"{parsed_url.netloc}{parsed_url.path}"
    full_path = full_path.rstrip("/")
    return full_path.lower()


def get_heading_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    h_tag = soup.find("h1") or soup.find("h2")
    return h_tag.get_text(strip=True) if isinstance(h_tag, Tag) else ""


def get_first_paragraph_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    main_section = soup.find("main")
    if isinstance(main_section, Tag):
        first_p = main_section.find("p")
    else:
        first_p = soup.find("p")

    return first_p.get_text(strip=True) if isinstance(first_p, Tag) else ""


def get_urls_from_html(html: str, base_url: str) -> list[str]:
    urls = []
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a")

    for anchor in anchors:
        if not isinstance(anchor, Tag):
            continue
        href = anchor.get("href")
        if isinstance(href, str) and href:
            try:
                absolute_url = urljoin(base_url, href)
                urls.append(absolute_url)
            except Exception as e:
                print(f"{str(e)}: {href}")

    return urls


def get_images_from_html(html: str, base_url: str) -> list[str]:
    image_urls = []
    soup = BeautifulSoup(html, "html.parser")
    images = soup.find_all("img")

    for img in images:
        if not isinstance(img, Tag):
            continue
        src = img.get("src")
        if isinstance(src, str) and src:
            try:
                absolute_url = urljoin(base_url, src)
                image_urls.append(absolute_url)
            except Exception as e:
                print(f"{str(e)}: {src}")

    return image_urls


def extract_page_data(html: str, page_url: str) -> PageData:
    return {
        "url": page_url,
        "heading": get_heading_from_html(html),
        "first_paragraph": get_first_paragraph_from_html(html),
        "outgoing_links": get_urls_from_html(html, page_url),
        "image_urls": get_images_from_html(html, page_url),
    }

class AsyncCrawler:
    def __init__(self, base_url: str, max_concurrentcy: int = 3, max_pages: int = 10) -> None:
        self.base_url = base_url
        self.base_domain = urlsplit(base_url).netloc
        self.page_data: dict[str, PageData] = {}
        self.lock = asyncio.Lock()
        self.max_concurrency = 3
        self.semaphore = asyncio.Semaphore(self.max_concurrency)
        self.session: aiohttp.ClientSession | None = None
        self.max_pages: int = max_pages
        self.should_stop: bool = False
        self.all_tasks: set() = set()


    async def __aenter__(self) -> "AsyncCrawler":
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.session is not None:
            await self.session.close()

    async def add_page_visit(self, normalized_url: str) -> bool:
        
        if self.should_stop:
            return False

        async with self.lock:
            
            if normalized_url in self.page_data:
                return False
            
            if len(self.page_data) >= self.max_pages:
                self.should_stop = True
                print("Reached maximum number of pages to crawl")

                for task in self.all_tasks:
                    if not task.done():
                        task.cancel()

                return False
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

    async def crawl_page(self, current_url: str) -> None:
       
        main_task = asyncio.current_task()
        try:
            if self.should_stop:
                return
            current_url_obj = urlsplit(current_url)
            if current_url_obj.netloc != self.base_domain:
                return

            normalized_url = normalize_url(current_url)

            async with self.semaphore:
                is_new = await self.add_page_visit(normalized_url)
                if is_new is False:
                    return

                html = await self.get_html(current_url)
                if html is None:
                    return

                page_info = extract_page_data(html, current_url)
                async with self.lock:
                    self.page_data[normalized_url] = page_info

                next_urls = get_urls_from_html(html, self.base_url)

                for next_url in next_urls:
                    task = asyncio.create_task(self.crawl_page(next_url))
                    self.all_tasks.add(task)
        finally:
            self.all_tasks.discard(main_task)
            

    async def crawl(self) -> dict[str, PageData]:
        
        first_task = asyncio.create_task(self.crawl_page(self.base_url))

        self.all_tasks.add(first_task)

        while self.all_tasks:
            tasks = list(self.all_tasks)
            await asyncio.gather(*tasks, return_exceptions = True)

        return self.page_data


async def crawl_site_async(base_url: str, max_concurrency: int, max_pages) -> dict[str, PageData]:
    async with AsyncCrawler(base_url, max_concurrency, max_pages) as crawler:
        return await crawler.crawl()
