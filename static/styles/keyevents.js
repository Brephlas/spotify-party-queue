// catch keyboard events to write them to the search field
$('body').on('keyup', eKeyUp);
$('#songname').on('keyup', eKeyUpINPUT);

function eKeyUp(e){
  if(e.which == 13) {
    // submit search
    $('#search-1').click();
  } else if(e.which == 8) {
    // backspace, so remove last character from search
    $('#songname').attr('value', $('#songname').val().slice(0,-1))
  } else if((e.which >= 48 && e.which <= 90) || e.which == 32) {
    // for alphanumeric inputs and space add this to the search query
    $('#songname').attr('value', $('#songname').val() + event.key);
  }
  if(e.which == 40) {
    // arrow down
    e.preventDefault();
    var counter = 0;
    var selected_exists = false;
    $('.col-lg-13.mx-auto').children('div').children('p').each(function(i) {
        counter = counter + 1;
        if(~$(this).text().indexOf(">")) { selected_exists = true; return false; }
    });
    var counter2 = 1;
    $('.col-lg-13.mx-auto').children('div').children('p').each(function(i) {
        if(!selected_exists) {
           $(this).text('> '+$(this).text());
           return false;
        }
        if(counter2 - 1 == counter) {
           $(this).text('> '+$(this).text());
	   window.scrollTo(0, $(this).offset().top-300);
        } else if(counter2 == counter) {
           $(this).text($(this).text().substring(2));
        }
        counter2 = counter2 + 1;
    });
  } else if(e.which == 38) {
    // arrow up
    e.preventDefault();
    var counter = 0;
    var selected_exists = false;
    $('.col-lg-13.mx-auto').children('div').children('p').each(function(i) {
        counter = counter + 1;
        if(~$(this).text().indexOf(">")) { selected_exists = true; return false; }
    });
    var counter2 = 1;
    $('.col-lg-13.mx-auto').children('div').children('p').each(function(i) {
        if(!selected_exists) {
           $(this).text('> '+$(this).text());
           return false;
        }
        if(counter2 + 1 == counter) {
           $(this).text('> '+$(this).text());
	  window.scrollTo(0, $(this).offset().top-250);
        } else if(counter2 == counter) {
           $(this).text($(this).text().substring(2));
        }
        counter2 = counter2 + 1;
    });
  } else if(e.which == 17) {
    if(~window.location.href.indexOf("playlists")) {
            // use ctrl to click a playlist in case playlists are listed
            var selected_exists = false;
            $('.row').children('div').each(function(i) {
                if(~$(this).children().children().children('p').text().indexOf(">")) {
                        selected_exists = true;
                        // click the link of the playlist
                        $(this).children().children().children('p').next('a')[0].click();
                        return false;
                }
            });
    } else {
            // ctrl click (add current element to queue)
            var selected_exists = false;
            $('.col-lg-13.mx-auto').children('div').children('p').each(function(i) {
                if(~$(this).text().indexOf(">")) {
                        if(!$(this).next().is(":disabled")) {
                                selected_exists = true;
                                // click "Add to queue" button
                                $(this).next().click();
                        return false;
                        } else {
                                console.log("Song was already added");
                        }
                }
            });
    }
    if(!selected_exists) {
        console.log("Nothing selected");
    }
  } else if(e.which == 37) {
          // arrow down
          var counter = 0;
          var selected_exists = false;
          $('.row').children('div').each(function(i) {
                counter = counter + 1;
                if(~$(this).children().children().children('p').text().indexOf(">")) { selected_exists = true; return false; }
          });
          var counter2 = 1;
          $('.row').children('div').each(function(i) {
                if(!selected_exists) {
                   $(this).children().children().children('p').text('> '+$(this).children().children().children('p').text());
                   return false;
                }
                if(counter2 + 1 == counter) {
                   $(this).children().children().children('p').text('> '+$(this).children().children().children('p').text());
                } else if(counter2 == counter) {
                   $(this).children().children().children('p').text($(this).children().children().children('p').text().substring(2));
                }
                counter2 = counter2 + 1;
          });
  } else if(e.which == 39) {
          // arrow down
          var counter = 0;
          var selected_exists = false;
          $('.row').children('div').each(function(i) {
                counter = counter + 1;
                if(~$(this).children().children().children('p').text().indexOf(">")) { selected_exists = true; return false; }
          });
          var counter2 = 1;
          $('.row').children('div').each(function(i) {
                if(!selected_exists) {
                   $(this).children().children().children('p').text('> '+$(this).children().children().children('p').text());
                   return false;
                }
                if(counter2 - 1 == counter) {
                   $(this).children().children().children('p').text('> '+$(this).children().children().children('p').text());
                } else if(counter2 == counter) {
                   $(this).children().children().children('p').text($(this).children().children().children('p').text().substring(2));
                }
                counter2 = counter2 + 1;
          });
  }
}

function eKeyUpINPUT(e){
    e.stopPropagation();
}
