from flask import Flask, escape, request, redirect, render_template, url_for, send_from_directory, jsonify, session
from flask_socketio import SocketIO, send, emit
from flask_session import Session
from spotifyapi import spotifyapi
import json
from noauthException import noauthException
import os
import urllib
import configparser
import redis
import urllib.parse
from copy import copy

app = Flask(__name__)
app.config.from_pyfile('spotify.cfg', silent=True)
socketio = SocketIO(app)
socketio.init_app(app, cors_allowed_origins="*")
config = configparser.ConfigParser()
configFilePath = './config.ini'
config.read(configFilePath)
spotifyapi = spotifyapi(config.get('Spotify', 'client_id'), config.get('Spotify', 'client_secret'), config.get('Network', 'redirect_uri'), config.get('Network', 'port'))
prev_url='/'

style_start = '<div class="row"><div class="col-12 grid-margin stretch-card"><div class="card"><div class="card-body" style="height: 100%;">'
style_end = '</div></div></div></div>'

def coverImage(playlist_id):
    # make sure covers folder exists
    if not os.path.exists('./covers'):
        os.makedirs('./covers')
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

@app.errorhandler(404)
def page_not_found(e):
    return redirect('/', code=302)

@app.route('/covers/<path:filename>')
def covers(filename):
    file_exists = os.path.isfile('covers/'+str(filename))
    if file_exists:
        return send_from_directory('covers/', filename)
    else:
        return send_from_directory('covers/404.jpg')

@app.route('/get-token')
def getToken():
    return spotifyapi.getAccessToken()

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

@socketio.on('changeProgress')
def seekSongPosition(json):
    song_position = json['progress']
    if song_position and song_position > 0 and song_position < 100:
        spotifyapi.seekSongPosition(json['progress'])

@app.route('/addNextSong', methods=['POST'])
def addNextSong():
    name = request.form.get('name')
    spotifyapi.addNextSong(name)
    return 'Ok'
    
@app.route('/')
def root():
    if not spotifyapi.isAuthenticated():
        return redirect(url_for('auth'))
    else:
        return redirect('/search', code=302)

@app.route('/search')
def search():
    global prev_url
    # set prev_url for redirect after authentication
    prev_url = '/search'
    # check if user is authenticated
    if not spotifyapi.isAuthenticated():
        return redirect(url_for('auth'))

    # get GET parameter
    q = request.args.get('q')
    t = request.args.get('type')

    # initialize html
    html = '<div class="input-group d-lg-none" style="display: grid;">'
    html += '<form action="/search" method="get">'
    html += '<div class="btn-group right" style="width:100%;" role="group">'
    html += '<input id="songname-mobile" type="text" autocomplete="off" class="form-control input" placeholder="Songname" name=\'q\'/>'
    html += '<input type="hidden" name="type" value="track"/>'
    html += '<button id="search-2" type="submit" class="btn btn-success" style="margin-left: 10px;">Search</button>'
    html += '</form>'
    html += '</div>'
    html += '</div>'
    html += '<hr id="hr" class="d-lg-none">'

    if not q:
        return render_template('index.html', style_start=style_start, style_end=style_end, html=html, current=spotifyapi.getCurrentlyPlaying(), access_token=spotifyapi.getAccessToken())
    else:
        prev_url = '/?q='+str(q)+'&type='+str(t)
        html += '<h3>Search results for '+str(q)+'</h3>'
        html += '<hr>'
        try:
            # error handling
            if q is None or t is None:
                return render_template('index.html', html=html, current=spotifyapi.getCurrentlyPlaying(), access_token=spotifyapi.getAccessToken())
            result = spotifyapi.search(q, t)
            counter = 0
            for track in result:
                html += '<div>'
                if app.config["RECOMMENDATIONS"] == True:
                    html += '<form action="/recommendations" method="get">'
                html += '<div style="opacity:.0;" class="fading">'
                artist_track = urllib.parse.quote_plus((track[0]+' - '+track[1]).encode('utf-8'))
                html += '<img width="40" height="40" src="'+track[3]+'" ondblclick="addSong('+str(counter)+', \''+track[2]+'\', \''+spotifyapi.getAccessToken()+'\', \''+artist_track+'\', \''+track[3]+'\')" />'
                html += '<p style="overflow-wrap: break-word; display:inline; padding-left: 10px;">'+track[0]+' - '+track[1]+'</p>'
                html += '<div class="btn-group right" role="group">'
                html += '<button type="button" id="'+str(counter)+'" class="btn btn-success right" onclick="addSong(this.id, \''+track[2]+'\', \''+spotifyapi.getAccessToken()+'\', \''+artist_track+'\', \''+track[3]+'\')">Add to queue</button>'
                if app.config["RECOMMENDATIONS"] == True:
                    html += '<input type="hidden" name="song_id" value="'+str(track[2].split(':')[-1])+'"/>'
                    html += '<button class="btn btn-info right">Recommendations</button>'
                html += '</div>'
                html += '</div>'
                if app.config["RECOMMENDATIONS"] == True:
                    html += '</form>'
                html += '</div>'
                html += '<hr style="overflow: hidden; position: relative;">'
                counter = counter + 1
            html += '</div>'
        except noauthException:
            return redirect(url_for('auth'))
        finally:
            return render_template('index.html', style_start=style_start, style_end=style_end, html=html, current=spotifyapi.getCurrentlyPlaying(), access_token=spotifyapi.getAccessToken())

