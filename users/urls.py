from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from . import views

urlpatterns = [
    url(r'^register/$', views.register),
    url(r'^login/$', views.login),
    url(r'^profile/(?P<id>[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})$', views.get_profile),
]

urlpatterns = format_suffix_patterns(urlpatterns)
