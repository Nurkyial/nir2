import requests
from django.conf import settings

FASTAPI_URL = settings.FASTAPI_BASE_URL

def fastapi_request(endpoint, method="GET", data=None, token=None, use_query_params=False):
    url = f"{FASTAPI_URL}/{endpoint}"
    
    headers = {
        "Authorization": f"Bearer {token}" if token else "",
        "Content-Type": "application/json"
    }
    
    try:
        # Если FastAPI ожидает параметры в URL, передаём их через `params`
        params = data if use_query_params else None
        json_data = None if use_query_params else data

        if method == 'GET':
            response = requests.get(url, headers=headers, params=params)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=json_data, params=params)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=json_data, params=params)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # Логируем полный ответ от FastAPI
        print(f"FastAPI Response [{response.status_code}]: {response.text}")

        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        return {"error": f"HTTP {response.status_code}: {response.text}"}
    
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return {"error": str(req_err)}