@app.route('/tracks')
def tracks():
    global prev_url
    # return to previous URL if Tracks are disabled
    if app.config["TRACKS"] == False:
        return redirect(prev_url, code=302)
    prev_url = '/tracks'
    html = '<div class="col-lg-12 mx-auto">'
    counter = 0
    try:
        tracks = spotifyapi.getSavedTracks()
        html += '<h3 id="songs_no" class="green card-title">Here are your '+str(len(tracks))+' saved tracks</h3>'
        html += '<hr>'
        html += '<div class="col-lg-13 mx-auto">'
        for track in tracks:
            html += '<div>'
            if app.config["RECOMMENDATIONS"] == True:
                html += '<form action="/recommendations" method="get">'
            html += '<div>'
            artist_track = urllib.parse.quote_plus((track[0]+' - '+track[1]).encode('utf-8'))
            html += '<img width="40" height="40" src="'+track[3]+'" ondblclick="addSong('+str(counter)+', \''+track[2]+'\', \''+spotifyapi.getAccessToken()+'\', \''+artist_track+'\', \''+track[3]+'\')" />'
            html += '<p style="overflow-wrap: break-word; display:inline; padding-left: 10px;">'+track[0]+' - '+track[1]+'</p>'
            html += '<div class="btn-group right" role="group">'
            html += '<button type="button" id="'+str(counter)+'" class="btn btn-success right" onclick="addSong(this.id, \''+track[2]+'\', \''+spotifyapi.getAccessToken()+'\', \''+artist_track+'\', \''+track[3]+'\')">Add to queue</button>'
            if app.config["RECOMMENDATIONS"] == True:
                html += '<input type="hidden" name="song_id" value="'+str(track[2].split(':')[-1])+'"/>'
                html += '<button class="btn btn-info right">Recommendations</button>'
            html += '</div>'
            html += '</div>'
            if app.config["RECOMMENDATIONS"] == True:
                html += '</form>'
            html += '</div>'
            html += '<hr style="overflow: hidden; position: relative;">'
            counter = counter + 1
        html += '<div id="more" style="text-align:center">More</div>'
        html += '</div>'
        return render_template('index.html', style_start=style_start, style_end=style_end, html=html, current=spotifyapi.getCurrentlyPlaying(), access_token=spotifyapi.getAccessToken())
    except noauthException:
        return redirect(url_for('auth'))

