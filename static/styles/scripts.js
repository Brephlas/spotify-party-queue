async function fadeOutAnimation(button) {
  var btn = button.parentElement;
  console.log(btn);
  const finish_animation = anime({
    targets: btn,
    duration: 500,
    delay: 50,
    opacity: [1, 0],
    easing: 'easeOutExpo',
    translateX: [0, 40],
    opacity: 0
  }).finished;
  await Promise.all([finish_animation]);
  // remove row after animation
  btn.nextElementSibling.remove();
  btn.remove();
}

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
  var Http = new XMLHttpRequest();
  var url='https://api.spotify.com/v1/me/player/queue?uri='+id;
  Http.open("POST", url);
  Http.setRequestHeader('Accept', 'application/json');
  Http.setRequestHeader('Content-Type', 'application/json');
  Http.setRequestHeader('Authorization', 'Bearer '+access_token);
  //Http.send();

  if(REMOVE_ELEMENTS == true) {
    // play fade out animation when elements are removed
    fadeOutAnimation(button);
  } else {
    // rotate animation when button clicked and elements are not removed
    anime({
      targets: button,
      rotateX: [{ value: "1turn", duration: 100 }]
    });

	  button.disabled = true;
	  button.textContent = "Added!";
  }

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

// search function for playlists
function search() {
  var input, filter, ul, li, a, i, txtValue;
  input = document.getElementById("search");
  filter = input.value.toUpperCase();
  li = document.getElementsByClassName("playlistname");
  for (i = 0; i < li.length; i++) {
      txtValue = li[i].textContent || li[i].innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
          li[i].parentNode.parentNode.parentNode.style.display = "";
          li[i].classList.add("search_listelement");
      } else {
          li[i].parentNode.parentNode.parentNode.style.display = "none";
          li[i].classList.remove("search_listelement");
      }
  }
}

