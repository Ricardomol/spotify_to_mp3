from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Songs (models.Model):
	title = models.CharField(max_length=80)
	artist = models.CharField(max_length=80)
	position = models.IntegerField()
	yt_id = models.CharField(max_length=20)
	spotify_id = models.CharField(max_length=40)

class Playlists (models.Model):
	title = models.CharField(max_length=80)
	songs = models.ForeignKey(Songs)

class Genres (models.Model):
	title = models.CharField(max_length=30)
	playlists = models.ForeignKey(Playlists)



