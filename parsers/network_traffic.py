from playwright.sync_api import sync_playwright
from typing import List, Dict


class RequestSniffer:
    # https://playwright.dev/python/docs/library

    """
    This class provides automated web browser control.
    It captures and returns headers, response body content, and cookies from the website passed
    as an argument to the method.
    """

    def __init__(self, headless: bool = True):  # do/dont display browser
        self.headless = headless

    def fetch_request_details(self, url: str) -> List[Dict]:
        traffic_data = []
        request_store: Dict[object, Dict] = {}

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context()
            page = context.new_page()

            def handle_request(request):
                request_store[request] = {
                    'url': request.url,
                    'method': request.method,
                    'request_headers': dict(request.headers),
                }

            def handle_response(response):
                request = response.request

                if request in request_store:
                    try:
                        body = response.text()
                    except Exception as e:
                        body = f"[Error getting response body: {e}]"

                    entry = request_store[request]
                    entry.update({
                        'status': response.status,
                        'response_headers': dict(response.headers),
                        'response_body': body,
                        'cookies': context.cookies(),
                    })
                    traffic_data.append(entry)

            page.on("request", handle_request)
            page.on("response", handle_response)

            page.goto(url, wait_until="networkidle")
            browser.close()

        return traffic_data
