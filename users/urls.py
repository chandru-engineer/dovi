from django.urls import path
from users.views import MinistryLoginAPIView, PublisherLoginAPIView, CreateMinistryView, CreatePublisherView, MeAPIView


urlpatterns = [
    # create ministry
    path("create/ministry", CreateMinistryView.as_view(), name='ministry_view'), 
    path('create/publisher', CreatePublisherView.as_view(), name='create_publisher'), 

    path("login/ministry", MinistryLoginAPIView.as_view(), name='ministry_login'), 
    path("login/publisher", PublisherLoginAPIView.as_view(), name='ministry_login'), 

    path('me/', MeAPIView.as_view(), name='me'),
]


 