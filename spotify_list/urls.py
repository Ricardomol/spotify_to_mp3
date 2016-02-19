 
"""spotify_list app URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from . import views

app_name = 'spotify_list'
urlpatterns = [
    url(r'^$', views.index, name = 'index'),
    url(r'^(?P<country>[a-z]*)$', views.index, name = 'index'),
    url(r'^download_file/(?P<yt_id>[-\w]+)', views.download_file, name = 'download_file'),
    url(r'^update_lists$', views.download_and_parse_csvs, name='dl_and_parse'),
    url(r'^borrar_mp3_y_csv$', views.borrar_mp3_y_csv, name='borrar_mp3_y_csv'),
    url(r'^dl_any_mp3$', views.dl_any_mp3, name='dl_any_mp3'),
]
