from django.urls import path
from vcs.views import CreateMinistryPostView, CreatePublisherPostView, VerifyContentView, FetchRelatedDocumentView, PostListView



urlpatterns = [
    path("create/ministry/post", CreateMinistryPostView.as_view(), name='create-ministry-post'),
    path("create/publiher/post", CreatePublisherPostView.as_view(), name='create-publisher-post'),


    path('post/list', PostListView.as_view(), name='post-list'), 

    path('verify', VerifyContentView.as_view(), name='verify-content'),

    path('fetch/related/docs/<str:did_id>', FetchRelatedDocumentView.as_view(), name='fetch-related-docs'),
]


