import sys
from crawl import crawl_page


def main():
    
    if len(sys.argv) < 2:
        print("no website provided")
        sys.exit(1)
    if len(sys.argv) > 2:
        print("too many arguments provided")
        sys.exit(1)

    base_url = sys.argv[1]

    print(f"starting crawl of: {base_url}")

    html = crawl_page(base_url)

    print(f"Crawled {len(html)} pages...")




if __name__ == "__main__":
    main()
