# В urls.py приложения (до общих маршрутов со slug):
from django.urls import path, re_path

from .views_podborki import podborka_detail, podborki_index

urlpatterns = [
    path("podborki/", podborki_index, name="podborki"),
    re_path(r"^podborki/(?P<path>[-a-z0-9_]+(?:/[-a-z0-9_]+){0,2})/$", podborka_detail, name="podborka"),
]
