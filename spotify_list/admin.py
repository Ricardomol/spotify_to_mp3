from django.contrib import admin
from .models import Songs, Playlists

# Register your models here.

class SongsAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'artist', 'yt_id', 'spotify_id']
    fields = ['title', 'artist', 'yt_id', 'spotify_id']

class PlaylistsAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'songs']
    fields = ['title', 'songs']

admin.site.register(Songs, SongsAdmin)
admin.site.register(Playlists, PlaylistsAdmin)
