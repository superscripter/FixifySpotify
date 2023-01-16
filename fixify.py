import os
import spotipy 
from spotipy.oauth2 import SpotifyOAuth

#pip install spotipy --upgrade

'''
Script Assumptions:
Your "My Library" songs are downloaded
All playlists are set as downloaded
If you have already used this script and a song is no longer downloaded, you want that song removed from the masTer playlist
You do not have a playlist with the name "Master" or if you do it is used for the purpose of this script
This name can be set below with the master_playlist_name

This script will not set the master_playlist_name to be a downloaded playlist
'''
master_playlist_name = 'Master'

#set verbose to True for more info when the script is running (sanity checks really)
verbose = False


os.environ['SPOTIPY_CLIENT_ID'] = '041f85aa425a4d27b986f168591cd8c3'
os.environ['SPOTIPY_CLIENT_SECRET'] = '9b122386bb304eb7849a21c75819dbc5'
os.environ['SPOTIPY_REDIRECT_URI'] = 'http://localhost:8080'

scope='user-library-read playlist-modify playlist-modify-private playlist-read-private'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))

all_tracks = set()

#----------------------------------YOUR LIBRARY------------------------------------------

total_library_count = 0
library_call_limit = 20
library_continue = True

while(library_continue):

    library_continue = False
    library_track_count = 0
    saved_library_tracks = sp.current_user_saved_tracks(library_call_limit, total_library_count)

    for track in saved_library_tracks['items']:
        library_track_count = library_track_count + 1
        track_id = track['track']['id']
        if(track_id != None):
            all_tracks.add(track_id)


    if(library_track_count == library_call_limit):
        library_continue = True

    total_library_count = total_library_count + library_track_count

print('\n')
print("First checking songs in Your Library")
print("Total library track count found: ", total_library_count)
total_library_track_count = len(all_tracks)
print("Found ", total_library_track_count, " unique tracks")

#----------------------------------ALBUMS------------------------------------------

total_album_count = 0
album_call_limit = 50
album_continue = True

while(album_continue):

    album_continue = False
    album_count = 0
    saved_albums = sp.current_user_saved_albums(album_call_limit, total_album_count)

    for album in saved_albums['items']:

        album_count = album_count + 1

        album_id   = album['album']['id']
        album_tracks = sp.album_tracks(album_id)['items'] #assumes all albums have under 50 tracks

        for track in album_tracks:
            track_id = track['id']
            if(track_id != None):
                all_tracks.add(track_id)

    if(album_count == album_call_limit):
        album_continue = True

    # the total album count is used as the offset in case we need to search for more albums
    total_album_count = total_album_count + album_count

print('\n')
print("Now checking songs in your saved albums")
print("Total album count found: ", total_album_count)
total_album_track_count = len(all_tracks) - total_library_track_count
print("Found ", total_album_track_count, " more unique tracks")

#-------------------------------------PLAYLISTS----------------------------------------

total_playlist_count = 0
playlist_continue = True
master_playlist_id = 0

while(playlist_continue):

    playlist_count = 0
    playlist_continue = False
    playlists = sp.current_user_playlists(50, total_playlist_count)

    for playlist in playlists['items']:

        playlist_count = playlist_count + 1

        playlist_name = playlist['name']
        playlist_id = playlist['id']        

        if playlist_name == master_playlist_name:
            master_playlist_id = playlist_id
            continue # dont ingest data from the master playlist

        total_playlist_track_count = 0
        playlist_track_continue = True
               
        while(playlist_track_continue):

            playlist_track_count = 0
            playlist_track_continue = False
            playlist_tracks = sp.playlist_tracks(playlist_id, offset = total_playlist_track_count)

            for track_info in playlist_tracks['items']:
                playlist_track_count = playlist_track_count + 1

                track_id = track_info['track']['id']
                if(track_id != None):
                    all_tracks.add(track_id)

            # if the playlist track count is 100, there could be more, contiue looking
            if(playlist_track_count == 100):
                playlist_track_continue = True

            # the total album count is used as the offset in case we need to search for more albums
            total_playlist_track_count = total_playlist_track_count + playlist_track_count

        if(verbose):
            print(playlist_name, " and track count: ",total_playlist_track_count)

    # if the count is 50, there could be more, continue looking
    if(playlist_count == 50):
        playlist_continue = True

    # the total count is used as the offset in case we need to search for more
    total_playlist_count = total_playlist_count + playlist_count

