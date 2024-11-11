# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'is_active']

class UserStatusSerializer(serializers.Serializer):
    login = serializers.CharField()

class RegisterSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField(write_only=True)
    status = serializers.CharField()