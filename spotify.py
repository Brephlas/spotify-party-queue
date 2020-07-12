from flask import Flask, escape, request, redirect, render_template, url_for, send_from_directory, jsonify
from spotifyapi import spotifyapi
import json
from noauthException import noauthException
import os
import urllib
import configparser

app = Flask(__name__)
config = configparser.ConfigParser()
configFilePath = './config.ini'
config.read(configFilePath)
spotifyapi = spotifyapi(config.get('Spotify', 'client_id'), config.get('Spotify', 'client_secret'))
prev_url='/'

def coverImage(playlist_id):
    if not os.path.isfile('covers/'+str(playlist_id)+'.jpg'):
        cover_url = spotifyapi.getCoverImage(playlist_id)
        urllib.request.urlretrieve(cover_url, 'covers/'+str(playlist_id)+'.jpg')
    return 'covers/'+str(playlist_id)+'.jpg'

@app.route('/covers/<path:filename>')
def covers(filename):
    return send_from_directory('covers/', filename)

@app.route('/')
def template():
    if spotifyapi.isAuthenticated():
        return render_template('index.html', current=spotifyapi.getCurrentlyPlaying())
    else:
        return redirect(url_for('auth'))

@app.route('/auth')
def auth():
    return spotifyapi.authorize()

@app.route('/token')
def auth2():
    global prev_url
    code = request.args.get('code')
    spotifyapi.token(code)
    return redirect(prev_url, code=302)

@app.route('/search')
def search():
    global prev_url
    ## add search bar
    html = '<form action="/search" method="get">'
    html += '<div class="input-group">'
    html += '<input type="text" class="form-control" placeholder="Songname" name=\'q\'/>'
    html += '<input type="hidden" name="type" value="track"/>'
    html += '<button type="submit" class="btn btn-sp">Success</button>'
    html += '</div>'
    html += '</form>'
    html += '<hr>'
    # add search content
    html += '<div class="col-lg-11 mx-auto">'
    q = request.args.get('q')
    t = request.args.get('type')
    prev_url = '/search?q='+str(q)+'&type='+str(t)
    try:
        # error handling
        if q is None or t is None:
            return render_template('index.html', html=html, current=spotifyapi.getCurrentlyPlaying())
        result = spotifyapi.search(q, t)
        for track in result:
            html += track[0]+' - '+track[1]
            html += '<button class="btn btn-primary right" onclick="addSong(\''+track[2]+'\', \''+spotifyapi.getAccessToken()+'\')">Add to queue</button>'
            html += '<hr>'
        html += '<div>'
        return render_template('index.html', html=html, current=spotifyapi.getCurrentlyPlaying())
    except noauthException:
        # authenticate first if not logged in currently
        # /auth will redirect to prev_url
        return redirect(url_for('auth'))

@app.route('/tracks')
def tracks():
    global prev_url
    prev_url = '/tracks'
    html = '<div class="col-lg-11 mx-auto">'
    try:
        tracks = spotifyapi.getSavedTracks()
        for track in tracks:
            html += track[0]+' - '+track[1]
            html += '<button class="btn btn-primary right" onclick="addSong(\''+track[2]+'\', \''+spotifyapi.getAccessToken()+'\')">Add to queue</button>'
            html += '<hr>'
        html += '<div>'
        return render_template('index.html', html=html, current=spotifyapi.getCurrentlyPlaying())
    except noauthException:
        return redirect(url_for('auth'))

@app.route('/playlists')
def playlists():
    global prev_url
    prev_url = '/playlists'
    try:
        html = '<div class="grid-container">'
        playlists = spotifyapi.getPlaylists()
        for playlist in playlists:
            cover_path = coverImage(playlist[0])
            html += '<div class="grid-item">'
            html += '<p>'+playlist[1]+'</p>'
            html += '<a title="'+playlist[1]+'" href="/playlisthandler?playlist='+playlist[0]+'"><img width="300" height="300" src="'+cover_path+'"/></a>'
            #html += '<a title="'+playlist[1]+'" href="/playlisthandler?playlist='+playlist[0]+'"><img width="300" height="300" src="'+spotifyapi.getCoverImage(playlist[0])+'"/></a>'
            html += '</div>'
        html += '</div>'
        return render_template('index.html', html=html, current=spotifyapi.getCurrentlyPlaying())
    except noauthException:
        return redirect(url_for('auth'))

@app.route('/playlisthandler')
def playlisthandler():
    global prev_url
    playlist_id = request.args.get('playlist')
    prev_url='/playlisthandler?playlist='+str(playlist_id)
    try:
        tracks = spotifyapi.getPlaylistTracks(playlist_id)
        html = ''
        for track in tracks:
            html += track[0]+' - '+track[1]
            html += '<button class="btn btn-primary right" onclick="addSong(\''+track[2]+'\', \''+spotifyapi.getAccessToken()+'\')">Add to queue</button>'
            html += '<hr>'
        return render_template('index.html', html=html, current=spotifyapi.getCurrentlyPlaying())
    except noauthException:
        return redirect(url_for('auth'))

@app.route('/devices', methods=['GET', 'POST'])
def devices():
    global prev_url
    prev_url = '/devices'
    html = '<div class="mid">'
    try:
        if request.method == 'POST':
            device_id = request.form.get('device_id')
            spotifyapi.transferPlayback(device_id)
            html = 'Transfered playback'
        devices_list = spotifyapi.getDevices()
        for device in devices_list:
            html += '<form action="/devices" method="POST">'
            html += '<button type="submit" class="btn btn-sp mid black">' + device[0] + '</button>'
            html += '<input type="hidden" name="device_id" value="'+device[1]+'">'
            html += '</form>'
            html += '<br>'
        html += '</div>'
        return render_template('index.html', html=html, current=spotifyapi.getCurrentlyPlaying())
    except noauthException:
            return redirect(url_for('auth'))

if __name__ == "__main__":
    app.run(host='0.0.0.0')
