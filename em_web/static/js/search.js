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

  var searchBlock = document.querySelector(".block-search");
  if (!searchBlock) {
    return !1;
  }
  var resultsDiv = searchBlock.querySelector(".search-results");

  q.open("get", "/search", true);
  q.send();

  q.onload = function () {
    var search = JSON.parse(q.responseText);

    var searchInput = document.getElementById("nav-search");
    searchInput.classList.remove("disabled");
    searchInput.addEventListener("input", function (e) {
      if (this.value === "") {
        searchBlock.classList.remove("search-open");
        resultsDiv.innerHTML = "";
        return;
      }

      var regex = new RegExp(this.value.replace(" ", ".* .*"), "gmi");

      var output = "";
      var count = 0;

      for (var key in search) {
        for (var subkey in search[key]) {
          // if we have a match
          var sMatch = search[key][subkey].match(regex);
          if (sMatch) {
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

      if (count === 0) {
        output += "<p>Nothing found.</p>";
      }

      resultsDiv.innerHTML = output;
      searchBlock.classList.add("search-open");
    });
  };
});
