/*
    Extract Management 2.0
    Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

(function () {
  String.prototype.format = function () {
    var i = 0,
      args = arguments;
    return this.replace(/{}/g, function () {
      return typeof args[i] != "undefined" ? args[i++] : "";
    });
  };

  var d = document,
    taskId = d.querySelector("h1.em-title[task_id]").getAttribute("task_id");

  function taskHello() {
    var q = new XMLHttpRequest();
    q.open("get", "/task/{}/hello".format(taskId), true);
    q.send();
    q.onload = function () {
      var data = JSON.parse(q.responseText);
      for (var key in data) {
        var els = Array.prototype.slice.call(
          d.querySelectorAll(".hello_{}".format(key))
        );

        for (var x = 0; x < els.length; x++) {
          els[x].innerHTML = data[key];

          if (key === "status") {
            els[x].classList.remove("em-error");
            els[x].classList.remove("em-success");
            els[x].classList.remove("em-running");
            switch (data[key].split(" ")[0]) {
              case "Running":
                els[x].classList.add("em-running");
                break;
              case "Completed":
                els[x].classList.add("em-success");
                break;
              case "Errored":
                els[x].classList.add("em-error");
                break;
            }
          }
        }
      }
    };
  }

  setInterval(taskHello, 3000);
})();
