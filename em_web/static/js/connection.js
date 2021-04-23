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
  var myTextArea = document.querySelectorAll("textarea.database_connection_string");
  for (var x = 0; x < myTextArea.length; x++) {
    if (myTextArea[x]) {
      var myCodeMirror = CodeMirror.fromTextArea(myTextArea[x], {
        theme: "nord",
        mode: "shell",
        autoRefresh: true,
        viewportMargin: Infinity,
        lineWrapping: true,
        lineNumbers: true,
        matchBrackets: true,
        enableSearchTools: true,
        enableCodeFormatting: true,
        scrollbarStyle: "overlay",
      });
    }
  }

  document.addEventListener("click", function (e) {
    if (e.target.closest(".dataSource-copy")) {
      var txt = document.createElement("textarea");
      txt.value = e.target
        .closest(".dataSource-copy")
        .getAttribute("data-value");
      txt.setAttribute("readonly", "");
      txt.style = {
        position: "absolute",
        left: "-9999px",
      };
      document.body.appendChild(txt);
      txt.select();
      document.execCommand("copy");
      document.body.removeChild(txt);
    }
  });
})();

(function () {
  var d = document;
  var t, q;

  d.addEventListener("click", function (e) {
    if (e.target.closest("#connections-addSftp")) {
      t = e.target.closest("#connections-addSftp");
      //get teamplate
      q = new XMLHttpRequest();
      q.open("get", "/connection/sftp", true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();

      q.onload = function () {
        var sftp, smb, gpg,ssh, ftp, database;
        if (d.querySelectorAll(".em-drop[data-sftp]").length > 0) {
          sftp = Math.max.apply(
            Math,
            Array.from(document.querySelectorAll(".em-drop[data-sftp]")).map(
              function (x) {
                return x.getAttribute("data-sftp");
              }
            )
          );
          sftp++;
        } else {
          sftp = 1;
        }
        document
          .getElementById("em-elementGroupSftp")
          .insertAdjacentHTML(
            "beforeend",
            q.responseText
              .replace(/sftp1/gm, "sftp" + sftp)
              .replace(/data-sftp="1"/gm, 'data-sftp="' + sftp + '"')
          );
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest("#connections-addSmb")) {
      t = e.target.closest("#connections-addSmb");
      //get teamplate
      q = new XMLHttpRequest();
      q.open("get", "/connection/smb", true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();

      q.onload = function () {
        if (d.querySelectorAll(".em-drop[data-smb]").length > 0) {
          smb = Math.max.apply(
            Math,
            Array.from(document.querySelectorAll(".em-drop[data-smb]")).map(
              function (x) {
                return x.getAttribute("data-smb");
              }
            )
          );
          smb++;
        } else {
          smb = 1;
        }
        document
          .getElementById("em-elementGroupSmb")
          .insertAdjacentHTML(
            "beforeend",
            q.responseText
              .replace(/smb1/gm, "smb" + smb)
              .replace(/data-smb="1"/gm, 'data-smb="' + smb + '"')
          );
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest("#connections-addGpg")) {
      t = e.target.closest("#connections-addGpg");
      //get teamplate
      q = new XMLHttpRequest();
      q.open("get", "/connection/gpg", true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();

      q.onload = function () {
        if (d.querySelectorAll(".em-drop[data-gpg]").length > 0) {
          gpg = Math.max.apply(
            Math,
            Array.from(document.querySelectorAll(".em-drop[data-gpg]")).map(
              function (x) {
                return x.getAttribute("data-gpg");
              }
            )
          );
          gpg++;
        } else {
          gpg = 1;
        }
        document
          .getElementById("em-elementGroupGpg")
          .insertAdjacentHTML(
            "beforeend",
            q.responseText
              .replace(/gpg1/gm, "gpg" + gpg)
              .replace(/data-gpg="1"/gm, 'data-gpg="' + gpg + '"')
          );
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest("#connections-addSsh")) {
      t = e.target.closest("#connections-addSsh");
      //get teamplate
      q = new XMLHttpRequest();
      q.open("get", "/connection/ssh", true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();

      q.onload = function () {
        if (d.querySelectorAll(".em-drop[data-ssh]").length > 0) {
          ssh = Math.max.apply(
            Math,
            Array.from(document.querySelectorAll(".em-drop[data-ssh]")).map(
              function (x) {
                return x.getAttribute("data-ssh");
              }
            )
          );
          ssh++;
        } else {
          ssh = 1;
        }
        document
          .getElementById("em-elementGroupSsh")
          .insertAdjacentHTML(
            "beforeend",
            q.responseText
              .replace(/ssh1/gm, "ssh" + ssh)
              .replace(/data-ssh="1"/gm, 'data-ssh="' + ssh + '"')
          );
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest("#connections-addFtp")) {
      t = e.target.closest("#connections-addFtp");
      //get teamplate
      q = new XMLHttpRequest();
      q.open("get", "/connection/ftp", true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();

      q.onload = function () {
        if (d.querySelectorAll(".em-drop[data-ftp]").length > 0) {
          ftp = Math.max.apply(
            Math,
            Array.from(document.querySelectorAll(".em-drop[data-ftp]")).map(
              function (x) {
                return x.getAttribute("data-ftp");
              }
            )
          );
          ftp++;
        } else {
          ftp = 1;
        }
        document
          .getElementById("em-elementGroupFtp")
          .insertAdjacentHTML(
            "beforeend",
            q.responseText
              .replace(/ftp1/gm, "ftp" + ftp)
              .replace(/data-ftp="1"/gm, 'data-ftp="' + ftp + '"')
          );
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest("#connections-addDatabase")) {
      t = e.target.closest("#connections-addDatabase");

      //get teamplate
      q = new XMLHttpRequest();
      q.open("get", "/connection/database", true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();

      q.onload = function () {
        if (d.querySelectorAll(".em-drop[data-database]").length > 0) {
          database = Math.max.apply(
            Math,
            Array.from(
              document.querySelectorAll(".em-drop[data-database]")
            ).map(function (x) {
              return x.getAttribute("data-database");
            })
          );
          database++;
        } else {
          database = 1;
        }
        document
          .getElementById("em-elementGroupDatabase")
          .insertAdjacentHTML(
            "beforeend",
            q.responseText
              .replace(/database1/gm, "database" + database)
              .replace(
                /data-database="1"/gm,
                'data-database="' + database + '"'
              )
          );
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    }
  });
})();
