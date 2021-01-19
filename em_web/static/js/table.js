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
  var tables = document.getElementsByClassName("em-ajaxTable");

  for (var x = 0; x < tables.length; x++) {
    if (tables[x].hasAttribute("data-src")) table(tables[x]);
  }

  function table(el, dest, reload) {
    if (typeof dest == "undefined") dest = el;
    if (typeof reload == "undefined") reload = false;
    q = new XMLHttpRequest();
    q.open(
      "get",
      el.getAttribute("data-src") + "?v=" + new Date().getTime(),
      true
    );
    q.send();

    q.onload = function () {
      try {
        loadTable(JSON.parse(this.responseText), dest, reload);
        dest.style.removeProperty("opacity");
      } catch (e) {
        dest.innerHTML =
          "<span class='em-error'>Failed to load. " + e + "</span>";
        console.log(this.responseText);
      }
      if (el.closest(".clps-o"))
        el.closest(".clps-o").dispatchEvent(
          new Event("change", {
            bubbles: true,
          })
        );
    };
  }

  function loadTable(arr, el, enableReload) {
    var out = "",
      i,
      x,
      head = [],
      total = arr.length,
      key,
      page = 1,
      sort = "",
      q,
      empty_msg = "No data to show.";

    // get total rows
    for (x = 0; x < arr.length; x++) {
      if (arr[x].total || arr[x].total == 0) {
        total = arr[x].total;
        arr.splice(x, 1);
        break;
      }
    }
    for (x = 0; x < arr.length; x++) {
      if (arr[x].page || arr[x].page == 0) {
        page = arr[x].page + 1;
        arr.splice(x, 1);
        break;
      }
    } // sort
    for (x = 0; x < arr.length; x++) {
      if (arr[x].sort) {
        sort = arr[x].sort;
        arr.splice(x, 1);
        break;
      }
    } // get header
    for (x = 0; x < arr.length; x++) {
      if (arr[x].head) {
        head = JSON.parse(arr[x].head.replace(/'/g, '"'));
        arr.splice(x, 1);
        break;
      } // get head from first set row of json.
      head = Object.keys(arr[x]);
    }

    for (x = 0; x < arr.length; x++) {
      if (arr[x].empty_msg) {
        empty_msg = arr[x].empty_msg;
        arr.splice(x, 1);
        break;
      }
    }

    var r = [],
      j = -1; // table tools

    r[++j] =
      '<div class="em-tableTools"><div><button class="em-tableReload" title="refresh"><svg viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg"><path d="M500.33 0h-47.41a12 12 0 0 0-12 12.57l4 82.76A247.42 247.42 0 0 0 256 8C119.34 8 7.9 119.53 8 256.19 8.1 393.07 119.1 504 256 504a247.1 247.1 0 0 0 166.18-63.91 12 12 0 0 0 .48-17.43l-34-34a12 12 0 0 0-16.38-.55A176 176 0 1 1 402.1 157.8l-101.53-4.87a12 12 0 0 0-12.57 12v47.41a12 12 0 0 0 12 12h200.33a12 12 0 0 0 12-12V12a12 12 0 0 0-12-12z"/></svg></button><button class="em-tableCopy" title="copy table"><svg viewBox="0 0 448 512" xmlns="http://www.w3.org/2000/svg"><path d="M320 448v40c0 13.255-10.745 24-24 24H24c-13.255 0-24-10.745-24-24V120c0-13.255 10.745-24 24-24h72v296c0 30.879 25.121 56 56 56h168zm0-344V0H152c-13.255 0-24 10.745-24 24v368c0 13.255 10.745 24 24 24h272c13.255 0 24-10.745 24-24V128H344c-13.2 0-24-10.8-24-24zm120.971-31.029L375.029 7.029A24 24 0 0 0 358.059 0H352v96h96v-6.059a24 24 0 0 0-7.029-16.97z"/></button><button class="em-tableSave" title="download table"><svg viewBox="0 0 512 512" xmlns="http://www.w3.org/2000/svg"><path d="M216 0h80c13.3 0 24 10.7 24 24v168h87.7c17.8 0 26.7 21.5 14.1 34.1L269.7 378.3c-7.5 7.5-19.8 7.5-27.3 0L90.1 226.1c-12.6-12.6-3.7-34.1 14.1-34.1H192V24c0-13.3 10.7-24 24-24zm296 376v112c0 13.3-10.7 24-24 24H24c-13.3 0-24-10.7-24-24V376c0-13.3 10.7-24 24-24h146.7l49 49c20.1 20.1 52.5 20.1 72.6 0l49-49H488c13.3 0 24 10.7 24 24zm-124 88c0-11-9-20-20-20s-20 9-20 20 9 20 20 20 20-9 20-20zm64 0c0-11-9-20-20-20s-20 9-20 20 9 20 20 20 20-9 20-20z"/></svg></button><label class="em-tableSwitch"><input type="checkbox"><span class="slider"></span></label></div></div>';

    if (total > 10) {
      var pages = Math.ceil(total / 10);

      var paginate = [],
        l = -1;
      paginate[++l] = '<div class="em-tablePag">';

      if (page - 3 > 0) {
        paginate[++l] =
          '<button class="em-tablePagItem" data-src="' +
          el.getAttribute("data-src") +
          "?s=" +
          sort +
          '">first</button>';
        paginate[++l] =
          '<button class="em-tablePagItem" data-src="' +
          el.getAttribute("data-src") +
          "?p=" +
          (page - 1) +
          "&s=" +
          sort +
          '"><span style="transform:rotate(-90deg);display:inline-block">▲</span></button>';
      }

      for (q = 1; q <= pages; q++) {
        if (
          q <= Math.max(page + 2, 5) &&
          (q >= Math.max(page - 2, 0) || pages - q < 5)
        ) {
          paginate[++l] = '<button class="em-tablePagItem';
          if (q == page) paginate[++l] = " disabled";
          paginate[++l] =
            '" data-src="' +
            el.getAttribute("data-src") +
            "?p=" +
            q +
            "&s=" +
            sort +
            '">' +
            q +
            "</button>";
        }

        if (q >= Math.max(page + 2, 5) && q < pages) {
          paginate[++l] =
            '<button class="em-tablePagItem" data-src="' +
            el.getAttribute("data-src") +
            "?p=" +
            (page + 1) +
            "&s=" +
            sort +
            '"><span style="transform:rotate(90deg);display:inline-block">▲</span></button>';
          paginate[++l] =
            '<button class="em-tablePagItem" data-src="' +
            el.getAttribute("data-src") +
            "?p=" +
            pages +
            "&s=" +
            sort +
            '">last</button>';
          break;
        }
      }

      paginate[++l] = "</div>";
      var pageMessage = page ? page * 10 : 10;
      var sortSelect = [];
      q = -1;

      for (x = 0; x < head.length; x++) {
        sortSelect[++q] =
          '<a class="em-tableSortOption desc" data-src="' +
          el.getAttribute("data-src") +
          "?p=" +
          page +
          "&s=" +
          head[x] +
          '.desc"><div class="em-tableSortArrow">▲</div>' +
          head[x] +
          "</a>";
        sortSelect[++q] =
          '<a class="em-tableSortOption asc" data-src="' +
          el.getAttribute("data-src") +
          "?p=" +
          page +
          "&s=" +
          head[x] +
          '.asc"><div class="em-tableSortArrow">▼</div>' +
          head[x] +
          "</a>";
      }

      r[++j] = '<div class="em-tableGetRows"><div>';
      r[++j] = paginate.join("");
      r[++j] =
        '<div class="em-tableCurrentRows">Showing records ' +
        (pageMessage - 9) +
        "-" +
        Math.min(pageMessage, total) +
        " of " +
        total +
        ".</div>";
      r[++j] =
        '<div class="em-tableSort">Sort by<button class="em-tableSortButton"><div class="em-tableSortArrow">';
      if (sort && sort.split(".").length > 0) {
        var ssplit = sort.split(".");
        r[++j] = ssplit[1] == "asc" ? "▼</div>" : "▲</div>";
        r[++j] = ssplit[0];
      } else {
        r[++j] = "..select..";
      }

      r[++j] =
        '</button><div class="em-tableSortSelect">' +
        sortSelect.join("") +
        "</div></div>";
      r[++j] = "</div></div>";
    } // table

    r[++j] = '<table class="em-table sort"><thead>'; // progress bar

    r[++j] = '<tr class="em-tableProg">';

    for (i = 0; i < head.length; i++) {
      r[++j] = "<th></th>";
    }

    r[++j] = "</tr>"; // add head to table

    r[++j] = "<tr>";

    for (i = 0; i < head.length; i++) {
      r[++j] = "<th>" + head[i];

      if (arr.length > 1) {
        r[++j] =
          '<svg class="icon-sm" viewBox="0 0 320 512" xmlns="http://www.w3.org/2000/svg"><path d="M41 288h238c21.4 0 32.1 25.9 17 41L177 448c-9.4 9.4-24.6 9.4-33.9 0L24 329c-15.1-15.1-4.4-41 17-41zm255-105L177 64c-9.4-9.4-24.6-9.4-33.9 0L24 183c-15.1 15.1-4.4 41 17 41h238c21.4 0 32.1-25.9 17-41z"></path></svg>';
      }

      r[++j] = "</th>";
    }

    r[++j] = "</th></tr></thead><tbody>"; // table body

    if (arr.length < 1 || total == 0) {
      r[++j] =
        '<tr><td colspan="' +
        (head.length || 1) +
        '">' +
        empty_msg +
        "</td></tr>";
    } else {
      for (key = 0; key < arr.length; key++) {
        if ("class" in arr[key]) {
          r[++j] = '<tr class="' + arr[key].class + '">';
        } else {
          r[++j] = "<tr>";
        }

        for (x = 0; x < head.length; x++) {
          r[++j] = "<td><div>" + arr[key][head[x]] + "</div></td>";
        }

        r[++j] = "</tr>";
      }
    }
    r[++j] = "</tbody>";
    r[++j] = '<caption class="em-tableLoad"><div></div></caption>';
    r[++j] = "</table>";

    el.innerHTML = r.join("");

    // add events - copy

    var copy = el.querySelector(".em-tableCopy");

    (function (copy, el) {
      copy.addEventListener("click", function () {
        var txt = document.createElement("textarea");
        txt.value = el.outerHTML;
        txt.setAttribute("readonly", "");
        txt.style = {
          position: "absolute",
          left: "-9999px",
        };
        document.body.appendChild(txt);
        txt.select();
        document.execCommand("copy");
        document.body.removeChild(txt);
      });
    })(copy, el.querySelector("table")); // save

    var save = el.querySelector(".em-tableSave");

    (function (save, el) {
      save.addEventListener("click", function () {
        var data = "",
          tableData = [],
          rows = el.querySelectorAll("tr:not(.em-tableProg)");

        for (var row = 0; row < rows.length; row++) {
          var rowData = [];
          var c = rows[row].querySelectorAll("th, td");

          for (var i = 0; i < c.length; i++) {
            rowData.push('"' + c[i].innerText + '"');
          }

          tableData.push(rowData.join(","));
        }

        data += tableData.join("\n");
        var a = document.createElement("a");
        a.href = URL.createObjectURL(
          new Blob([data], {
            type: "text/csv",
          })
        );
        a.setAttribute("download", "data.csv");
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      });
    })(save, el); // reload

    var reload = el.querySelector(".em-tableReload");

    (function (reload, el) {
      reload.addEventListener("click", function () {
        el.innerHTML =
          '<div class="loader-typing"><img src="/static/img/typing.gif"></div>';
        table(el);
      });
    })(reload, el);

    var autoReload = el.querySelector(".em-tableSwitch");
    /* auto reload */
    (function (autoReload, el) {
      var reloadTimer,
        load = function () {
          el.style.opacity = "0.5";
          table(el, undefined, true);
        },
        counter = 4,
        dataSpan = autoReload.querySelector("span.slider"),
        counting = function () {
          reloadTimer = window.setTimeout(countDown, 1000);
          dataSpan.classList.add("counting");
          dataSpan.setAttribute("data-counter", counter);
        },
        countDown = function () {
          counter = counter -= 1;
          dataSpan.setAttribute("data-counter", counter);
          if (counter < 1) {
            dataSpan.classList.remove("counting");
            window.clearTimeout(reloadTimer);
            reloadTimer = null;
            load();
          } else {
            reloadTimer = window.setTimeout(countDown, 1000);
          }
        },
        input = autoReload.querySelector("input");

      if (enableReload) {
        input.checked = true;
        counter = 4;
        counting();
      } else {
        if (typeof reloadTimer != "undefined") {
          window.clearTimeout(reloadTimer);
        }
      }

      input.addEventListener("click", function () {
        if (input.checked) {
          counting();
        } else {
          dataSpan.classList.remove("counting");
          autoReload.removeAttribute("checked");
          input.checked = false;
          window.clearTimeout(reloadTimer);
        }
      });
    })(autoReload, el); // sort

    var th = el.querySelectorAll("tr:not(.em-tableProg) th");
    function my_tr_clic(h, el) {
      h.addEventListener("click", function () {
        var table = el.querySelector("tbody"),
          r = Array.from(table.querySelectorAll("tr")).sort(
            comparer(index(h) - 1)
          );
        this.asc = !this.asc;
        if (!this.asc) r = r.reverse();

        for (var i = 0; i < r.length; i++) {
          table.append(r[i]);
        }
      });
    }

    if (th.length > 0) {
      for (q = 0; q < th.length; q++) {
        new my_tr_clic(th[q], el);
      }
    } // other pages

    var otherPages = el.querySelectorAll(".em-tablePagItem:not(.disabled)");

    function my_click_loader(h, el) {
      h.addEventListener("click", function () {
        el.innerHTML =
          '<div class="loader-typing"><img src="/static/img/typing.gif"></div>';
        table(this, el);
      });
    }

    for (q = 0; q < otherPages.length; q++) {
      new my_click_loader(otherPages[q], el);
    } // sort

    var tableSort = el.querySelectorAll(".em-tableSortOption");

    for (q = 0; q < tableSort.length; q++) {
      new my_click_loader(tableSort[q], el);
    }
  }

  var comparer = function comparer(index) {
      return function (a, b) {
        var valA = getCellValue(a, index).replace("$", ""),
          valB = getCellValue(b, index).replace("$", "");
        if (
          /^\d{1,2}\/\d{1,2}\/\d{2,4}$/.test(valA) &&
          /^\d{1,2}\/\d{1,2}\/\d{2,4}$/.test(valB)
        )
          return new Date(valA) - new Date(valB);

        if (isNumeric(valA) && isNumeric(valB)) {
          return valA - valB;
        }
        return valA.toString().localeCompare(valB);
      };
    },
    isNumeric = function isNumeric(n) {
      return !isNaN(parseFloat(n)) && isFinite(n);
    },
    getCellValue = function getCellValue(row, index) {
      return row.getElementsByTagName("td")[index].textContent;
    },
    index = function index(el) {
      if (!el) return -1;
      var i = 0;

      while (el) {
        i++;
        el = el.previousElementSibling;
      }

      return i;
    };
})();
