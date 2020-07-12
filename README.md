# spotify-party-queue
I was tired of saying "please make sure to not click on a song" when i was giving away my phone so someone else could add his favorite songs to the playback queue and then still fucking up the playback, so i decided to write a web interface (e.g. for the use on a tablet) for spotify that only allows adding songs to the queue.

# Install
1. Install fask and ConfigParser: `pip3 install flask ConfigParser`
1. Create a spotify application in their [developer dashboard](https://developer.spotify.com/dashboard/applications)
2. Clone this repo
`git clone https://github.com/Brephlas/spotify-party-queue.git`
3. Create file `config.ini` with your spotify client id and secret:
```
[Spotify]
client_id = CLIENT_ID
client_secret = CLIENT_SECRET
```
4. Run `python3 spotify.py`
5. Open `http://<SERVERIP>:5000` in your browser
6. Authorize the app to access your spotify data


# Config
## Change port
Add your port to the line *app.run* function in `spotify.py`:
```
if __name__ == '__main__':
      app.run(host='0.0.0.0', port=80)
```
