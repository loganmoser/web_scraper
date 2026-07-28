import sys
from crawl import crawl_site_async
import asyncio
from json_report import write_json_report

async def main():
    
    if len(sys.argv) < 2:
        print("no website provided")
        sys.exit(1)
    if len(sys.argv) > 4:
        print("too many arguments provided")
        sys.exit(1)

    base_url = sys.argv[1]
    max_concurrency = int(sys.argv[2])
    max_pages = int(sys.argv[3])

    print(f"Beginning crawl of {base_url}")
    data = await crawl_site_async(base_url, max_concurrency, max_pages)

    print(f"Crawled {len(data.values())} pages...")

    write_json_report(data)

    with open("report.json", "r") as f:
        print(f.read())

if __name__ == "__main__":
    asyncio.run(main())
