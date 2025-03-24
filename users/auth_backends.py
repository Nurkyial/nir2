import requests
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.backends import BaseBackend

FASTAPI_URL = settings.FASTAPI_BASE_URL

class FastAPIAuthBackend(BaseBackend):
    """Аутентификация через FastAPI"""

    def authenticate(self, request, username=None, password=None):
        url = f"{FASTAPI_URL}/auth/login"
        data = {"username":username, "password":password}
        response = requests.post(url, json=data)

        if response.status_code == 200:
            user_data = response.json
            return self.get_or_create_user(user_data)
        return None
    
    def get_or_create_user(self, user_data):
        """Создание временного пользователя без записи в БД"""
        user = User(username=user_data["username"])
        user.is_authenticated = True
        return user
    
    def get_user(self, user_id):
        return None