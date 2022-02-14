(function () {
  // from https://www.w3schools.com/howto/howto_js_alert.asp
  var close = document.getElementsByClassName('flashes-close');
  var i;

  function hide(el) {
    var div = el.parentElement;
    div.style.opacity = '0';

    setTimeout(function () {
      div.style.display = 'none';
    }, 200);
  }

  for (i = 0; i < close.length; i++) {
    close[i].addEventListener('click', hide.bind(this, close[i]), false);
  }
})();
