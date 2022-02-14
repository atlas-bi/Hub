document.addEventListener('click', function (e) {
  if (e.target.closest('.notification .delete')) {
    var el = e.target.closest('.notification');
    el.parentNode.removeChild(el);
  }
});

var debounce = function debounce(func, wait, immediate) {
  var timeout;
  return function () {
    var context = this,
      args = arguments;

    var later = function later() {
      timeout = null;
      if (!immediate) func.apply(context, args);
    };

    var callNow = immediate && !timeout;
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    if (callNow) func.apply(context, args);
  };
};

// function to check if a user is active/inactive
// if a user is inactive we want to stop ajax requests
// until the user is back.

(function () {
  window.ajaxOn = true;

  var sessionTimerId,
    startPageTimer = function () {
      var sessionTimeout = 2 * 6000;
      sessionTimerId = window.setTimeout(doInactive, sessionTimeout);
    },
    resetPageTimer = function () {
      debounce(
        (function () {
          window.clearTimeout(sessionTimerId);
          startPageTimer();
          window.ajaxOn = true;
        })(),
        500,
      );
    },
    doInactive = function () {
      window.ajaxOn = false;
    },
    setupPageTimer = function () {
      document.addEventListener('mousemove', resetPageTimer, false);
      document.addEventListener('mousedown', resetPageTimer, false);
      document.addEventListener('keypress', resetPageTimer, false);
      document.addEventListener('touchmove', resetPageTimer, false);
      document.addEventListener(
        'scroll',
        resetPageTimer,
        {
          passive: true,
        },
        false,
      );
      startPageTimer();
    };

  // if document is already loaded
  if (document.readyState == 'complete') {
    setupPageTimer();
  }
  // if document has not loaded yet
  window.addEventListener(
    'load',
    function () {
      setupPageTimer();
    },
    false,
  );
})();
