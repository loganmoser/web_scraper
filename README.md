A small asynchronous web crawler. Point it at a URL, tell it how many pages to visit and how many requests to run at once, and it walks the site's internal links, pulls basic info off each page (heading, first paragraph, links, images), and writes it all to `report.json`.

This was built as part of the boot.dev course, so it's intentionally simple — a good project to read end-to-end if you're learning how async crawling works.

## How it works (the concepts)

A crawler's job is basically: **visit a page → record what's on it → find the links on that page → repeat for each new link**, while making sure you don't visit the same page twice or wander off to a different website.

This project splits that job across three files:

- **`crawl.py`** — the crawler itself: fetching pages, parsing HTML, and managing concurrency.
- **`json_report.py`** — takes the crawler's results and writes them to a JSON file.
- **`main.py`** — the entry point that wires the two together and prints progress.

### Why "async"?

Fetching a web page mostly means *waiting* — waiting for a server to respond. If you crawled one page at a time, your program would sit idle during every single wait. `asyncio` lets Python start a request, and while it's waiting on the network, go work on other requests instead. That's why `crawl_page` is `async def` and every network call inside it is `await`ed — `await` is the "pause here, let something else run, resume when the result is ready" instruction.

Concretely, each time the crawler finds a new link, it doesn't fetch it immediately in a loop — it spins up a new task for it:

```python
task = asyncio.create_task(self.crawl_page(next_url))
```

So instead of one page at a time, you end up with a growing, self-multiplying set of "go crawl this page" tasks all running concurrently.

### Keeping concurrency under control

Letting every page spawn unlimited concurrent requests would hammer the target server and open too many connections at once. That's what `asyncio.Semaphore` is for — think of it as a bouncer holding a fixed number of tickets:

```python
self.semaphore = asyncio.Semaphore(self.max_concurrency)

async with self.semaphore:
    ...  # only max_concurrency tasks can be inside this block at once
```

Any task that reaches `async with self.semaphore:` while all tickets are taken just waits its turn — no extra code needed to track "who's busy."

### Not visiting the same page twice

Multiple pages on a site often link to each other, so without some bookkeeping the crawler would loop forever. `AsyncCrawler` keeps a dictionary, `self.page_data`, keyed by a **normalized URL** (lowercased, no trailing slash, no `http://` vs `https://` distinction), and checks it before crawling a page:

```python
async def add_page_visit(self, normalized_url: str) -> bool:
    async with self.lock:
        if normalized_url in self.page_data:
            return False   # already seen it, skip
        ...
```

Because many tasks can run at once, it's possible for two tasks to check "have we seen this URL?" at the exact same moment before either has recorded it — a race condition. The `asyncio.Lock()` prevents that: only one task at a time can be inside the `async with self.lock:` block, so the check-and-record happens atomically.

### Stopping at the page limit

Once `self.page_data` hits `max_pages`, the crawler sets `self.should_stop = True` and cancels every task still in flight:

```python
for task in self.all_tasks:
    if not task.done():
        task.cancel()
```

Every task also checks `self.should_stop` early on, so anything that starts after the limit is hit exits immediately instead of doing unnecessary work.

### Staying on one site

Before crawling a URL, the crawler compares its domain against the domain it started on:

```python
if current_url_obj.netloc != self.base_domain:
    return
```

This stops the crawl from following an external link off to some other website entirely.

### What gets extracted from each page

For every page it keeps, `crawl.py` uses BeautifulSoup to pull out:

| Field | How it's found |
|---|---|
| `heading` | first `<h1>`, falling back to `<h2>` |
| `first_paragraph` | first `<p>` inside `<main>`, falling back to the first `<p>` anywhere |
| `outgoing_links` | every `href` on the page, turned into an absolute URL |
| `image_urls` | every `src` on the page, turned into an absolute URL |

### Writing the report

`json_report.py` takes the finished `dict[str, PageData]`, sorts the pages alphabetically by URL, and dumps them to `report.json`:

```python
pages = sorted(page_data.values(), key=lambda p: p["url"])
json.dump(pages, f, indent=2)
```

## Requirements

- Python 3.13+
- Dependencies (installed automatically if you use `uv`, otherwise via `pip`):
  - `aiohttp` — async HTTP client
  - `beautifulsoup4` — HTML parsing
  - `requests`

## Installation

With [uv](https://github.com/astral-sh/uv) (there's a `uv.lock` in the repo, so this is the easiest path):

```bash
git clone https://github.com/loganmoser/web_scraper.git
cd web_scraper
uv sync
```

Or with plain `pip`:

```bash
git clone https://github.com/loganmoser/web_scraper.git
cd web_scraper
pip install aiohttp beautifulsoup4 requests
```

## Usage

```bash
python main.py <base_url> <max_concurrency> <max_pages>
```

- `base_url` — the site to start crawling, e.g. `https://example.com`
- `max_concurrency` — how many pages to fetch at the same time, e.g. `3`
- `max_pages` — stop once this many unique pages have been crawled, e.g. `10`

Example:

```bash
uv run main.py https://example.com 3 10
```

While it runs, you'll see progress printed to the console (which page it's crawling, any HTTP errors, when it hits the page limit). When it finishes, it prints the full contents of `report.json`, which will look like:

```json
[
  {
    "url": "https://example.com",
    "heading": "Example Domain",
    "first_paragraph": "This domain is for use in illustrative examples...",
    "outgoing_links": ["https://www.iana.org/domains/example"],
    "image_urls": []
  }
]
```

## Notes / limitations

