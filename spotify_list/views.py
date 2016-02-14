# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from django.http import HttpResponse
from django.shortcuts import render

import os
import csv
import wget
import logging
import unicodedata

import youtube_dl

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.tools import argparser

from spotify_list.models import Songs, Playlists



# Set DEVELOPER_KEY to the API key value from the APIs & auth > Registered apps
# tab of
#   https://cloud.google.com/console
# Please ensure that you have enabled the YouTube Data API for your project.
DEVELOPER_KEY = "AIzaSyBIHbo9jl62SMsy4Eos7qhgidSEHHChUI0"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


def youtube_search(search_string, max_results):
    youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
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

    # print "Videos:\n", "\n".join(videos), "\n"

    if search_result is not None and 'videoId' in search_result['id']:
        return (search_result['id']['videoId'])
    else:
        return("")


def index(request, country="global"):

    # Download the CSV file from Spotify
    if country == "do":
        pl_search_term = 'Top 100 do'
    elif country == "spain":
        pl_search_term = 'Top 100 es'
    elif country == "usa":
        pl_search_term = 'Top 100 us'
    elif country == "uk":
        pl_search_term = 'Top 100 gb'
    elif country == "global":
        pl_search_term = 'Top 100 global'
    else:
        pl_search_term = 'Top 100 global'

    pls = Playlists.objects.filter(title = pl_search_term)

    songs = []

    for pl in pls:
        print pl.title
        song_dict  = {}
        song_dict['title'] = pl.songs.title
        song_dict['artist'] = pl.songs.artist
        song_dict['yt_id'] = pl.songs.yt_id
        song_dict['spotify_id'] = pl.songs.spotify_id
        song_dict['position'] = pl.songs.position
        songs.append(song_dict)

    context = {}
    context['country'] = country
    context['songs'] = songs
    return render(request, 'spotify_list/index.html', context)


def download_file(request, yt_id):
    print "******************++ EN DOWNLOAD FILE 1"
    def remove_accents(mystr):
        """Changes accented characters (áüç...) to their unaccented counterparts (auc...)."""
        s = ''.join((c for c in unicodedata.normalize('NFD',unicode(mystr)) if unicodedata.category(c) != 'Mn'))
        return s.decode()

    def hooks(data):
        if data['status'] == 'finished':
            global filename
            print ("data['filename'] = %s" % data['filename'])
            data['filename'] = remove_accents(data['filename'])
            filename = data['filename']
            print ("remove_accents(data['filename']) = %s" % data['filename'])
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
    print "******************++ EN DOWNLOAD FILE 1.5"
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        print "******************++ EN DOWNLOAD FILE 2"
        ydl.download(['http://www.youtube.com/watch?v='+yt_id])

    print "******************++ EN DOWNLOAD FILE 1"

    # fsock = open('/var/www/django_spotify/django_spotify/'+filename, 'r')
    # response = HttpResponse(fsock, content_type='audio/mpeg')
    # response['Content-Disposition'] = "attachment; filename=%s.mp3" % (filename)
    # return response

    try:
        response = HttpResponse()
        response['Content-Type'] = 'application/mp3'
        response['X-Accel-Redirect'] = '/files/' + filename
        response['Content-Disposition'] = 'attachment;filename=' + filename
    except Exception:
        raise Http404
    return response


def download_and_parse_csvs(request):

    countries = ['global', 'es', 'us', 'do', 'gb']

    song_fields = ['position', 'title', 'artist', 'streams', 'spotify_id', 'yt_id']

    # Borrar canciones y playlists anteriores en la bdd
    Playlists.objects.all().delete()
    Songs.objects.all().delete()

    for country in countries:

        url = 'https://spotifycharts.com/api/?download=true&limit=100&country='+country+'&recurrence=daily&date=latest&type=regional'

        pl_title = "Top 100 " + country
        pl_spotify_id = "NA"

        # Download the CSV file from Spotify
        csvfile = wget.download(url)

        # Parse the CSV file
        songs = []
        with open(csvfile, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=str(u','), quotechar=str(u'"'))
            for row  in reader:
                # import pdb; pdb.set_trace()
                song_dict = {}
                for i, e in enumerate(row):
                    # print ("Elemento %s = %s" % (i, e))
                    song_dict[song_fields[i]] = e.decode('utf-8')
                    if i == len(row) - 1:
                        # Extraer el spotify_id de la url leida del archivo CSV
                        song_dict[song_fields[i]] = e.decode('utf-8').rsplit('/', 1)[-1]

                # buscar en Youtube el video correspondiente a cada canción
                try:
                    song_dict[song_fields[len(song_fields)-1]] = youtube_search(song_dict['title']+' '+song_dict['artist'], 1)

                    try:
                        s = Songs(position = song_dict['position'],
                                    title = song_dict['title'],
                                    artist = song_dict['artist'],
                                    yt_id = song_dict['yt_id'],
                                    spotify_id = song_dict['spotify_id'])
                        s.save()

                        pl = Playlists(title = pl_title,
                                        songs = s)
                        pl.save()
                    except ValueError, e:
                        print "Pass"

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