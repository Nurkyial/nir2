import requests
from django.conf import settings

FASTAPI_URL = settings.FASTAPI_BASE_URL

def fastapi_request(endpoint, method="GET", data=None, token=None, files=None, use_query_params=False):
    url = f"{FASTAPI_URL}/{endpoint}"
    
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}" if token else ""
    if not files:
        headers["Content-Type"] = "application/json"
        
    params = data if use_query_params else None
    json_data = None if use_query_params or files else data
 
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, json=json_data, params=params)
        elif method == 'POST':
            if files:
                print('f')
                response = requests.post(url, headers=headers, params=params, files=files)
            else:
                print('e')
                response = requests.post(url, headers=headers, json=json_data, params=params)
        elif method == 'PUT':
            response = requests.put(url, headers=headers, json=json_data, params=params)
        elif method == 'DELETE':
            response = requests.delete(url, headers=headers, params=params)
        elif method == 'PATCH':
            response = requests.patch(url, headers=headers, json=json_data, params=params)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # Логируем полный ответ от FastAPI
        # print(f"FastAPI for API: {endpoint} Response [{response.status_code}]: {response.text}")

        response.raise_for_status()
        return response.json(), response.status_code
    
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err} - Response: {response.text}")
        return {"error": f"HTTP {response.status_code}: {response.text}"}, response.status_code
    
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return {"error": str(req_err)}, response.status_code
