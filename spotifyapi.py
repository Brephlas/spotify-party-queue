import requests
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
from flask import redirect
from noauthException import noauthException
import pickle
from pathlib import Path

class spotifyapi:
    def __init__(self, client_id, client_secret, redirect_uri, port):
        self.redirect_uri = redirect_uri
        self.port = port
        self.client_id = client_id
        self.client_secret = client_secret
        self.authenticated = False
        self.header = {'Accept' : 'application/json', 'Content-Type' : 'application/json'}
        self.playlists = []
        self.tracks = [] # helper for storing saved tracks
        self.playlist_tracks = {} # helper for storing tracks of playlists
        self.recent_tracks = [] # helper for storing recently played tracks
        self.play_next = []
        self.currently_playing = ''
        self.loadOfflineStorage()

    def setHeader(self, token):
        self.header = {'Accept' : 'application/json', 'Content-Type' : 'application/json', 'Authorization' : 'Bearer '+token}

    def setRefreshToken(self, refresh_token):
        self.refresh_token = refresh_token

    def setExpiryTime(self, time):
        self.expiry = time

    def setToken(self, token, refresh_token, expiry):
        self.setHeader(token)
        self.access_token = token
        self.setRefreshToken(refresh_token)
        self.setExpiryTime(expiry)
        self.authenticated = True

    def isAuthenticated(self):
        return self.authenticated

    def getAccessToken(self):
        if self.access_token:
            return self.access_token
        else:
            raise noauthException

    def sendRequest(self, url):
        r = requests.get(url, headers=self.header)
        if 'The access token expired' in r.text:
            # refresh the token automatically if it expired
            self.refreshToken()
            r = requests.get(url, headers=self.header)
            return json.loads(r.text)
        elif 'Only valid bearer authentication supported' in r.text:
            # first authentication missing
            raise noauthException
        else:
            # prevent error if there is no song played currently
            try:
                return json.loads(r.text)
            except:
                return None

    def sendRequest_PUT(self, url):
        r = requests.put(url, headers=self.header)
        if 'The access token expired' in r.text:
            # refresh the token automatically if it expired
            self.refreshToken()
            r = requests.put(url, headers=self.header)
            return json.loads(r.text)
        elif 'Only valid bearer authentication supported' in r.text:
            # first authentication missing
            raise noauthException
        else:
            # prevent error if there is no song played currently
            try:
                return json.loads(r.text)
            except:
                return None

    def authorize(self):
        #permissions = ['user-modify-playback-state', 'playlist-read-private', 'user-read-playback-state', 'user-library-read'] # without ability to modify playback
        permissions = ['user-modify-playback-state', 'playlist-read-private', 'user-read-playback-state', 'user-library-read', 'user-library-modify', 'user-read-recently-played'] # usage for e.g. save current song
        scope = '%20'.join(permissions)
        return redirect('https://accounts.spotify.com/authorize?client_id='+self.client_id+'&response_type=code&redirect_uri='+self.redirect_uri+':'+self.port+'/token&scope='+scope, code=302)

    def token(self, code):
        body_params = {'grant_type' : 'authorization_code', 'code' : code, 'redirect_uri' : self.redirect_uri+':'+self.port+'/token'}
        url='https://accounts.spotify.com/api/token'

        response=requests.post(url, data=body_params, auth = (self.client_id, self.client_secret))
        data = json.loads(response.text)
        self.setToken(data['access_token'], data['refresh_token'], data['expires_in'])

    def refreshToken(self):
        body_params = {'grant_type' : 'refresh_token', 'refresh_token' : self.refresh_token}
        url='https://accounts.spotify.com/api/token'

        response=requests.post(url, data=body_params, auth = (self.client_id, self.client_secret))
        data = json.loads(response.text)
        try:
            self.setToken(data['access_token'], data['refresh_token'], data['expires_in'])
        except KeyError:
            self.setToken(data['access_token'], self.refresh_token, data['expires_in'])

    def search(self, q, t):
        if not q or not t or q == 'None' or t == 'None':
            return ''
        try:
            data = self.sendRequest('https://api.spotify.com/v1/search?q='+str(q)+'&type='+str(t)+'&limit=20')
            tracks = []
            for track in data['tracks']['items']:
                artist = track['artists'][0]['name']
                song = track['name']
                uri = track['uri']
                cover_url = track['album']['images'][0]['url']
                tracks.append((artist, song, uri, cover_url))
            return tracks
        except (noauthException):
            raise noauthException

    def getSavedTracks(self, songs_dynamic_loading = True):
        counter = 0
        try:
            if self.tracks:
                data = self.sendRequest('https://api.spotify.com/v1/me/tracks?limit=1')
                for track in data['items']:
                    uri = track['track']['uri']
                if uri == self.tracks[0][2]:
                    # if the first local stored song matches with the api's first stored song
                    # there was no change made and we can use the local list
                    return self.tracks
                else:
                    tmp_list = []
                    for i in range(5):
                        offset = i * 5
                        data = self.sendRequest('https://api.spotify.com/v1/me/tracks?limit=5&offset='+str(offset))
                        for track in data['items']:
                            uri = track['track']['uri']
                            if uri == self.tracks[0][2]:
                                tmp_to_extend = self.tracks
                                tmp_list.extend(tmp_to_extend)
                                self.tracks = tmp_list
                                return self.tracks
                            else:
                                artist = track['track']['artists'][0]['name']
                                song = track['track']['name']
                                uri = track['track']['uri']
                                cover_url = track['track']['album']['images'][0]['url']
                                tmp_list.append((artist, song, uri, cover_url))

            # no tracks are stored
            self.tracks = []

            # determine if dynamic loading is enabled to load all songs at once or not
            if songs_dynamic_loading:
                data = self.sendRequest('https://api.spotify.com/v1/me/tracks?limit=50')
                
                for track in data['items']:
                    artist = track['track']['artists'][0]['name']
                    song = track['track']['name']
                    uri = track['track']['uri']
                    cover_url = track['track']['album']['images'][0]['url']
                    self.tracks.append((artist, song, uri, cover_url))
            else:
                # while there are saved songs left to collect
                while True:
                    offset = counter * 50
                    data = self.sendRequest('https://api.spotify.com/v1/me/tracks?limit=50&offset='+str(offset))
                
                    for track in data['items']:
                        artist = track['track']['artists'][0]['name']
                        song = track['track']['name']
                        uri = track['track']['uri']
                        cover_url = track['track']['album']['images'][0]['url']
                        self.tracks.append((artist, song, uri, cover_url))
                    if not data['items']:
                        # break out of loop as all songs are collected
                        break
                    counter = counter + 1
            return self.tracks
        except KeyError:
            raise noauthException

    def getRecentlyPlayed(self, songs_dynamic_loading = True):
        counter = 0
        try:
            if self.recent_tracks:
                data = self.sendRequest('https://api.spotify.com/v1/me/player/recently-played?limit=1')
                for track in data['items']:
                    uri = track['track']['uri']
                if uri == self.recent_tracks[0][2]:
                    # if the first local stored song matches with the api's first stored song
                    # there was no change made and we can use the local list
                    return self.recent_tracks
                else:
                    tmp_list = []
                    for i in range(5):
                        offset = i * 5
                        data = self.sendRequest('https://api.spotify.com/v1/me/player/recently-played?limit=5&offset='+str(offset))
                        for track in data['items']:
                            uri = track['track']['uri']
                            if uri == self.recent_tracks[0][2]:
                                tmp_to_extend = self.recent_tracks
                                tmp_list.extend(tmp_to_extend)
                                self.recent_tracks = tmp_list
                                return self.recent_tracks
                            else:
                                artist = track['track']['artists'][0]['name']
                                song = track['track']['name']
                                uri = track['track']['uri']
                                cover_url = track['track']['album']['images'][0]['url']
                                tmp_list.append((artist, song, uri, cover_url))

            # no tracks are stored
            self.recent_tracks = []

            # load 50 of the last played tracks
            data = self.sendRequest('https://api.spotify.com/v1/me/player/recently-played?limit=50')
        
            for track in data['items']:
                artist = track['track']['artists'][0]['name']
                song = track['track']['name']
                uri = track['track']['uri']
                cover_url = track['track']['album']['images'][0]['url']
                self.recent_tracks.append((artist, song, uri, cover_url))
            if not data['items']:
                # break out of loop as all songs are collected
                return []
            return self.recent_tracks
        except KeyError:
            raise noauthException

    def getPlaylists(self):
        if self.playlists:
            data = self.sendRequest('https://api.spotify.com/v1/me/playlists?limit=1')
            if data['items'][0]['id'] == self.playlists[0][0]:
                # if the first local stored song matches with the api's first stored song
                # there was no change made and we can use the local list
                return self.playlists
        if not self.playlists:
            try:
                counter = 0
                # while there are saved songs left to collect
                while True:
                    offset = counter * 20
                    data = self.sendRequest('https://api.spotify.com/v1/me/playlists?limit=20&offset='+str(offset))

                    # check if auth token is missing
                    try:
                        if data['error']['message']:
                            raise noauthException
                    except KeyError:
                        pass

                    playlist_hidden = []
                    try:
                        with open('.playlist_hidden', 'r') as playlist_hidden_read:
                            for line in playlist_hidden_read:
                                playlist_hidden.append(line.strip())
                    except FileNotFoundError:
                        with open('.playlist_hidden', 'w+') as playlist_hidden_write:
                            playlist_hidden_write.write('')

                    for element in data['items']:
                        # only add playlist to returned list of playlist
                        # if it is not in the hidden list
                        if element['id'] not in playlist_hidden:
                            self.playlists.append((element['id'], element['name'], element['tracks']['total']))
                    if not data['items']:
                        # break out of loop as all songs are collected
                        break
                    counter = counter + 1
            except noauthException:
                raise noauthException
        return self.playlists

    def getAllPlaylists(self):
        allPlaylists = []
        try:
            counter = 0
            # while there are saved songs left to collect
            while True:
                offset = counter * 20
                data = self.sendRequest('https://api.spotify.com/v1/me/playlists?limit=20&offset='+str(offset))

                # check if auth token is missing
                try:
                    if data['error']['message']:
                        raise noauthException
                except KeyError:
                    pass

                for element in data['items']:
                    # only add playlist to returned list of playlist
                    # if it is not in the hidden list
                    allPlaylists.append((element['id'], element['name'], element['tracks']['total']))
                if not data['items']:
                    # break out of loop as all songs are collected
                    break
                counter = counter + 1
        except noauthException:
            raise noauthException
        return allPlaylists

    def getCoverImage(self, playlist_id):
        try:
            data = self.sendRequest('https://api.spotify.com/v1/playlists/'+playlist_id+'/images')
            if data:
                return data[0]['url']
            else:
                return ''
        except KeyError:
            raise noauthException
        
    def getPlaylistName(self, playlist_id):
        try:
            data = self.sendRequest('https://api.spotify.com/v1/playlists/'+playlist_id)
            if data:
                return data['name']
            else:
                return ''
        except KeyError:
            raise noauthException
        
    def getPlaylistNoSongs(self, playlist_id):
        try:
            data = self.sendRequest('https://api.spotify.com/v1/playlists/'+playlist_id)
            if data:
                return int(data['tracks']['total'])
            else:
                return 0
        except KeyError:
            raise noauthException

    def getPlaylistTracks(self, playlist_id, playlists_dynamic_loading = False):
        if playlist_id in self.playlist_tracks:
            if len(self.playlist_tracks[playlist_id]) == self.getPlaylistNoSongs(playlist_id):
                # if the first local stored song matches with the api's first stored song
                # there was no change made and we can use the local list
                return self.playlist_tracks[playlist_id]
        try:
            self.playlist_tracks[playlist_id] = []
            counter = 0
            # while there are saved songs left to collect
            offset = counter * 50
            data = self.sendRequest('https://api.spotify.com/v1/playlists/'+playlist_id+'/tracks?limit=50')
            
            # check if auth token is missing
            try:
                if data['error']['message']:
                    raise noauthException
            except KeyError:
                pass

            # only load first 50 songs if configured
            if playlists_dynamic_loading == True:
                for track in data['items']:
                    artist = track['track']['artists'][0]['name']
                    song = track['track']['name']
                    uri = track['track']['uri']
                    try:
                        cover_url = track['track']['album']['images'][0]['url']
                    except IndexError:
                        cover_url = 'covers/404.jpg'
                    self.playlist_tracks[playlist_id].append((artist, song, uri, cover_url))
            else:
                while True:
                    offset = counter * 50
                    data = self.sendRequest('https://api.spotify.com/v1/playlists/'+playlist_id+'/tracks?limit=50&offset='+str(offset))
                    
                    # check if auth token is missing
                    try:
                        if data['error']['message']:
                            raise noauthException
                    except KeyError:
                        pass

                    for track in data['items']:
                        artist = track['track']['artists'][0]['name']
                        song = track['track']['name']
                        uri = track['track']['uri']
                        try:
                            cover_url = track['track']['album']['images'][0]['url']
                        except IndexError:
                            cover_url = 'covers/404.jpg'
                        self.playlist_tracks[playlist_id].append((artist, song, uri, cover_url))
                    if not data['items']:
                        # break out of loop as all songs are collected
                        break
                    counter = counter + 1
                self.playlist_tracks[playlist_id].reverse()
            # store songs for peristence after restart before returning
            self.storeOfflineStorage()
            return self.playlist_tracks[playlist_id]
        except noauthException:
            raise noauthException

    def startPlayback(self):
        requests.put('https://api.spotify.com/v1/me/player/play', headers=self.header)

    def getCurrentlyPlaying(self):
        try:
            data = self.sendRequest('https://api.spotify.com/v1/me/player/currently-playing')
            artist = data['item']['artists'][0]['name']
            song = data['item']['name']
            if len(artist + ' - ' + song) < 30:
                current_song = artist + ' - ' + song
            else:
                current_song = song
            return current_song
        except:
            return 'Nothing playing right now'

    def getCurrentlyPlayingID(self):
        try:
            data = self.sendRequest('https://api.spotify.com/v1/me/player/currently-playing')
            song_id = data['item']['id']
            return song_id
        except:
            return 0

    def addNextSong(self, name):
        if name not in self.play_next:
            self.play_next.append(name)

    def getTrackLength(self):
        try:
            data = self.sendRequest('https://api.spotify.com/v1/me/player/currently-playing')
            progress = data['progress_ms']
            song_id = data['item']['id']
            data_track = self.sendRequest('https://api.spotify.com/v1/tracks/'+str(song_id))
            track_length = data_track['duration_ms']
            return track_length
        except:
            return '0'

    def getCurrentProgress(self):
        try:
            data = self.sendRequest('https://api.spotify.com/v1/me/player/currently-playing')
            progress = data['progress_ms']
            song_id = data['item']['id']
            data_track = self.sendRequest('https://api.spotify.com/v1/tracks/'+str(song_id))
            track_length = data_track['duration_ms']
            return str(100*float(progress)/float(track_length))
        except:
            return '0'

    def seekSongPosition(self, percentage):
        try:
            track_length = self.getTrackLength()
            seekPosition = int(int(track_length) * (percentage/100))
            requests.put('https://api.spotify.com/v1/me/player/seek?position_ms='+str(seekPosition), headers=self.header)
        except noauthException:
            raise noauthException

    def saveCurrentSong(self):
        try:
            data = self.sendRequest('https://api.spotify.com/v1/me/player/currently-playing')
            song_id = data['item']['id']
            self.sendRequest_PUT('https://api.spotify.com/v1/me/tracks/?ids='+str(song_id))
            return True
        except noauthException:
            raise noauthException
        except:
            return False

    def getRecommendations(self, seed_id):
        try:
            data = self.sendRequest('https://api.spotify.com/v1/recommendations?limit=20&seed_tracks='+str(seed_id))
            return data
        except noauthException:
            raise noauthException

    def getSongName(self, song_id):
        try:
            data = self.sendRequest('https://api.spotify.com/v1/tracks/'+str(song_id))
            song_name = data['name']
            return song_name
        except:
            return ''

    def getSongAndArtistName(self, song_id):
        try:
            data = self.sendRequest('https://api.spotify.com/v1/tracks/'+str(song_id))
            song_name = data['name']
            artist_name = data['artists'][0]['name']
            return artist_name + " - " + song_name
        except:
            return ''

    def getAvailableDevices(self):
        try:
            # request current devices of the user
            data = self.sendRequest('https://api.spotify.com/v1/me/player/devices')
            devices_from_api = []

            # check if auth token is missing
            try:
                if data['error']['message']:
                    raise noauthException
            except KeyError:
                pass
            
            for element in data['devices']:
                devices_from_api.append((element['name'], element['id']))

            # return list of devices
            return data['devices']
        except noauthException:
            raise noauthException

    def getAllDevices(self):
        devices = []
        try:
            # read devices from local file
            with open('.devices', 'r') as devices_read:
                for line in devices_read:
                    name, player_id = line.strip().rsplit(' ', 1)
                    devices.append((name, player_id))

            # request current devices of the user
            data = self.sendRequest('https://api.spotify.com/v1/me/player/devices')
            devices_from_api = []

            # check if auth token is missing
            try:
                if data['error']['message']:
                    raise noauthException
            except KeyError:
                pass
            
            for element in data['devices']:
                devices_from_api.append((element['name'], element['id']))

            # check if new devices are available
            # merge both lists
            devices = devices + list(set(devices_from_api) - set(devices))

            # store devices to local file
            with open('.devices', 'w+') as devices_write:
                for device in devices:
                    devices_write.write("%s %s\n" % (device))
            
            # return list of devices
            return devices
        except noauthException:
            raise noauthException

    def transferPlayback(self, device_id):
        # create list first because spotify web api want it this way
        device_ids = []
        device_ids.append(device_id)
        d = {'device_ids': device_ids}
        body_params = json.dumps(d)
        requests.put('https://api.spotify.com/v1/me/player', headers=self.header, data=body_params)

    def storeOfflineStorage(self):
        with open('.playlist_tracks.pkl', 'wb') as f:
            pickle.dump(self.playlist_tracks, f)

    def loadOfflineStorage(self):
        playlist_storage_file = Path(".playlist_tracks.pkl")
        file_size = playlist_storage_file.stat().st_size
        if playlist_storage_file.is_file() and file_size > 0:
            with open(playlist_storage_file, 'rb') as f:
                self.playlist_tracks = pickle.load(f)

    def buttonControlSaveSong(self):
        current_song_id = self.getCurrentlyPlayingID()
        if current_song_id != 0:
            data = self.sendRequest('https://api.spotify.com/v1/me/tracks/contains?ids='+current_song_id)
            return 'disabled' if data[0] else ''
        else:
            # no song is playing
            return 'disabled'