print('\n')
print("Now checking songs in your playlists")
print("Total playlist count found: ", total_playlist_count)
print("Found ", len(all_tracks) - total_album_track_count - total_library_track_count, " more unique tracks")

#-------------------------------------MASTER PLAYLIST----------------------------------------

print('\n')
print("Total unique track count: ", len(all_tracks))

user_info = sp.current_user()
user_id   = user_info['id']
master_playlist_info = []
track_add_limit = 100

if(master_playlist_id):

    master_tracks = set()

    total_master_track_count = 0
    master_track_call_limit = 100
    master_track_continue = True

    while(master_track_continue):

        master_track_continue = False
        master_track_count = 0
        master_playlist_tracks = sp.playlist_tracks(master_playlist_id, limit = master_track_call_limit, offset = total_master_track_count)

        for track in master_playlist_tracks['items']:
            master_track_count = master_track_count + 1
            master_tracks.add(track['track']['id'])

        if(master_track_count == master_track_call_limit):
            master_track_continue = True

        total_master_track_count = total_master_track_count + master_track_count

    print("A master playlist was already found with ", len(master_tracks), " unique tracks")

    new_unique_tracks = list(all_tracks.difference(master_tracks))
    tracks_to_add = len(new_unique_tracks)
    track_index = 0
    while(tracks_to_add > track_add_limit):
        sp.user_playlist_add_tracks(user_id, master_playlist_id, new_unique_tracks[track_index:track_index + track_add_limit])
        track_index = track_index + track_add_limit
        tracks_to_add = tracks_to_add - track_add_limit
    if(tracks_to_add):
        sp.user_playlist_add_tracks(user_id, master_playlist_id, new_unique_tracks[track_index:])

    old_unique_tracks = list(master_tracks.difference(all_tracks))
    tracks_to_remove= len(old_unique_tracks)
    track_index = 0

    while(tracks_to_remove > track_add_limit):
        sp.user_playlist_remove_all_occurrences_of_tracks(user_id, master_playlist_id, old_unique_tracks[track_index:track_index + track_add_limit])
        track_index = track_index + track_add_limit
        tracks_to_remove = tracks_to_remove - track_add_limit
    if(tracks_to_remove):
        sp.user_playlist_remove_all_occurrences_of_tracks(user_id, master_playlist_id, old_unique_tracks[track_index:])

    print(len(new_unique_tracks), " new tracks will be added to the master playlist, and ",len(old_unique_tracks), " will be removed. Complete")
else:
    print("No master playlist has been found, all ", len(all_tracks)," will be added. Complete")
    master_playlist_info = sp.user_playlist_create(user_id, master_playlist_name)

    all_tracks = list(all_tracks)
    tracks_to_add = len(all_tracks)
    track_index = 0
    while(tracks_to_add > track_add_limit):
        sp.user_playlist_add_tracks(user_id, master_playlist_info['id'], all_tracks[track_index:track_index + track_add_limit])
        track_index = track_index + track_add_limit
        tracks_to_add = tracks_to_add - track_add_limit
    if(tracks_to_add):
        sp.user_playlist_add_tracks(user_id, master_playlist_info['id'], all_tracks[track_index:])


"""
Notes: 
The smartest way of doing this, is checking the most current time the master playlist was updated and only adding in songs liked after that period.
But, time is not a priority with this scrpt currently so the simpllier method of a manual check will be done
"""