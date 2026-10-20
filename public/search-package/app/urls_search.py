# Добавьте в urls.py приложения (до маршрутов вида <slug:...>/, чтобы "search" не принялся за slug):
from django.urls import path

from .views_search import search_page, search_suggest

urlpatterns = [
    path("search/", search_page, name="search"),
    path("search/suggest/", search_suggest, name="search_suggest"),
]
