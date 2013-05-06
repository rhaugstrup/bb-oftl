
$(function() {

  if (!$.support.boxModel) {
    $('body').html(
        "Your browser will not display this web page correctly. " +
        "Please update to the latest version of your browser. " +
        "This website is known to appear correctly with the latest " +
        "versions of Chrome, Safari, Firefox, and Internet Explorer.")
  }

  if (window.location.href.indexOf("#") != -1 &&
      window.location.href.indexOf("#ui") == -1) {
    $.fn.colorbox({
      current: "",
      href: function() { return window.location.href.replace("#", ""); },
      scrolling: false
    });
  }

  $('#tabs').tabs({
    select: function(event, ui) {
      /* clear panel html to prevent a user clicking a link from an earlier
       * loaded version of the tab before the tab has been reloaded */
      $(ui.panel).html("");

      /* without this, old dialog form fields are incorrectly re-used on coach's
       * page tab swap */
      $('.dialog').remove(); 
    },
    load:   function(event, ui) { close_working(); },
    cookie: { expires: 1 }
  });

  $("body").ajaxStart(function() {
    $(this).prepend("<div class='loading'>Loading...</div>");
  }).ajaxStop(function() {
    $(".loading").remove();
  }).ajaxError(function() {
    $(".loading").remove();
    close_working();
  });
});

function open_working() {
  $('<div />')
    .append("Please wait....")
    .attr("title", "Processing")
    .addClass("dialog working")
    .prependTo($("body"))
    .dialog({
      closeOnEscape: false,
      modal: true,
      open: function(event, ui) {
        $(".ui-dialog-titlebar-close", $(this).parent()).hide();
      }
    })
}

function close_working() {
  $('.working').dialog('close');
  $('.working').remove();
}

function analytics() {
  var _gaq = _gaq || [];
  _gaq.push(['_setAccount', 'UA-8829066-2']);
  _gaq.push(['_trackPageview']);
  (function() {
    var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;
    ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';
    var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);
  })();
}

if (typeof(String.prototype.trim) === "undefined") {
  String.prototype.trim = function() {
    return String(this).replace(/^\s+|\s+$/g, '');
  };
}
