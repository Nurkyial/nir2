from django.utils.deprecation import MiddlewareMixin
import requests
from django.conf import settings

FASTAPI_URL = settings.FASTAPI_BASE_URL

class FastAPIAuthMiddleware(MiddlewareMixin):
    def process_request(self, request):
        token = request.session.get("access_token")
        if token:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{FASTAPI_URL}/user/me", headers=headers)

            if status_code == 200:
                request.user_data = response.json()
            else:
                request.user_data = None
        else:
                request.user_data = None