@app.route('/previousTracks')
def previousTracks():
    global prev_url
    # return to previous URL if Tracks are disabled
    if app.config["TRACKS"] == False:
        return redirect(prev_url, code=302)
    prev_url = '/previousTracks'
    html = '<div class="col-lg-12 mx-auto">'
    counter = 0
    try:
        tracks = spotifyapi.getRecentlyPlayed()
        html += '<h3 id="songs_no" class="green card-title">Here are your '+str(len(tracks))+' recently played tracks</h3>'
        html += '<hr>'
        html += '<div class="col-lg-13 mx-auto">'
        for track in tracks:
            html += '<div>'
            if app.config["RECOMMENDATIONS"] == True:
                html += '<form action="/recommendations" method="get">'
            html += '<div>'
            artist_track = urllib.parse.quote_plus((track[0]+' - '+track[1]).encode('utf-8'))
            html += '<img width="40" height="40" src="'+track[3]+'" ondblclick="addSong('+str(counter)+', \''+track[2]+'\', \''+spotifyapi.getAccessToken()+'\', \''+artist_track+'\', \''+track[3]+'\')" />'
            html += '<p style="overflow-wrap: break-word; display:inline; padding-left: 10px;">'+track[0]+' - '+track[1]+'</p>'
            html += '<div class="btn-group right" role="group">'
            html += '<button type="button" id="'+str(counter)+'" class="btn btn-success right" onclick="addSong(this.id, \''+track[2]+'\', \''+spotifyapi.getAccessToken()+'\', \''+artist_track+'\', \''+track[3]+'\')">Add to queue</button>'
            if app.config["RECOMMENDATIONS"] == True:
                html += '<input type="hidden" name="song_id" value="'+str(track[2].split(':')[-1])+'"/>'
                html += '<button class="btn btn-info right">Recommendations</button>'
            html += '</div>'
            html += '</div>'
            if app.config["RECOMMENDATIONS"] == True:
                html += '</form>'
            html += '</div>'
            html += '<hr style="overflow: hidden; position: relative;">'
            counter = counter + 1
        html += '<div id="more" style="text-align:center">More</div>'
        html += '</div>'
        return render_template('index.html', style_start=style_start, style_end=style_end, html=html, current=spotifyapi.getCurrentlyPlaying(), access_token=spotifyapi.getAccessToken())
    except noauthException:
        return redirect(url_for('auth'))

@app.route('/playlists')
def playlists():
    global prev_url
    # return to previous URL if playlists are disabled
    if app.config["PLAYLISTS"] == False:
        return redirect(prev_url, code=302)
    prev_url = '/playlists'
    try:
        html = ''
        # create copy of playlists to avoid reversing the returned global playlists
        playlists = copy(spotifyapi.getPlaylists())
        playlists.reverse()
        html += '<input type="text" id="search" class="border form-control input" onkeyup="search()" placeholder="Search for playlist.." title="Type in a playlist name">'
        html += '<div class="row">'
        for playlist in playlists:
            cover_path = coverImage(playlist[0])
            html += '<div class="col-sm-2 grid-margin">'
            html += '<div class="card">'
            html += '<div class="card-body">'
            html += '<p class="playlistname">'+str(playlist[1])+'</p>'
            html += '<a title="'+playlist[1]+'" href="/playlisthandler?playlist='+str(playlist[0])+'" onclick="loading(\''+spotifyapi.getAccessToken()+'\')"><img class="responsive" src="'+cover_path+'"/></a>'
            html += '</div>'
            html += '</div>'
            html += '</div>'
        html += '</div>'
        return render_template('index.html', html=html, current=spotifyapi.getCurrentlyPlaying(), access_token=spotifyapi.getAccessToken())
    except noauthException:
        return redirect(url_for('auth'))

