import requests
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.oauth2 import SpotifyClientCredentials
import spotipy.util as util
from flask import redirect
from noauthException import noauthException

class spotifyapi:
    def __init__(self, client_id, client_secret, redirect_uri, port):
        self.redirect_uri = redirect_uri
        self.port = port
        self.client_id = client_id
        self.client_secret = client_secret
        self.authenticated = False
        self.header = {'Accept' : 'application/json', 'Content-Type' : 'application/json'}
        self.playlists = []

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
        return self.access_token

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

    def authorize(self):
        permissions = ['user-modify-playback-state', 'playlist-read-private', 'user-read-playback-state', 'user-library-read']
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
            data = self.sendRequest('https://api.spotify.com/v1/search?q='+str(q)+'&type='+str(t)+'&limit=10')
            tracks = []
            for track in data['tracks']['items']:
                artist = track['artists'][0]['name']
                song = track['name']
                uri = track['uri']
                tracks.append((artist, song, uri))
            return tracks
        except (noauthException, KeyError):
            raise noauthException

    def getSavedTracks(self):
        try:
            data = self.sendRequest('https://api.spotify.com/v1/me/tracks?limit=50')
            tracks = []
            for track in data['items']:
                artist = track['track']['artists'][0]['name']
                song = track['track']['name']
                uri = track['track']['uri']
                tracks.append((artist, song, uri))
            return tracks
        except noauthException:
            raise noauthException

    def getPlaylists(self):
        if not self.playlists:
            try:
                data = self.sendRequest('https://api.spotify.com/v1/me/playlists')
                for element in data['items']:
                        self.playlists.append((element['id'], element['name']))
            except noauthException:
                raise noauthException
        return self.playlists

    def getCoverImage(self, playlist_id):
        data = self.sendRequest('https://api.spotify.com/v1/playlists/'+playlist_id+'/images')
        return data[0]['url']

    def getPlaylistTracks(self, playlist_id):
        try:
            data = self.sendRequest('https://api.spotify.com/v1/playlists/'+playlist_id+'/tracks')
            tracks = []
            for element in data['items']:
                artist = element['track']['album']['artists'][0]['name']
                song = element['track']['name']
                uri = element['track']['uri']
                tracks.append((artist, song, uri))
            return tracks
        except noauthException:
            raise noauthException

    def startPlayback(self):
        requests.put('https://api.spotify.com/v1/me/player/play', headers=self.header)

    def getCurrentlyPlaying(self):
        data = self.sendRequest('https://api.spotify.com/v1/me/player/currently-playing')
        try:
            artist = data['item']['artists'][0]['name']
            song = data['item']['name']
            return artist + ' - ' + song
        except:
            return 'Nothing playing right now'

    def getDevices(self):
        try:
            data = self.sendRequest('https://api.spotify.com/v1/me/player/devices')
            devices = []
            for element in data['devices']:
                devices.append((element['name'], element['id']))
            return devices
        except noauthException:
            raise noauthException

    def transferPlayback(self, device_id):
        # create llist first because spotify web api want it this way
        device_ids = []
        device_ids.append(device_id)
        d = {'device_ids': device_ids}
        body_params = json.dumps(d)
        requests.put('https://api.spotify.com/v1/me/player', headers=self.header, data=body_params)