from django.contrib.auth import authenticate
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserProfile, UserType
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.models import User
from users.serializers import MeSerializer
from commons.generate_did import generate_did_document

class CreateMinistryView(APIView): 
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        phone_number = request.data.get("phone_number", "")
        address = request.data.get("address", "")
        org_name = request.data.get("org_name", "")

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        did = generate_did_document()
        profile = UserProfile.objects.create(
            user=user,
            user_type=UserType.MINISTRY.value,
            phone_number=phone_number,
            address=address,
            org_name=org_name, 
            did_url=did
        )

        return Response({"message": "Ministry user created successfully", "username": username}, status=status.HTTP_201_CREATED)


class CreatePublisherView(APIView): 
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")
        phone_number = request.data.get("phone_number", "")
        address = request.data.get("address", "")
        org_name = request.data.get("org_name", "")

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(username=username, email=email, password=password)
        did = generate_did_document()
        profile = UserProfile.objects.create(
            user=user,
            user_type=UserType.PUBLISHER.value,
            phone_number=phone_number,
            address=address,
            org_name=org_name, 
            did_url = did
        )
        return Response({"message": "Publisher user created successfully", "username": username}, status=status.HTTP_201_CREATED)


class MinistryLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user and user.profile.user_type == UserType.MINISTRY.value:
            # Generate JWT token
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Ministry login successful',
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid credentials or not a Ministry user'}, status=status.HTTP_401_UNAUTHORIZED)


class PublisherLoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)

        if user and user.profile.user_type == UserType.PUBLISHER.value:
            # Generate JWT token
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'Publisher login successful',
                'access': str(refresh.access_token),
                'refresh': str(refresh)
            }, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid credentials or not a Publisher user'}, status=status.HTTP_401_UNAUTHORIZED)



class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = MeSerializer(user)
        return Response(serializer.data, status=200)