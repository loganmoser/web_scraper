import unittest
from crawl import normalize_url, get_heading_from_html, get_first_paragraph_from_html, get_urls_from_html, get_images_from_html, extract_page_data


class TestCrawl(unittest.TestCase):
    def test_normalize_url(self):
        input_url = "https://www.boot.dev/blog/path"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_is_normalized(self):
        input_url = "http://www.boot.dev/blog/path"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_stripped_url(self):
        input_url = "www.BOOT.dev/blog/path/"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    def test_is_normal(self):
        input_url = "https://www.boot.dev/blog/path/"
        actual = normalize_url(input_url)
        expected = "www.boot.dev/blog/path"
        self.assertEqual(actual, expected)

    
    def test_get_heading_from_html_basic(self) -> None:
        input_body = "<html><body><h1>Test Title</h1></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "Test Title"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_h2_fallback(self) -> None:
        input_body = "<html><body><h2>Fallback Title</h2></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "Fallback Title"
        self.assertEqual(actual, expected)

    def test_get_heading_from_html_with_whitespace(self) -> None:
        input_body = "<html><body><h1>   Whitespace Title   </h1></body></html>"
        actual = get_heading_from_html(input_body)
        expected = "Whitespace Title"
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_basic(self) -> None:
        input_body = "<html><body><p>This is the first paragraph.</p></body></html>"
        actual = get_first_paragraph_from_html(input_body)
        expected = "This is the first paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_main_priority(self) -> None:
        input_body = """<html><body>
            <p>Outside paragraph.</p>
            <main>
                <p>Main paragraph.</p>
            </main>
        </body></html>"""
        actual = get_first_paragraph_from_html(input_body)
        expected = "Main paragraph."
        self.assertEqual(actual, expected)

    def test_get_first_paragraph_from_html_no_paragraph(self) -> None:
        input_body = "<html><body><h1>No paragraphs here</h1></body></html>"
        actual = get_first_paragraph_from_html(input_body)
        expected = ""
        self.assertEqual(actual, expected)

    def test_get_urls_from_html_absolute(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><a href="https://crawler-test.com"><span>Boot.dev</span></a></body></html>'
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com"]
        self.assertEqual(actual, expected)

    def test_get_multiple_urls(self):
        input_url = "https://crawler-test.com"
        input_body = """
            <html>
                <body>
                    <a href="https://crawler-test.com">
                        <span>Boot.dev</span>
                    </a>
                    <a href="https://crawler-test.com/second_link">
                        <span>Extra link</span>
                    </a>
                </body>
            </html>
            """
        actual = get_urls_from_html(input_body, input_url)
        expected = ["https://crawler-test.com", "https://crawler-test.com/second_link"]
        self.assertEqual(actual, expected)

    def test_get_urls_empty(self):
        input_url = "https://crawler-test.com"
        input_body = """
            <html>
                <body>
                    <h1> NO LINKS!!! </h1>
                </body>
            </html>
            """
        actual = get_urls_from_html(input_body, input_url)
        expected = []
        self.assertEqual(actual, expected)
    
    def test_get_images_from_html_relative(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="/logo.png" alt="Logo"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/logo.png"]
        self.assertEqual(actual, expected)

    def test_get_images_from_html_nested(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="/logos/logo.png" alt="logo"></body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/logos/logo.png"]
        self.assertEqual(actual, expected)

    def test_get_multiple_images(self):
        input_url = "https://crawler-test.com"
        input_body = '<html><body><img src="/logo.png" alt="logo"><img src="/cat.png" alt="cat"</body></html>'
        actual = get_images_from_html(input_body, input_url)
        expected = ["https://crawler-test.com/logo.png", "https://crawler-test.com/cat.png"]
        self.assertEqual(actual, expected)
    def test_extract_page_data_basic(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h1>Test Title</h1>
            <p>This is the first paragraph.</p>
            <a href="/link1">Link 1</a>
            <img src="/image1.jpg" alt="Image 1">
        </body></html>"""
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "Test Title",
            "first_paragraph": "This is the first paragraph.",
            "outgoing_links": ["https://crawler-test.com/link1"],
            "image_urls": ["https://crawler-test.com/image1.jpg"],
        }
        self.assertEqual(actual, expected)
    def test_extracted_page_data_stripped(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <h1> TEST TITLE     </h1>
            <p>      parAGRaph 1 </p>
            <a href="/link1"> Link 1 </a>
            <img src="/image1.jpg" alt="Image 1">
            </body></html>
            """
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "TEST TITLE",
            "first_paragraph": "parAGRaph 1",
            "outgoing_links": ["https://crawler-test.com/link1"],
            "image_urls": ["https://crawler-test.com/image1.jpg"]
        }
        self.assertEqual(actual, expected)
    def test_extracted_page_data_missing(self):
        input_url = "https://crawler-test.com"
        input_body = """<html><body>
            <p>This is the first paragraph</p>
            <a href="/link1"> Link 1 </a>
            <a href="/link2"> Link 2 </a>
            <img src="/img1.png" alt="Image 1">
            <img src="/img2.png" alt="Image 2">
            </body></html>
            """
        actual = extract_page_data(input_body, input_url)
        expected = {
            "url": "https://crawler-test.com",
            "heading": "",
            "first_paragraph": "This is the first paragraph",
            "outgoing_links": ["https://crawler-test.com/link1", "https://crawler-test.com/link2"],
            "image_urls": ["https://crawler-test.com/img1.png", "https://crawler-test.com/img2.png"]
        }
        self.assertEqual(actual, expected)

if __name__ == "__main__":
    unittest.main()
