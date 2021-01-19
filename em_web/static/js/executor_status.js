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
  var my_timeout = 1000;
  function executorStatus() {
    var q = new XMLHttpRequest();
    q.open("get", "/executor/status", true);
    q.send();

    q.onload = function () {
      var jobs = JSON.parse(this.responseText),
        box = document.getElementsByClassName("em-status")[0];

      if (Object.keys(jobs).length < 1) {
        box.style.removeProperty("height");
        my_timeout = Math.min(my_timeout + 3000, 10000);
      } else {
        var job_text = "";
        for (var key in jobs) {
          job_text += jobs[key] + "&nbsp;";
        }

        box.style.height = "64px";

        box.querySelector(".em-statusMessage").innerHTML = job_text;
        my_timeout = 1000;
      }
    };

    setTimeout(executorStatus, my_timeout);
  }

  executorStatus();
})();
