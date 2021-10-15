from flask import Flask, escape, request, redirect, render_template, url_for, send_from_directory, jsonify
from flask_socketio import SocketIO, send, emit
from spotifyapi import spotifyapi
import json
from noauthException import noauthException
import os
import urllib
import configparser

app = Flask(__name__)
app.config.from_pyfile('spotify.cfg', silent=True)
socketio = SocketIO(app)
config = configparser.ConfigParser()
configFilePath = './config.ini'
config.read(configFilePath)
spotifyapi = spotifyapi(config.get('Spotify', 'client_id'), config.get('Spotify', 'client_secret'), config.get('Network', 'redirect_uri'), config.get('Network', 'port'))
prev_url='/'

def coverImage(playlist_id):
    # make sure covers folder exists
    if not os.path.exists('./covers'):
        os.makedirs('./cover')
    # check if playlist_id has a stored cover image
    if not os.path.isfile('covers/'+str(playlist_id)+'.jpg'):
        cover_url = spotifyapi.getCoverImage(playlist_id)
        if cover_url:
            try:
                urllib.request.urlretrieve(cover_url, 'covers/'+str(playlist_id)+'.jpg')
            except urllib.error.HTTPError:
                return 'covers/404.jpg'
        else:
            return 'covers/404.jpg'
    return 'covers/'+str(playlist_id)+'.jpg'

@app.route('/covers/<path:filename>')
def covers(filename):
    return send_from_directory('covers/', filename)

@app.route('/')
def template():
    if spotifyapi.isAuthenticated():
        return redirect('/search', code=302)
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
    # redirect to prev_url 
    # which is used to go back to page where authentication was started
    return redirect(prev_url, code=302)

@socketio.on('updatesong')
def handle_my_custom_event(methods=['GET', 'POST']):
    current_song = spotifyapi.getCurrentlyPlaying()
    socketio.emit('updatesong_response', current_song)

@socketio.on('updateprogress')
def handle_update_progress(methods=['GET', 'POST']):
    current_progress = spotifyapi.getCurrentProgress()
    socketio.emit('updateprogress_response', current_progress)

@app.route('/search')
def search():
    global prev_url
    # set prev_url for redirect after authentication
    prev_url = '/search'
    # check if user is authenticated
    if not spotifyapi.isAuthenticated():
        return redirect(url_for('auth'))
    # add search bar
    html = '<form action="/search" method="get">'
    html += '<div class="input-group">'
    html += '<input id="1" type="text" autocomplete="off" class="keyboard form-control input" placeholder="Songname" name=\'q\'/>'
    html += '<input type="hidden" name="type" value="track"/>'
    html += '<button type="submit" class="btn btn-sp">Search</button>'
    html += '</div>'
    html += '</form>'
    html += '<hr id="hr" style="display: none;">'
    html += '<div id="keyboard" style="display: none; margin-left:auto; margin-right:auto;" class="simple-keyboard"></div>'
    html += '<hr>'
    # add search content
    html += '<div class="col-lg-13 mx-auto">'
    q = request.args.get('q')
    t = request.args.get('type')
    prev_url = '/search?q='+str(q)+'&type='+str(t)
    try:
        # error handling
        if q is None or t is None:
            return render_template('index.html', html=html, current=spotifyapi.getCurrentlyPlaying())
        result = spotifyapi.search(q, t)
        counter = 0
        for track in result:
            html += '<img width="40" height="40" src="'+track[3]+'"/>'
            html += '<p style="overflow-wrap: break-word; display:inline; padding-left: 10px;">'+track[0]+' - '+track[1]+'</p>'
            html += '<button id="'+str(counter)+'" class="btn btn-primary right" onclick="addSong(this.id, \''+track[2]+'\', \''+spotifyapi.getAccessToken()+'\')">Add to queue</button>'
            html += '<hr>'
            counter = counter + 1
        html += '<div>'
        return render_template('index.html', html=html, current=spotifyapi.getCurrentlyPlaying())
    except noauthException:
        return redirect(url_for('auth'))

@app.route('/tracks')
def tracks():
    global prev_url
    # return to previous URL if Tracks are disabled
    if not app.config.get("TRACKS"):
        return redirect(prev_url, code=302)
    prev_url = '/tracks'
    html = '<div class="col-lg-12 mx-auto">'
    counter = 0
    try:
        tracks = spotifyapi.getSavedTracks()
        html += '<h3 class="green">Here are your '+str(len(tracks))+' saved tracks</h3>'
        html += '<hr>'
        for track in tracks:
            html += '<div>'
            html += '<img width="40" height="40" src="'+track[3]+'"/>'
            html += '<p style="overflow-wrap: break-word; display:inline; padding-left: 10px;">'+track[0]+' - '+track[1]+'</p>'
            html += '<button id="'+str(counter)+'" class="btn btn-primary right" onclick="addSong(this.id, \''+track[2]+'\', \''+spotifyapi.getAccessToken()+'\')">Add to queue</button>'
            html += '</div>'
            html += '<hr>'
            counter = counter + 1
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
            html += '<a title="'+playlist[1]+'" href="/playlisthandler?playlist='+playlist[0]+'&name='+playlist[1]+'"><img width="300" height="300" src="'+cover_path+'"/></a>'
            html += '</div>'
        html += '</div>'
        return render_template('index.html', html=html, current=spotifyapi.getCurrentlyPlaying())
    except noauthException:
        return redirect(url_for('auth'))

