from playwright.sync_api import sync_playwright
from typing import List, Dict


class RequestSniffer:
    # https://playwright.dev/python/docs/library

    """
    This class provides automated web browser control.
    It captures and returns headers, response body content, and cookies from the website passed
    as an argument to the method.
    return [
                {'url': str, 'method': str,
                'request_headers': {k:v, ...}, 'status': int,
                'response_headers': {k:v, ...},
                'response_body': str|dict,
                'cookies': [{k:v, ...}]
    """

    def __init__(self, headless: bool = True):  # do/dont display browser
        self.headless = headless

    def fetch_request_details(self, url: str) -> List[Dict]:
        traffic_data = []
        request_store = {}

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
                if request not in request_store:
                    return

                try:
                    body = response.text()
                except Exception as e:
                    body = f"[Error getting response body: {e}]"

                entry = request_store[request]
                entry.update({
                    'status': response.status,
                    'response_headers': dict(response.headers),
                    'response_body': body,
                })
                traffic_data.append(entry)

            page.on("request", handle_request)
            page.on("response", handle_response)

            try:
                cleaned_url = url.rstrip('/')
                page.goto(cleaned_url, wait_until="domcontentloaded", timeout=10000)
                page.wait_for_load_state("networkidle", timeout=10000)

                # Получаем cookies после завершения всех операций
                cookies = context.cookies()
                # Добавляем cookies ко всем записям
                for entry in traffic_data:
                    entry['cookies'] = cookies

            except Exception as e:
                print(f"Navigation error: {e}")
            finally:
                # Удаляем обработчики перед закрытием
                page.remove_listener("request", handle_request)
                page.remove_listener("response", handle_response)
                browser.close()
        return traffic_data
