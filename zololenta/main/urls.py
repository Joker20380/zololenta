from django.urls import path, re_path
from django.views.decorators.csrf import csrf_exempt
from .views import *

urlpatterns = [
                path('', Index.as_view(), name='index'),
                path('confidential_information/', Confidential_information.as_view(), name='confidential_information'),
                path('contacts/', ContactsView.as_view(), name='contacts'),
                path('subscribe/', Subscribe, name='subscribe'),
                path('unsubscribe/', Unsubscribe, name='unsubscribe_request'),
    			path('unsubscribe/confirm/<str:token>/', Unsubscribe_confirm, name='unsubscribe_confirm'),
    			path('news/<slug:news_slug>/', ShowNews.as_view(), name='news'),

              ]