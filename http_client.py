import requests


class HttpClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url.rstrip("/") if base_url else ""
        
    def safe_json_response(response):
    try:
        return response.json()
    except Exception:
        return {
            "_not_json": True,
            "status_code": response.status_code,
            "text": response.text,
        }

    def request(self, method: str, url: str, headers=None, json_body=None):
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=json_body,
            timeout=60,
        )

        return response

    def post(self, path: str, headers=None, json=None):
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = requests.post(
            url,
            headers=headers,
            json=json,
            timeout=60,
        )

        return {
            "status_code": response.status_code,
            "text": response.text,
            "json": self._safe_json(response),
        }

    def get(self, path: str, headers=None):
        url = f"{self.base_url}/{path.lstrip('/')}"
        response = requests.get(
            url,
            headers=headers,
            timeout=60,
        )

        return {
            "status_code": response.status_code,
            "text": response.text,
            "json": self._safe_json(response),
        }

    def _safe_json(self, response):
        try:
            return response.json()
        except Exception:
            return None