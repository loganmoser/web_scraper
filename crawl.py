from urllib.parse import urlsplit

def normalize_url(url: str) -> str:

    url_split = urlsplit(url)

    path = f"{url_split.netloc}{url_split.path}".rstrip("/").lower()  

    return path