@app.route('/hideplaylists')
def hideplaylists():
    global prev_url
    name = request.args.get('name')
    prev_url='/hideplaylists'
    html = '<h4>Hide playlists</h4>'
    html += '<hr>'
    try:
        # get list of playlists that are already hidden
        playlist_hidden = []
        with open('.playlist_hidden', 'r') as playlist_hidden_read:
            for line in playlist_hidden_read:
                playlist_hidden.append(line.strip())

        playlists = spotifyapi.getAllPlaylists()
        for playlist in playlists:
            cover_path = coverImage(playlist[0])
            html += '<img width="40" height="40" src="'+cover_path+'"/>'
            html += '<a style="padding-left: 10px;" title="'+playlist[1]+'" href="/playlisthandler?playlist='+playlist[0]+'&name='+playlist[1]+'">'+playlist[1]+'</a>'
            html += '<p>Number of tracks in this playlist: '+str(playlist[2])+'</p>'

            if playlist[0] in playlist_hidden:
                btn_type = 'btn-success'
                btn_msg = 'Unhide playlist'
            else:
                btn_type = 'btn-info'
                btn_msg = 'Hide playlist'

            html += '<form action="/playlisthandler_hide" method="POST">'
            html += '<button type="submit" class="btn '+str(btn_type)+' right">'+str(btn_msg)+'</button>'
            html += '<input type="hidden" name="playlist_id" value="'+playlist[0]+'">'
            html += '<input type="hidden" name="playlist_name" value="'+playlist[1]+'">'
            html += '<input type="hidden" name="playlist_total_tracks" value="'+str(playlist[2])+'">'
            html += '</form>'
            html += '<hr>'
        return render_template('index.html', html=html, current=spotifyapi.getCurrentlyPlaying())
    except noauthException:
        return redirect(url_for('auth'))

@app.route('/playlisthandler')
def playlisthandler():
    global prev_url
    playlist_id = request.args.get('playlist')
    name = request.args.get('name')
    prev_url='/playlisthandler?playlist='+str(playlist_id)
    html = ''
    try:
        tracks = spotifyapi.getPlaylistTracks(playlist_id)
        html += '<p style="overflow-wrap: break-word; display:inline;"><h4>'+str(name)+'</h4></p>'
        html += '<p>Number of tracks in this playlist: '+str(len(tracks))+'</p>'
        html += '<hr>'
        counter = 0
        for track in tracks:
            html += '<img width="40" height="40" src="'+track[3]+'"/>'
            html += '<p style="overflow-wrap: break-word; display:inline; padding-left: 10px;">'+track[0]+' - '+track[1]+'</p>'
            html += '<button id="'+str(counter)+'" class="btn btn-primary right" onclick="addSong(this.id, \''+track[2]+'\', \''+spotifyapi.getAccessToken()+'\')">Add to queue</button>'
            html += '<hr>'
            counter = counter + 1
        return render_template('index.html', html=html, current=spotifyapi.getCurrentlyPlaying())
    except noauthException:
        return redirect(url_for('auth'))

@app.route('/playlisthandler_hide', methods=['POST'])
def playlisthandler_hide():
    global prev_url, playlist_position
    playlist_id = request.form.get('playlist_id')
    playlist_name = request.form.get('playlist_name')
    playlist_total_tracks = request.form.get('playlist_total_tracks')
    try:
        # get the list of all hidden playlists
        playlist_hidden = []
        try:
            with open('.playlist_hidden', 'r') as playlist_hidden_read:
                for line in playlist_hidden_read:
                    playlist_hidden.append(line.strip())
        except FileNotFoundError:
            with open('.playlist_hidden', 'w+') as playlist_hidden_write:
                playlist_hidden_write.write('')

        # add playlist to the hidden playlists
        if playlist_id not in playlist_hidden:
            # add playlist_id to the hidden playlists
            playlist_hidden.append(playlist_id)
            # update local playlist storage
            spotifyapi.playlists = list(filter(lambda x: x[0] != playlist_id, spotifyapi.playlists))
        else:
            # remove playlist id from hidden playlists
            playlist_hidden.remove(playlist_id)
            # add it back to the list of playlists at the position where it was before
            spotifyapi.playlists.append((playlist_id, playlist_name, playlist_total_tracks))

        # store hidden playlists to local file
        with open('.playlist_hidden', 'w+') as playlist_hidden_write:
            for playlist in playlist_hidden:
                playlist_hidden_write.write("%s\n" % playlist)
        return redirect(prev_url, code=302)
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
            html += 'Transferred playback<br>'
        devices_list = spotifyapi.getAvailableDevices()
        html += '<h4>Available Devices</h4>'
        for device in devices_list:
            html += '<form action="/devices" method="POST">'
            html += '<button type="submit" class="btn btn-sp mid black">' + device['name'] + '</button>'
            html += '<input type="hidden" name="device_id" value="'+device['id']+'">'
            html += '<br>'
            html += 'Volume: '+str(device['volume_percent'])
            html += '<br>'
            html += 'Type: '+device['type']
            if device['is_active']:
                html += '<br><p class="green">Currently playing</p>'
            html += '</form>'
            html += '<br>'
        html += '<h4>All Devices</h4>'
        devices_list = spotifyapi.getAllDevices()
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
