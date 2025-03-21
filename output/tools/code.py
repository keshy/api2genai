import requests
from typing import Dict, Any, Optional


def get_bearer_token() -> str:
    # Replace with your actual bearer token retrieval logic
    return "YOUR_BEARER_TOKEN"


def get_url(base_url: str, path: str, params: Optional[Dict[str, Any]] = None) -> str:
    url = base_url + path
    if params:
        query_params = '&'.join([f'{key}={value}' for key, value in params.items() if value is not None])
        if query_params:
            url += '?' + query_params
    return url


def _call_api(url: str, method: str, headers: Dict[str, str], json: Optional[Dict[str, Any]] = None) -> Any:
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=json)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=json)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        elif method == "PATCH":
            response = requests.patch(url, headers=headers, json=json)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        if response.status_code == 204:
            return None

        return response.json() if response.content else None

    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None
