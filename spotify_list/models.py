from __future__ import unicode_literals

from django.db import models

# Create your models here.

class Song (models.Model):
	title = models.CharField(max_length=140)
	artist = models.CharField(max_length=140)
	position = models.IntegerField()
	yt_id = models.CharField(max_length=20)
	spotify_id = models.CharField(max_length=40)

	def __unicode__(self):
		return "{0}. By: {1}".format(self.title, self.artist)

class Playlist (models.Model):
	title = models.CharField(max_length=100)
	songs = models.ForeignKey(Song)

class Genre (models.Model):
	title = models.CharField(max_length=30)
	playlists = models.ForeignKey(Playlist)



