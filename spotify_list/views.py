# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render
from django import template
from django.views.generic import ListView, DetailView

import os
import csv
import wget
import logging
import unicodedata
import json
import youtube_dl

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

from spotify_list.models import Song, Playlist



# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = "AIzaSyBIHbo9jl62SMsy4Eos7qhgidSEHHChUI0"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def youtube_search(search_string, max_results):
    youtube = build(YOUTUBE_API_SERVICE_NAME,
                    YOUTUBE_API_VERSION,
                    developerKey=DEVELOPER_KEY)

    # Call the search.list method to retrieve results matching the specified
    # query term.
    search_response = youtube.search().list(
                                    q=search_string,
                                    part="id,snippet",
                                    maxResults=max_results
                                    ).execute()

    videos = []
    channels = []
    playlists = []

    # Add each result to the appropriate list, and then display the lists of
    # matching videos, channels, and playlists.
    search_result = None
    for search_result in search_response.get("items", []):
        if search_result["id"]["kind"] == "youtube#video":
            videos.append("%s (%s)" % (search_result["snippet"]["title"],
                                        search_result["id"]["videoId"]))

    if search_result is not None and 'videoId' in search_result['id']:
        return (search_result['id']['videoId'])
    else:
        return("")


def country_code_to_search_term(country_code):
        if country_code == "do":
            pl_search_term = 'Top 100 do'
        elif country_code == "spain":
            pl_search_term = 'Top 100 es'
        elif country_code == "usa":
            pl_search_term = 'Top 100 us'
        elif country_code == "uk":
            pl_search_term = 'Top 100 gb'
        elif country_code == "global":
            pl_search_term = 'Top 100 global'
        else:
            pl_search_term = 'Top 100 global' 
        return pl_search_term


def download_file(request, yt_id):

    def remove_accents(mystr):
        """Changes accented characters (áüç...) to their unaccented counterparts (auc...)."""
        s = ''.join((c for c in unicodedata.normalize('NFD',unicode(mystr)) if unicodedata.category(c) != 'Mn'))
        return s.decode()

    def hooks(data):
        if data['status'] == 'finished':
            global filename
            data['filename'] = remove_accents(data['filename']).replace(",", "")
            filename = data['filename']
            filename = os.path.splitext(filename)[0]+'.mp3'
            return filename

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'progress_hooks': [hooks],
        'outtmpl': '%(title)s.%(ext)s'
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download(['http://www.youtube.com/watch?v='+yt_id])

    try:
        response = HttpResponse()
        response['Content-Type'] = 'application/mp3'
        response['X-Accel-Redirect'] = '/files/' + filename
        response['Content-Disposition'] = 'attachment;filename=' + filename
    except Exception:
        raise Http404
    return response


def dl_any_mp3(request):
    context = {}
    return render(request, 'spotify_list/dl_any_mp3.html', context)


def download_and_parse_csvs(request):

    countries = ['global', 'es', 'us', 'do', 'gb']

    song_fields = ['position', 'title', 'artist', 'streams', 'spotify_id', 'yt_id']

    Playlist.objects.all().delete()
    Song.objects.all().delete()

    for country in countries:

        url = 'https://spotifycharts.com/regional/'+country+'/daily/latest/download'

        pl_title = "Top 100 " + country
        pl_spotify_id = "NA"

        csvfile = wget.download(url)

        # Parse the CSV file
        songs = []
        with open(csvfile, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=str(u','), quotechar=str(u'"'))
            for row in reader:
                print ("Parseando la row = %s" % row)
                song_dict = {}
                for i, e in enumerate(row):
                    song_dict[song_fields[i]] = e.decode('utf-8')
                    if i == len(row) - 1:
                        # Extraer el spotify_id de la url leida del archivo CSV
                        song_dict[song_fields[i]] = e.decode('utf-8').rsplit('/', 1)[-1]

                if song_dict['position'] == "101":
                    break

                # buscar en Youtube el video correspondiente a cada canción
                try:
                    song_dict[song_fields[len(song_fields)-1]] = youtube_search(song_dict['title']+' '+song_dict['artist'], 1)

                    try:
                        s = Song(position = song_dict['position'],
                                 title = song_dict['title'],
                                 artist = song_dict['artist'],
                                 yt_id = song_dict['yt_id'],
                                 spotify_id = song_dict['spotify_id'])
                        s.save()

                        pl = Playlist(title = pl_title,
                                      songs = s)
                        pl.save()
                    except ValueError, e:
                        print "Pass: %s" % e

                except HttpError, e:
                    print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
                # fin busqueda en youtube

    context = {}
    context['country'] = country
    context['songs'] = songs
    return render(request, 'spotify_list/update_lists.html', context)


def borrar_mp3_y_csv (request):

    filelist = [ f for f in os.listdir(".") if f.endswith(".mp3") or f.endswith(".csv")]
    for f in filelist:
        os.remove(f)
    context = {}
    return render(request, 'spotify_list/borrar_mp3_y_csv.html', context)


class SongListView(ListView):
    model = Song

    def get_context_data(self, **kwargs):
        context = super(SongListView, self).get_context_data(**kwargs)
        context['country'] = self.kwargs.get("country", "global")
        return context

    def get_queryset(self, **kwargs):
        country = self.kwargs.get("country", "global")
        pl_search_term = country_code_to_search_term(country)       
        queryset = Song.objects.filter(playlist__title=pl_search_term).order_by('position').distinct('position')
        return queryset

# class SongDetailView(DetailView):
#     model = Song

#     def get_context_data(self, **kwargs):
#         context = super(SongListView, self).get_context_data(**kwargs)
#         context['country'] = self.kwargs.get("country", "global")
#         print("context['object_list'] = %s" % context["object_list"])
#         return context