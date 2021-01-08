function addSong(element_id, id, access_token) {
  var button = document.getElementById(element_id);
  button.disabled = true;
  const Http = new XMLHttpRequest();
  const url='https://api.spotify.com/v1/me/player/queue?uri='+id;
  Http.open("POST", url);
  Http.setRequestHeader('Accept', 'application/json');
  Http.setRequestHeader('Content-Type', 'application/json');
  Http.setRequestHeader('Authorization', 'Bearer '+access_token);
  Http.send();
  $.notify("Added song to queue", "info");
}

function sendMatrix(song) {
  const Http = new XMLHttpRequest();
  const url='http://192.168.178.155';
  Http.open("POST", url);
  Http.setRequestHeader('Accept', 'application/x-www-form-urlencoded');
  Http.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
  Http.send('lauftext='+song+'&wartenMs=50&helligkeit=3');
}

function toggleKeyboard() {
  var x = document.getElementById("keyboard");
  if (x.style.display === "none") {
    x.style.display = "";
  } else {
    x.style.display = "none";
  }
}

window.addEventListener('click', function(e){
  try {
    if (document.getElementsByClassName('keyboard')[0].contains(e.target)){
      // Clicked in box
      document.getElementById("keyboard").style.display = "";
      return
    }
  } catch (e) {
    ;
  }
  try {
    if (document.getElementById('keyboard').contains(e.target)){
      // Clicked in box
      //console.log('keyboard click')
      return
    }
    if (document.getElementsByClassName('keyb')[0].contains(e.target)){
      // Clicked in box
      //console.log('keyboard click')
      return
    }
  } catch (e) {
    ;
  }
  document.getElementById("keyboard").style.display = "none";
});

function addInputClass(clicked_id) {
  var elements = document.getElementsByClassName('keyboard');
  for (var i = 0; i < elements.length; i++) {
    elements[i].classList.remove('input');
  }
  keyboard.clearInput();
  keyboard.setInput(document.getElementById(clicked_id).value);
  var element = document.getElementById(clicked_id);
  element.classList.add("input");
  document.getElementById("keyboard").style.display = "";
}

try {
  let Keyboard = window.SimpleKeyboard.default;

  let keyboard = new Keyboard({
    onChange: input => onChange(input),
    onKeyPress: button => onKeyPress(button),
    layout: {
      'default': [
        '` 1 2 3 4 5 6 7 8 9 0 - = {bksp}',
        '{tab} q w e r t z u i o p [ ] \\',
        '{lock} a s d f g h j k l ; \' {enter}',
        '{shift} y x c v b n m , . / {shift}',
        '.com @ {space}'
      ],
      'shift': [
        '~ ! @ # $ % ^ & * ( ) _ + {bksp}',
        '{tab} Q W E R T Z U I O P { } |',
        '{lock} A S D F G H J K L : " {enter}',
        '{shift} Y X C V B N M < > ? {shift}',
        '.com @ {space}'
      ]
    }
  });

  /**
   * Update simple-keyboard when input is changed directly
   */
  document.querySelector(".input").addEventListener("input", event => {
    keyboard.setInput(event.target.value);
  });
} catch (KEYBOARD_DOM_ERROR) {
  ;
}

//console.log(keyboard);

function onChange(input) {
  document.querySelector(".input").value = input;
  //console.log("Input changed", input);
}

function onKeyPress(button) {
  //console.log("Button pressed", button);

  /**
   * If you want to handle the shift and caps lock buttons
   */
  if (button === "{shift}" || button === "{lock}") handleShift();
}

function handleShift() {
  let currentLayout = keyboard.options.layoutName;
  let shiftToggle = currentLayout === "default" ? "shift" : "default";

  keyboard.setOptions({
    layoutName: shiftToggle
  });
}

// Update current played song
var socket = io.connect('http://' + document.domain + ':' + location.port);

const interval = setInterval(function() {
  socket.emit( 'updatesong', {} )
  socket.emit( 'updateprogress', {} )
}, 10000); // 10 seconds

socket.on( 'connect', function() {
  socket.emit( 'updatesong', {} )
} )
socket.on( 'updatesong_response', function( msg ) {
  $('#current').text(msg)
  sendMatrix(msg)
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
