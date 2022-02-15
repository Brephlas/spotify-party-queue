function addSong(element_id, id, access_token, song_name) {
  var button = document.getElementById(element_id);
  button.disabled = true;
  var Http = new XMLHttpRequest();
  var url='https://api.spotify.com/v1/me/player/queue?uri='+id;
  Http.open("POST", url);
  Http.setRequestHeader('Accept', 'application/json');
  Http.setRequestHeader('Content-Type', 'application/json');
  Http.setRequestHeader('Authorization', 'Bearer '+access_token);
  Http.send();
  // show notification
  $.notify(song_name + " added to queue", {globalPosition: 'bottom center', className:"success"});
  // Update next_songs list
  Http = new XMLHttpRequest();
  url=location.protocol + '//' + document.domain + ':' + location.port + '/addNextSong';
  Http.open("POST", url);
  Http.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
  //console.log(song_name)
  Http.send('name='+encodeURIComponent(song_name));
}

/*
# Decide if light theme is wanted. If so, build one :)
window.onload = function () {
  const toggle = document.getElementById("topnav_right_mode_toggle");
  const theme = document.getElementById("stylesheet_toggle");
  const selected = localStorage.getItem("css");
  theme.href = selected;
  var d = new Date();

  if (localStorage.getItem("css") == null) {
    // change theme based on time
    if (d.getHours() >= 16 || d.getHours() < 8) {
      theme.href = "/static/styles/styles.css";
    } else {
      theme.href = "/static/styles/styles_light.css";
    }
    localStorage.setItem("css", theme.href);
  }

  toggle.addEventListener("click", function () {
    if (theme.getAttribute("href") == "/static/styles/styles_light.css") {
        theme.href = "/static/styles/styles.css";
    } else {
        theme.href = "/static/styles/styles_light.css";
    }
    localStorage.setItem("css", theme.href);
  });
}
*/

var url = window.location.href.split("/"); //replace string with location.href
var navLinks = document.getElementsByTagName("nav")[0].getElementsByTagName("a");
//naturally you could use something other than the <nav> element
var i=0;
var currentPage = url[url.length - 1]
for(i;i<navLinks.length;i++){
  var lb = navLinks[i].href.split("/");
  if(lb[lb.length-1] == currentPage) {
    navLinks[i].classList.add("current");

  }
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