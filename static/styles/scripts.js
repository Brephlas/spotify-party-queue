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

  // different timeout settings for smaller screens
  if(window.screen.width <= 980) {
	  timeout_target = 1500;
  } else {
	  timeout_target = 3000;
  }

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
        iconColor: 'rgb(0, 255, 184)',
	timeout: timeout_target
    });
}

function loading() {
	// set mouse cursor to loading
	document.body.style.cursor='wait';

	// larger screen
	// set icon upper left to loading gif
	$("#logo_img").hide();
	$("#logo_img_mini").hide();
	div_to_display_loading = "logo";
	document.getElementById(div_to_display_loading).style.backgroundRepeat = 'no-repeat';
	document.getElementById(div_to_display_loading).style.backgroundSize = 'cover';
	// check if there is an active playback
	if (
	  (
	    document.documentElement.textContent || document.documentElement.innerText
	  ).indexOf('Nothing playing right now') > -1
	) {
	  document.getElementById(div_to_display_loading).style.backgroundImage = 'url(/static/assets/img/loading_white.gif)';
	} else {
	  document.getElementById(div_to_display_loading).style.backgroundImage = 'url(/static/assets/img/loading.gif)';
	}

	// small screens
	$("#logo-mini").hide();
	div_to_display_loading = "logo-mini-div";
	document.getElementById(div_to_display_loading).style.backgroundRepeat = 'no-repeat';
	document.getElementById(div_to_display_loading).style.backgroundSize = 'cover';
	// check if there is an active playback
	if (
	  (
	    document.documentElement.textContent || document.documentElement.innerText
	  ).indexOf('Nothing playing right now') > -1
	) {
	  document.getElementById(div_to_display_loading).style.backgroundImage = 'url(/static/assets/img/loading_white.gif)';
	} else {
	  document.getElementById(div_to_display_loading).style.backgroundImage = 'url(/static/assets/img/loading.gif)';
	}
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
  console.log(table_elements.length);
}

// set the sidebar on page load
if (localStorage.getItem('sidebar') == "closed") {
  document.body.classList.add("sidebar-icon-only");
} else {
  document.body.classList.remove("sidebar-icon-only");
}

async function reloadImg(url) {
  await fetch(url, { cache: 'reload', mode: 'no-cors' })
  document.body.querySelectorAll('img[alt="logo"]')
    .forEach(img => img.src = url)
}

if(SOCKET == true) {
  var socket = io.connect(location.protocol + '//' + document.domain + ':' + location.port);

  // click event handler for the progress bar
  // progress bar click listener
  document.getElementById('progress').addEventListener('click', function (e) {
      var maxWidth = document.getElementById("progress-container").offsetWidth;
      var currentProgress = e.offsetX;
      var percentageProgress = Math.round((currentProgress/maxWidth) * 100);

      console.log( percentageProgress );
      socket.emit('changeProgress', {'progress': percentageProgress})
  });

  // progress bar click listener (mobile)
  document.getElementById('progress-mobile').addEventListener('click', function (e) {
      var maxWidth = document.getElementById("progress-mobile-container").offsetWidth;
      var currentProgress = e.offsetX;
      var percentageProgress = Math.round((currentProgress/maxWidth) * 100);

      socket.emit('changeProgress', {'progress': percentageProgress})
  });


  // Update current played song

  const interval = setInterval(function() {
    socket.emit( 'updatesong', {} )
    socket.emit( 'updateprogress', {} )
  }, 10000); // 10 seconds

  socket.on( 'connect', function() {
    socket.emit( 'updatesong', {} )
  } )
  socket.on( 'updatesong_response', function( msg ) {

    // update icon as indicator for playback
    var icon = document.querySelector('img[alt="logo"]');
    if(msg == 'Nothing playing right now') {
	    // white icon because no playback
	    icon.src = '/static/assets/img/menuicon.png';
    } else {
	    // green icon because music is playing
	    icon.src = '/static/assets/img/menuicon_green.png';
    }
    // update cache
    reloadImg(icon.src);

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
    $('#progress-mobile').attr('aria-valuenow', msg).css('width', msg+'%');
  })
}