function showpageload() {
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

let lastY = 0;
// Scroll to the bottom of the page
// Trigger fetching of additional songs
window.addEventListener('scroll', function(e) {
  // check if end was nearly reached (and function not already ran)
  let triggerY = window.screen.height/5;
  if (Math.round(window.innerHeight + window.scrollY) >= document.body.scrollHeight - triggerY && (Math.abs(lastY - window.scrollY) > triggerY || lastY == 0) ) {
    // store last scroll value
    lastY = window.scrollY;

    // return for now in case of playlists
    if(window.location.pathname.includes("playlisthandler") && !PLAYLISTS_DYNAMIC_LOADING) return;
    
    // return if not in any track view
    if(!window.location.pathname.includes("tracks") && !window.location.pathname.includes("playlisthandler")) return;

    // show loading notification
    iziToast.show({
      theme: 'dark',
      icon: 'icon-contacts',
      title: 'Loading',
      displayMode: 2,
      position: 'topCenter',
      transitionIn: 'fadeIn',
      transitionOut: 'fadeOut',
      timeout: 500
    });
    // set mouse cursor to loading
    document.body.style.cursor='wait';

    // determine offset
    var replace_el = document.getElementById("more");
    let offset = parseInt(replace_el.previousSibling.previousSibling.childNodes[0][0].id) + 1;

    var url = "";
    if(window.location.pathname.includes("tracks")) {
      url="https://api.spotify.com/v1/me/tracks?limit=50&offset=";
    } else {
      var playlist_id = new URLSearchParams(window.location.search).get('playlist');
      url="https://api.spotify.com/v1/playlists/"+playlist_id+"/tracks?limit=50&offset=";
    }

    var html = "";
    // pull saved songs
    var Http = new XMLHttpRequest();
    Http.responseType = 'json';
    url_temp = url + offset;
    Http.open("GET", url_temp);
    Http.setRequestHeader('Accept', 'application/json');
    Http.setRequestHeader('Content-Type', 'application/json');
    Http.setRequestHeader('Authorization', 'Bearer '+access_token);

    // get result of each request and fill variables
    let counter = offset;
    Http.onreadystatechange= function(e) {
      var result = Http.response;
      if(!result) return;
      var items = result['items'];
      if(items.length) {
        items.forEach((song) => {
          var name = song['track']['artists'][0]['name'] + ' - ' + song['track']['name'];
          var uri = song['track']['uri'];
          var cover_url = song['track']['album']['images'][0]['url'];

          // generate HTML elements for each song
          html += '<div>'
          if (RECOMMENDATIONS)
              html += '<form action="/recommendations" method="get">'
          html += '<div>'
          html += '<img class="fading-newelems'+offset+'" style="opacity:.0; width="40" height="40" src="'+cover_url+'" ondblclick="addSong('+counter+', \''+uri+'\', \''+access_token+'\', \''+encodeURI(name.replaceAll("'", "%27"))+'\', \''+cover_url+'\')" />'
          html += '<p class="fading-newelems'+offset+'" style="opacity:.0; overflow-wrap: break-word; display:inline; padding-left: 10px;">'+name+'</p>'
          html += '<div class="btn-group right" role="group">'
          html += '<button id="'+counter+'" class="btn btn-success right fading-buttons'+offset+'" style="opacity:.0; onclick="addSong(this.id, \''+uri+'\', \''+access_token+'\', \''+encodeURI(name.replaceAll("'", "%27"))+'\', \''+cover_url+'\')">Add to queue</button>'
          if (RECOMMENDATIONS) {
            html += '<input type="hidden" name="song_id" value="'+uri.split(':').at(-1)+'"/>'
            html += '<button style="opacity:.0;" class="btn btn-info right fading-buttons'+offset+'">Recommendations</button>'
          }
          html += '</div>'
          html += '</div>'
          if (RECOMMENDATIONS)
              html += '</form>'
          html += '</div>'
          html += '<hr style="overflow: hidden; position: relative;">'
          counter = parseInt(counter) + 1;
        });

        html += "<div id=\"more\" style=\"text-align:center\">More</div>";
        document.getElementById("more").outerHTML = html;
        if(window.location.pathname.includes("tracks")) {
          document.getElementById("songs_no").innerHTML = "Here are your "+counter+" saved tracks";
        } else {
          document.getElementById("songs_no").innerHTML = "Number of tracks in this playlist: "+counter;
        }

        // animate new elements
        var elements = document.querySelectorAll('.fading-newelems'+offset);
        anime({
          targets: elements,
          duration: (el, i) => 20*i + 500,
          delay: (el, i) => (200+30*i),
          opacity: [0, 1],
          easing: 'easeInOutQuint',
          translateX: [40, 0],
          opacity: 1
        });
        var elements2 = document.querySelectorAll('.fading-buttons'+offset);
        anime({
          targets: elements2,
          duration: (el, i) => 20*i + 500,
          delay: (el, i) => (200+30*i),
          opacity: [0, 1],
          easing: 'easeOutExpo',
          opacity: 1
        });
      } else {
        iziToast.destroy();
        html += "<div id=\"more\" style=\"text-align:center\">End reached</div>";
        document.getElementById("more").outerHTML = html;
      }
      document.body.style.cursor='';
    };
    Http.send();
  }
});

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
  var socket = io.connect(location.protocol + '//' + location.hostname + ':' + location.port);

  // click event handler for the progress bar
  // progress bar click listener
  document.getElementById('progress').addEventListener('click', function (e) {
      var maxWidth = document.getElementById("progress-container").offsetWidth;
      var currentProgress = e.offsetX;
      var percentageProgress = Math.round((currentProgress/maxWidth) * 100);

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
  setInterval(function() {
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
      if(!icon.src.includes('/static/assets/img/menuicon.png')) {
        icon.src = '/static/assets/img/menuicon.png';
        // update cache
        reloadImg(icon.src);
      }
    } else {
	    // green icon because music is playing
      if(!icon.src.includes('/static/assets/img/menuicon_green.png')) {
        icon.src = '/static/assets/img/menuicon_green.png';
        // update cache
        reloadImg(icon.src);
      }
    }

    $('#current').text(msg)
    $('#current_mainpage').text(msg)
    document.title = "Spotifyqueue - "+msg;
  })

  // update progress bar
  setInterval(function() {
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

window.onload = function fading() {
	var elements = document.querySelectorAll('.fading');
	anime({
		targets: elements,
		duration: (el, i) => 10*i + 500,
//delay: (el, i) => 100+30*i,
		delay: anime.stagger(30),
		opacity: [0, 1],
		easing: 'easeOutExpo',
		translateX: [40, 0],
		opacity: 1
	});
	var elements = document.querySelectorAll('.fading-slow');
	anime({
		targets: elements,
		duration: (el, i) => 10*i + 500,
		delay: (el, i) => (100+30*i)/(30+i),
		opacity: [0, 1],
		easing: 'easeOutExpo',
		translateX: [40, 0],
		opacity: 1
	});
}

// place cursor in search field for playlists
if(window.location.pathname.includes("playlists")) {
	var search_input = document.querySelector('#search');
  search_input.focus();
}

// action when pressed enter
$('#search').on('keyup', eKeyUp);
function eKeyUp(e){
  // when enter was pressed inside input
  if(e.which == 13) {    
    // get all results
	  var playlists = document.querySelectorAll(".search_listelement");
    // and if one element is left, click it
    if(playlists.length == 1) {
      playlists[0].nextElementSibling.click();
    }
  }
}

previous_click_opened = null;
// detect click outside navbar
$(document).on("click", function (event)
{
  if ($(event.target).closest('.element').length == 0)
  {
    // if click is outside of navbar close it
    let navbar = document.getElementsByClassName("sidebar active");
    let sidebar_opened = $(event.target).hasClass('sidebar-toggler');
    // check if sidebar should be closed
    if (!$(event.target).is("nav") && navbar.length == 1 && !sidebar_opened && previous_click_opened) {
      // close nav bar
      navbar[0].classList.remove("active");
      previous_click_opened = false;
    }
    // check if the last click opened the sidebar
    if (sidebar_opened) {
      previous_click_opened = true;
    }
  }
});

// drag listener
var divOverlay = document.getElementById ("#content");
var dragged = false
var oldX = 0;
window.addEventListener('mousedown', function (e) { oldX = e.pageX; dragged = false });
document.addEventListener('mousemove', function () { dragged = true });
window.addEventListener('mouseup', function(e) {
  if (Math.abs((e.pageX - oldX)) > 100 ) {
    if (dragged == true && e.pageX < oldX) {
      history.forward();
    } else if (dragged == true && e.pageX > oldX) {
      history.back();
    }
  }   
});
