from django.urls import path

from .views import (
    Index,
    Confidential_information,
    ContactsView,
    Blog,
    RibbonConstructorView,
    Subscribe,
    Unsubscribe,
    Unsubscribe_confirm,
    ShowNews,
)

urlpatterns = [
    path("", Index.as_view(), name="index"),
    path("confidential_information/", Confidential_information.as_view(), name="confidential_information"),
    path("contacts/", ContactsView.as_view(), name="contacts"),
    path("blog/", Blog.as_view(), name="blog"),
    path("constructor/", RibbonConstructorView.as_view(), name="ribbon_constructor"),

    path("subscribe/", Subscribe, name="subscribe"),
    path("unsubscribe/", Unsubscribe, name="unsubscribe_request"),
    path("unsubscribe/confirm/<str:token>/", Unsubscribe_confirm, name="unsubscribe_confirm"),

    path("news/<slug:news_slug>/", ShowNews.as_view(), name="news"),
]
