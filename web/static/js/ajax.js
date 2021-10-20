var ajaxContent = function () {
  function load(el, dest) {
    if (typeof dest == "undefined") {
      dest = el;
    }

    var q = new XMLHttpRequest();
    q.open("get", el.getAttribute("data-src"), true);
    q.send();

    q.onload = function () {
      el.innerHTML = this.responseText;

      // find and execute any javascript

      var js = Array.prototype.slice.call(
        el.querySelectorAll('script:not([type="application/json"])')
      );
      for (var x = 0; x < js.length; x++) {
        var q = document.createElement("script");
        q.innerHTML = js[x].innerHTML;
        q.type = "text/javascript";
        q.setAttribute("async", "true");
        el.appendChild(q);
        js[x].parentElement.removeChild(js[x]);
      }

    // find and load any scroll
    var scroll = Array.prototype.slice.call(
      el.querySelectorAll('[ss-container]')
    );
    for (var x = 0; x < scroll.length; x++) {
      document.dispatchEvent(
        new CustomEvent("ss-load", {
          cancelable: true,
          detail: {
            el: scroll[x],
          },
        })
      );
    }
    };
  }

  var stuff = document.getElementsByClassName("em-ajaxContent");
  for (var x = 0; x < stuff.length; x++) {
    if (stuff[x].hasAttribute("data-src")) {
      load(stuff[x]);
    }
  }

};

ajaxContent();

(function () {
  document.addEventListener("click", function (e) {
    if (e.target.closest("input[action]")) {
      // submit ajax request to the specified action.
      var q = new XMLHttpRequest(),
        target = e.target.closest("input[action]"),
        action = target.getAttribute("action");
      q.open("get", action, true);
      q.send();

      // change from enable to disable and vise versa
      if (action.indexOf("enable") !== -1) {
        target.setAttribute("action", action.replace("enable", "disable"));
      } else {
        target.setAttribute("action", action.replace("disable", "enable"));
      }
    }
  });
})();
