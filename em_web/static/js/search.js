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

window.addEventListener("load", function () {
  var q = new XMLHttpRequest();

  var search_block = document.querySelector(".block-search");
  var results_div = search_block.querySelector(".search-results");

  q.open("get", "/search", true);
  q.send();

  q.onload = function () {
    var search = JSON.parse(q.responseText);

    var search_input = document.getElementById("nav-search");
    search_input.classList.remove("disabled");
    search_input.addEventListener("input", function (e) {
      if (this.value == "") {
        search_block.classList.remove("search-open");
        results_div.innerHTML = "";
        return;
      }

      var regex = new RegExp(this.value.replace(" ", ".* .*"), "gmi");

      var output = "";
      var count = 0;

      for (var key in search) {
        for (var subkey in search[key]) {
          // if we have a match
          var s_match = search[key][subkey].match(regex);
          if (s_match) {
            output +=
              '<div class="search-result">' +
              key +
              ': <a href="/' +
              key.replace("user", "project/user") +
              "/" +
              subkey +
              '">' +
              search[key][subkey].replace(regex, function (m) {
                return "<strong>" + m + "</strong>";
              }) +
              "</a></div>";
            count++;
          }
        }
      }

      if (count == 0) {
        output += "<p>Nothing found.</p>";
      }

      results_div.innerHTML = output;
      search_block.classList.add("search-open");
    });
  };
});