@app.route('/hideplaylists')
def hideplaylists():
    global prev_url
    # return to previous URL if playlists are disabled
    if app.config["PLAYLISTS"] == False:
        return redirect(prev_url, code=302)
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
            html += '<div style="overflow: auto;">'
            html += '<form action="/playlisthandler_hide" method="POST" style="display: flex; align-items: center;">'
            html += '<img class="left" width="50" height="50" src="'+cover_path+'" style="margin-right: 10px;"/>'

            html += '<div style="display: flex; flex-direction: column; flex-grow: 1;">'  # Flex-grow hinzufügen
            html += '<a style="overflow-wrap: break-word; display: inline;" title="'+playlist[1]+'" href="/playlisthandler?playlist='+playlist[0]+'&name='+playlist[1]+'">'+playlist[1]+'</a>'
            html += '<p style="overflow-wrap: break-word; display: inline;">Number of tracks in this playlist: '+str(playlist[2])+'</p>'
            html += '</div>'

            html += '<div style="margin-left: auto;">'  # Margin-left: auto für rechtsbündige Ausrichtung
            if playlist[0] in playlist_hidden:
                btn_type = 'btn-success'
                btn_msg = 'Unhide playlist'
            else:
                btn_type = 'btn-info'
                btn_msg = 'Hide playlist'

            html += '<input type="hidden" name="playlist_id" value="'+playlist[0]+'">'
            html += '<input type="hidden" name="playlist_name" value="'+playlist[1]+'">'
            html += '<input type="hidden" name="playlist_total_tracks" value="'+str(playlist[2])+'">'
            html += '<div class="btn-group right" role="group">'
            html += '<button type="submit" class="btn '+str(btn_type)+' right">'+str(btn_msg)+'</button>'
            html += '</div>'
            html += '</div>'
            html += '</form>'
            html += '</div>'
            html += '<hr style="overflow: hidden; position: relative;">'
        return render_template('index.html', style_start=style_start, style_end=style_end, html=html, current=spotifyapi.getCurrentlyPlaying(), access_token=spotifyapi.getAccessToken())
    except noauthException:
        return redirect(url_for('auth'))

@app.route('/playlisthandler')
def playlisthandler():
    global prev_url
    playlist_id = request.args.get('playlist')
    prev_url='/playlisthandler?playlist='+str(playlist_id)
    # return to previous URL if playlists are disabled
    if app.config["PLAYLISTS"] == False:
        return redirect(prev_url, code=302)
    try:
        name = spotifyapi.getPlaylistName(playlist_id)
        html = ''
        tracks = spotifyapi.getPlaylistTracks(playlist_id, app.config["PLAYLISTS_DYNAMIC_LOADING"])
        html += '<p style="overflow-wrap: break-word; display:inline;"><h4>'+str(name)+'</h4></p>'
        html += '<p id="songs_no">Number of tracks in this playlist: '+str(len(tracks))+'</p>'
        html += '<hr>'
        html += '<div class="col-lg-13 mx-auto">'
        counter = 0
        for track in tracks:
            html += '<div>'
            if app.config["RECOMMENDATIONS"] == True:
                html += '<form action="/recommendations" method="get">'
            html += '<div style="opacity:.0;" class="fading">'
            artist_track = urllib.parse.quote_plus((track[0]+' - '+track[1]).encode('utf-8'))
            html += '<img width="40" height="40" src="'+track[3]+'" ondblclick="addSong('+str(counter)+', \''+track[2]+'\', \''+spotifyapi.getAccessToken()+'\', \''+artist_track+'\', \''+track[3]+'\')" />'
            html += '<p style="overflow-wrap: break-word; display:inline; padding-left: 10px;">'+track[0]+' - '+track[1]+'</p>'
            html += '<div class="btn-group right" role="group">'
            html += '<button type="button" id="'+str(counter)+'" class="btn btn-success" onclick="addSong(this.id, \''+track[2]+'\', \''+spotifyapi.getAccessToken()+'\', \''+artist_track+'\', \''+track[3]+'\')">Add to queue</button>'
            if app.config["RECOMMENDATIONS"] == True:
                html += '<input type="hidden" name="song_id" value="'+str(track[2].split(':')[-1])+'"/>'
                html += '<button class="btn btn-info">Recommendations</button>'
            html += '</div>'
            html += '</div>'
            if app.config["RECOMMENDATIONS"] == True:
                html += '</form>'
            html += '</div>'
            html += '<hr style="overflow: hidden; position: relative;">'
            counter = counter + 1
        
        # show button for more elements when dynamic loading is active
        if app.config["PLAYLISTS_DYNAMIC_LOADING"] == True:
            html += '<div id="more" style="text-align:center">More</div>'

        html += '</div>'
        return render_template('index.html', style_start=style_start, style_end=style_end, html=html, current=spotifyapi.getCurrentlyPlaying(), access_token=spotifyapi.getAccessToken())
    except noauthException:
        return redirect(url_for('auth'))