- It only follows links on the same domain it started on.
- It doesn't respect `robots.txt` — be considerate about which sites and how hard you crawl them.
- There's a fixed `User-Agent` header (`BootCrawler/1.0`) sent with every request.
- Non-HTML responses (images, PDFs, etc.) and HTTP errors (status 400+) are skipped and logged, not treated as fatal.A small asynchronous web crawler. Point it at a URL, tell it how many pages to visit and how many requests to run at once, and it walks the site's internal links, pulls basic info off each page (heading, first paragraph, links, images), and writes it all to report.json.

This was built as part of the boot.dev course, so it's intentionally simple — a good project to read end-to-end if you're learning how async crawling works.

How it works (the concepts)

A crawler's job is basically: visit a page → record what's on it → find the links on that page → repeat for each new link, while making sure you don't visit the same page twice or wander off to a different website.

This project splits that job across three files:

crawl.py — the crawler itself: fetching pages, parsing HTML, and managing concurrency.
json_report.py — takes the crawler's results and writes them to a JSON file.
main.py — the entry point that wires the two together and prints progress.
Why "async"?

Fetching a web page mostly means waiting — waiting for a server to respond. If you crawled one page at a time, your program would sit idle during every single wait. asyncio lets Python start a request, and while it's waiting on the network, go work on other requests instead. That's why crawl_page is async def and every network call inside it is awaited — await is the "pause here, let something else run, resume when the result is ready" instruction.

Concretely, each time the crawler finds a new link, it doesn't fetch it immediately in a loop — it spins up a new task for it:

python
task = asyncio.create_task(self.crawl_page(next_url))

So instead of one page at a time, you end up with a growing, self-multiplying set of "go crawl this page" tasks all running concurrently.

Keeping concurrency under control

Letting every page spawn unlimited concurrent requests would hammer the target server and open too many connections at once. That's what asyncio.Semaphore is for — think of it as a bouncer holding a fixed number of tickets:

python
self.semaphore = asyncio.Semaphore(self.max_concurrency)

async with self.semaphore:
    ...  # only max_concurrency tasks can be inside this block at once

Any task that reaches async with self.semaphore: while all tickets are taken just waits its turn — no extra code needed to track "who's busy."

Not visiting the same page twice

Multiple pages on a site often link to each other, so without some bookkeeping the crawler would loop forever. AsyncCrawler keeps a dictionary, self.page_data, keyed by a normalized URL (lowercased, no trailing slash, no http:// vs https:// distinction), and checks it before crawling a page:

python
async def add_page_visit(self, normalized_url: str) -> bool:
    async with self.lock:
        if normalized_url in self.page_data:
            return False   # already seen it, skip
        ...

Because many tasks can run at once, it's possible for two tasks to check "have we seen this URL?" at the exact same moment before either has recorded it — a race condition. The asyncio.Lock() prevents that: only one task at a time can be inside the async with self.lock: block, so the check-and-record happens atomically.

Stopping at the page limit

Once self.page_data hits max_pages, the crawler sets self.should_stop = True and cancels every task still in flight:

python
for task in self.all_tasks:
    if not task.done():
        task.cancel()

Every task also checks self.should_stop early on, so anything that starts after the limit is hit exits immediately instead of doing unnecessary work.

Staying on one site

Before crawling a URL, the crawler compares its domain against the domain it started on:

python
if current_url_obj.netloc != self.base_domain:
    return

This stops the crawl from following an external link off to some other website entirely.

What gets extracted from each page

For every page it keeps, crawl.py uses BeautifulSoup to pull out:

Field	How it's found
heading	first <h1>, falling back to <h2>
first_paragraph	first <p> inside <main>, falling back to the first <p> anywhere
outgoing_links	every href on the page, turned into an absolute URL
image_urls	every src on the page, turned into an absolute URL
Writing the report

json_report.py takes the finished dict[str, PageData], sorts the pages alphabetically by URL, and dumps them to report.json:

python
pages = sorted(page_data.values(), key=lambda p: p["url"])
json.dump(pages, f, indent=2)
Requirements
Python 3.13+
Dependencies (installed automatically if you use uv, otherwise via pip):
aiohttp — async HTTP client
beautifulsoup4 — HTML parsing
requests
Installation

With uv (there's a uv.lock in the repo, so this is the easiest path):

bash
git clone https://github.com/loganmoser/web_scraper.git
cd web_scraper
uv sync

Or with plain pip:

bash
git clone https://github.com/loganmoser/web_scraper.git
cd web_scraper
pip install aiohttp beautifulsoup4 requests
Usage
bash
python main.py <base_url> <max_concurrency> <max_pages>
base_url — the site to start crawling, e.g. https://example.com
max_concurrency — how many pages to fetch at the same time, e.g. 3
max_pages — stop once this many unique pages have been crawled, e.g. 10

Example:

bash
uv run main.py https://example.com 3 10

While it runs, you'll see progress printed to the console (which page it's crawling, any HTTP errors, when it hits the page limit). When it finishes, it prints the full contents of report.json, which will look like:

json
[
  {
    "url": "https://example.com",
    "heading": "Example Domain",
    "first_paragraph": "This domain is for use in illustrative examples...",
    "outgoing_links": ["https://www.iana.org/domains/example"],
    "image_urls": []
  }
]
Notes / limitations
It only follows links on the same domain it started on.
It doesn't respect robots.txt — be considerate about which sites and how hard you crawl them.
There's a fixed User-Agent header (BootCrawler/1.0) sent with every request.
Non-HTML responses (images, PDFs, etc.) and HTTP errors (status 400+) are skipped and logged, not treated as fatal.
