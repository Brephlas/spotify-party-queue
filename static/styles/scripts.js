function addSong(element_id, id, access_token, song_name, img_path) {
  // check if there is an active playback
  if (
    (
      document.documentElement.textContent || document.documentElement.innerText
    ).indexOf('Nothing playing right now') > -1
  ) {
    iziToast.warning({title: 'There is no playback currently',position: 'topCenter'});
    return;
  }

  // add song to queue
  var button = document.getElementById(element_id);
  button.disabled = true;
  button.textContent = "Added!";
  var Http = new XMLHttpRequest();
  var url='https://api.spotify.com/v1/me/player/queue?uri='+id;
  Http.open("POST", url);
  Http.setRequestHeader('Accept', 'application/json');
  Http.setRequestHeader('Content-Type', 'application/json');
  Http.setRequestHeader('Authorization', 'Bearer '+access_token);
  Http.send();
  // show notification
  iziToast.show({
        theme: 'dark',
        icon: 'icon-contacts',
        title: decodeURI(song_name.replaceAll('+', ' ')),
	message: ' added to queue',
        displayMode: 2,
        position: 'topCenter',
        transitionIn: 'flipInX',
        transitionOut: 'flipOutX',
	image: img_path,
        progressBarColor: 'rgb(0, 255, 184)',
        imageWidth: 70,
        layout: 2,
        iconColor: 'rgb(0, 255, 184)'
    });

  // Update next_songs list
  Http = new XMLHttpRequest();
  url=location.protocol + '//' + document.domain + ':' + location.port + '/addNextSong';
  Http.open("POST", url);
  Http.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
  Http.send('name='+encodeURIComponent(song_name));
}

var url = window.location.href.split("/"); //replace string with location.href
var navLinks = document.getElementsByTagName("nav")[0].getElementsByTagName("a");
// you also could use something other than the <nav> element
var i=0;
var currentPage = url[url.length - 1]
for(i;i<navLinks.length;i++){
  var lb = navLinks[i].href.split("/");
  if(lb[lb.length-1] == currentPage) {
    navLinks[i].classList.add("current");

  }
}

// get/set state of the sidebar
function toggleSidebar() {
  try {
    var state = localStorage.getItem('sidebar');
    if (state == "closed") {
      localStorage.setItem('sidebar', 'open');
    } else {
      localStorage.setItem('sidebar', 'closed');
    }
  } catch {
    localStorage.setItem('sidebar', 'open');
  }
}

// set the sidebar on page load
if (localStorage.getItem('sidebar') == "closed") {
  document.body.classList.add("sidebar-icon-only");
} else {
  document.body.classList.remove("sidebar-icon-only");
}

if(SOCKET == true) {
  // Update current played song
  var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

  const interval = setInterval(function() {
    socket.emit( 'updatesong', {} )
    socket.emit( 'updateprogress', {} )
  }, 10000); // 10 seconds

  socket.on( 'connect', function() {
    socket.emit( 'updatesong', {} )
  } )
  socket.on( 'updatesong_response', function( msg ) {
    $('#current').text(msg)
    $('#current_mainpage').text(msg)
    document.title = "Spotifyqueue - "+msg;
  })

  const interval_progress = setInterval(function() {
    socket.emit( 'updateprogress', {} )
  }, 5000); // 5 seconds

  socket.on( 'connect', function() {
    socket.emit( 'updateprogress', {} )
  } )
  socket.on( 'updateprogress_response', function( msg ) {
    $('#progress').attr('aria-valuenow', msg).css('width', msg+'%');
  })
}