@app.route('/playlisthandler_hide', methods=['POST'])
def playlisthandler_hide():
    global prev_url, playlist_position
    # return to previous URL if playlists are disabled
    if app.config["PLAYLISTS"] == False:
        return redirect(prev_url, code=302)
    prev_url = '/hideplaylists'
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

@app.route('/recommendations', methods=['GET'])
def recommendations():
    global prev_url
    if app.config["RECOMMENDATIONS"] == False:
        return redirect(prev_url, code=302)
    try:
        song_id = request.args.get('song_id')
        song_name = spotifyapi.getSongAndArtistName(song_id)
        # error handling, redirect back if no song_id provided
        if not song_id:
            return redirect(prev_url, code=302)
        prev_url = '/recommendations?song_id='+str(song_id)
        songs = spotifyapi.getRecommendations(song_id)
        track = songs['tracks'][0]
        html = ''
        html += '<p style="overflow-wrap: break-word; display:inline;"><h4>Recommendations for '+str(song_name)+'</h4></p>'
        html += '<hr>'
        html += '<div class="col-lg-13 mx-auto">'
        counter = 0
        for track in songs['tracks']:
            # track vars
            track_name = track['name']
            artist_name = track['artists'][0]['name']
            track_uri = track['uri']
            track_img = track['album']['images'][0]['url']
            artist_track = urllib.parse.quote_plus((artist_name + " - " + track_name).encode('utf-8'))
            # build HTML
            html += '<div style="opacity:.0;" class="fading">'
            html += '<img width="40" height="40" src="'+track_img+'" ondblclick="addSong('+str(counter)+', \''+track_uri+'\', \''+spotifyapi.getAccessToken()+'\', \''+artist_track+'\', \''+track_img+'\')" />'
            html += '<p style="overflow-wrap: break-word; display:inline; padding-left: 10px;">'+artist_name+' - '+track_name+'</p>'
            html += '<button id="'+str(counter)+'" class="btn btn-success right" onclick="addSong(this.id, \''+track_uri+'\', \''+spotifyapi.getAccessToken()+'\', \''+artist_track+'\', \''+track_img+'\')">Add to queue</button>'
            html += '</div>'
            html += '<hr>'
            counter = counter + 1
        html += '</div>'
        return render_template('index.html', style_start=style_start, style_end=style_end, html=html, current=spotifyapi.getCurrentlyPlaying(), access_token=spotifyapi.getAccessToken())
    except noauthException:
        return redirect(url_for('auth'))

@app.route('/config', methods=['GET', 'POST'])
def config():
    global prev_url
    try:
        # handle change request
        if request.method == 'POST':
            config_entry = request.form.get('config_entry').upper()
            reverse = True if app.config.get(str(config_entry)) == False else False
            app.config[str(config_entry)] = reverse

        num_lines = sum(1 for _ in open('spotify.cfg'))

        # Detect config entries of application
        trigger_config = False
        parse_cfgs = []
        for cfg in app.config:
                parse_cfgs.append(cfg)

        html = ''
        # create an entry for each relevant config
        for cfg in parse_cfgs[-num_lines:]:
            status = app.config.get(cfg)
            if status == True:
                html += '<h3 style="color:#1DB954">'+str(cfg)+'</h3>'
            else:
                html += '<h3>'+str(cfg)+'</h3>'
            html += '<form action="/config" method="POST">'
            html += '<button type="submit" class="btn btn-info">Toggle - Currently: '+str(status)+'</button>'
            html += '<input type="hidden" name="config_entry" value="'+cfg+'">'
            html += '</form>'
        # Also add a link to /hideplaylists
        html += '<h3><a href="/hideplaylists">Hideplaylists</a></h3'
        return render_template('index.html', style_start=style_start, style_end=style_end, html=html, current=spotifyapi.getCurrentlyPlaying(), access_token=spotifyapi.getAccessToken())
    except noauthException:
        return redirect(url_for('auth'))
