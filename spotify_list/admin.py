from django.contrib import admin
from .models import Song, Playlist


class SongsAdmin(admin.ModelAdmin):
    list_display = ['title', 'artist', 'id', 'yt_id', 'spotify_id']
    search_fields = ['title', 'artist']
    fields = ['title', 'artist', 'yt_id', 'spotify_id']


class PlaylistsAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'songs']
    fields = ['title', 'songs']


admin.site.register(Song, SongsAdmin)
admin.site.register(Playlist, PlaylistsAdmin)
