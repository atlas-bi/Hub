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
  // on click of checkbox change input value
  var d = document;

  var myTextArea = d.querySelector('textarea[name="sourceCode"]');
  if (myTextArea) {
    var mySourceCodeMirror = CodeMirror.fromTextArea(myTextArea, {
      theme: "nord",
      mode: "sql",
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
  var myProcessingTextArea = d.querySelector('textarea[name="processingCode"]');
  if (myProcessingTextArea) {
    var myProcessingCodeMirror = CodeMirror.fromTextArea(myProcessingTextArea, {
      theme: "nord",
      mode: "python",
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

  d.addEventListener("click", function (e) {
    var i, ipt, q;
    if (e.target.closest("#project_cron_check")) {
      i = e.target.closest("#project_cron_check");
      ipt = d.querySelector('input[name="project_cron"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
      }
    } else if (e.target.closest("#project_intv_check")) {
      i = e.target.closest("#project_intv_check");
      ipt = d.querySelector('input[name="project_intv"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
      }
    } else if (e.target.closest("#project_ooff_check")) {
      i = e.target.closest("#project_ooff_check");
      ipt = d.querySelector('input[name="project_ooff"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_ooff_check")) {
      i = e.target.closest(".task_ooff_check");
      ipt = d.querySelector('input[name="task-ooff"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest("#project_take_ownership")) {
      i = e.target.closest("#project_take_ownership");
      ipt = d.querySelector('input[name="project_ownership"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_overwrite_smb_if_exists")) {
      i = e.target.closest(".task_overwrite_smb_if_exists");
      ipt = d.querySelector('input[name="task_overwrite_smb"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_overwrite_sftp_if_exists")) {
      i = e.target.closest(".task_overwrite_sftp_if_exists");
      ipt = d.querySelector('input[name="task_overwrite_sftp"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_overwrite_ftp_if_exists")) {
      i = e.target.closest(".task_overwrite_ftp_if_exists");
      ipt = d.querySelector('input[name="task_overwrite_ftp"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_save_sftp")) {
      i = e.target.closest(".task_save_sftp");
      ipt = d.querySelector('input[name="task_save_sftp"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_file_gpg")) {
      i = e.target.closest(".task_file_gpg");
      ipt = d.querySelector('input[name="task_file_gpg"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_save_ftp")) {
      i = e.target.closest(".task_save_ftp");
      ipt = d.querySelector('input[name="task_save_ftp"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_save_smb")) {
      i = e.target.closest(".task_save_smb");
      ipt = d.querySelector('input[name="task_save_smb"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".send_completion_email_check")) {
      i = e.target.closest(".send_completion_email_check");
      ipt = d.querySelector('input[name="task_send_completion_email"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_smb_ignore_delimiter")) {
      i = e.target.closest(".task_smb_ignore_delimiter");
      ipt = d.querySelector('input[name="task_smb_ignore_delimiter"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_sftp_ignore_delimiter")) {
      i = e.target.closest(".task_sftp_ignore_delimiter");
      ipt = d.querySelector('input[name="task_sftp_ignore_delimiter"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_ftp_ignore_delimiter")) {
      i = e.target.closest(".task_ftp_ignore_delimiter");
      ipt = d.querySelector('input[name="task_ftp_ignore_delimiter"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_ignore_file_delimiter")) {
      i = e.target.closest(".task_ignore_file_delimiter");
      ipt = d.querySelector('input[name="task_ignore_file_delimiter"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".send_completion_email_log_check")) {
      i = e.target.closest(".send_completion_email_log_check");
      ipt = d.querySelector('input[name="task_send_completion_email_log"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".send_output_check")) {
      i = e.target.closest(".send_output_check");
      ipt = d.querySelector('input[name="task_send_output"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_embed_output")) {
      i = e.target.closest(".task_embed_output");
      ipt = d.querySelector('input[name="task_embed_output"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".send_error_email_check")) {
      i = e.target.closest(".send_error_email_check");
      ipt = d.querySelector('input[name="task_send_error_email"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_dont_send_empty")) {
      i = e.target.closest(".task_dont_send_empty");
      ipt = d.querySelector('input[name="task_dont_send_empty"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_include_query_headers")) {
      i = e.target.closest(".task_include_query_headers");
      ipt = d.querySelector('input[name="task_include_query_headers"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        // add required attr on inputs
      }
    } else if (e.target.closest(".task_create_zip")) {
      i = e.target.closest(".task_create_zip");
      ipt = d.querySelector('input[name="task_create_zip"]');
      if (i.getAttribute("checked") === "checked") {
        i.removeAttribute("checked");
        ipt.value = 0;
        document.querySelector(".task-destinationZip").style.display = "None";
        // remove required attr on inputs
      } else {
        i.setAttribute("checked", "checked");
        ipt.value = 1;
        document
          .querySelector(".task-destinationZip")
          .style.removeProperty("display");
        // add required attr on inputs
      }
    } else if (e.target.closest("#job-addTask")) {
      //get teamplate
      q = new XMLHttpRequest();
      q.open("get", "/jobs/task", true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();

      q.onload = function () {
        var task = d
          .querySelectorAll(".em-drop[data-task]")
          [d.querySelectorAll(".em-drop[data-task]").length - 1].getAttribute(
            "data-task"
          );
        task++;
        document
          .getElementById("em-elementGroup")
          .insertAdjacentHTML(
            "beforeend",
            q.responseText
              .replace(/task1/gm, "task" + task)
              .replace(/data-task="1"/gm, 'data-task="' + task + '"')
          );
        // update titles
        var drop = document.querySelectorAll(".em-drop[data-task]");
        for (var x = 0; x < drop.length; x++) {
          drop[x].innerHTML =
            "Stop " +
            numberToEnglish(x + 1, "") +
            '<svg class="em-dropIcon" viewBox="0 0 320 512" xmlns="http://www.w3.org/2000/svg"><path d="m143 352.3-136-136c-9.4-9.4-9.4-24.6 0-33.9l22.6-22.6c9.4-9.4 24.6-9.4 33.9 0l96.4 96.4 96.4-96.4c9.4-9.4 24.6-9.4 33.9 0l22.6 22.6c9.4 9.4 9.4 24.6 0 33.9l-136 136c-9.2 9.4-24.4 9.4-33.8 0z"/></svg>';
        }
      };
    }
  });

  d.addEventListener("change", function (e) {
    var t, p, q;
    if (e.target.closest('select[name="smb_destination"]')) {
      t = e.target.closest('select[name="smb_destination"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-smb")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/smb-dest?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector("." + t.getAttribute("data-smb"));
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="sftp_destination"]')) {
      t = e.target.closest('select[name="sftp_destination"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-sftp")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/sftp-dest?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector(
          "." + t.getAttribute("data-sftp")
        );
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="gpg_file"]')) {
      t = e.target.closest('select[name="gpg_file"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-gpg")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/gpg-file?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector("." + t.getAttribute("data-gpg"));
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="sftp_processing"]')) {
      t = e.target.closest('select[name="sftp_processing"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-sftp")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/sftp-processing?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector(
          "." + t.getAttribute("data-sftp")
        );
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="sftp_source"]')) {
      t = e.target.closest('select[name="sftp_source"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-sftp")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/sftp-source?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector(
          "." + t.getAttribute("data-sftp")
        );
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="sftp_query"]')) {
      t = e.target.closest('select[name="sftp_query"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-sftp")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/sftp-query?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector(
          "." + t.getAttribute("data-sftp")
        );
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="ftp_source"]')) {
      t = e.target.closest('select[name="ftp_source"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-ftp")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/ftp-source?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector("." + t.getAttribute("data-ftp"));
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="ssh_source"]')) {
      t = e.target.closest('select[name="ssh_source"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-ssh")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/ssh-source?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector("." + t.getAttribute("data-ssh"));
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="ftp_processing"]')) {
      t = e.target.closest('select[name="ftp_processing"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-ftp")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/ftp-processing?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector("." + t.getAttribute("data-ftp"));
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="ftp_destination"]')) {
      t = e.target.closest('select[name="ftp_destination"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-ftp")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/ftp-dest?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector("." + t.getAttribute("data-ftp"));
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="ftp_query"]')) {
      t = e.target.closest('select[name="ftp_query"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-ftp")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/ftp-query?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector("." + t.getAttribute("data-ftp"));
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="smb_source"]')) {
      t = e.target.closest('select[name="smb_source"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-smb")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/smb-source?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector("." + t.getAttribute("data-smb"));
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="smb_processing"]')) {
      t = e.target.closest('select[name="smb_processing"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-smb")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/smb-processing?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector("." + t.getAttribute("data-smb"));
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="smb_query"]')) {
      t = e.target.closest('select[name="smb_query"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-smb")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/smb-query?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector("." + t.getAttribute("data-smb"));
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="database_source"]')) {
      t = e.target.closest('select[name="database_source"]');
      if (t.value == "none") {
        t.parentElement.querySelector(
          "." + t.getAttribute("data-database")
        ).innerHTML = "";
        return;
      }
      q = new XMLHttpRequest();
      q.open("get", "/task/database-source?org=" + t.value, true);
      q.setRequestHeader(
        "Content-Type",
        "application/x-www-form-urlencoded; charset=UTF-8"
      );
      q.setRequestHeader("Ajax", "True");
      q.send();
      q.onload = function () {
        var p = t.parentElement.querySelector(
          "." + t.getAttribute("data-database")
        );
        p.innerHTML = q.responseText;

        var s = p.querySelector("script");
        if (s) {
          l = document.createElement("script");
          l.innerHTML = s.innerText;
          document.querySelector("body").appendChild(l);
        }
        if (t.closest(".clps-o")) {
          t.closest(".clps-o").dispatchEvent(
            new Event("change", {
              bubbles: true,
            })
          );
        }
      };
    } else if (e.target.closest('select[name="sourceType"]')) {
      t = e.target.closest('select[name="sourceType"]');
      p = t.closest("div");
      p.querySelector(".task-sourceDatabase").style.display = "none";
      p.querySelector(".task-sourceSmb").style.display = "none";
      p.querySelector(".task-sourceSftp").style.display = "none";
      p.querySelector(".task-sourceFtp").style.display = "none";
      p.querySelector(".task-query-location").style.display = "none";
      p.querySelector(".task-sourceSsh").style.display = "none";

      if (t.value === 1) {
        p.querySelector(".task-sourceDatabase").style.removeProperty("display");
        p.querySelector(".task-query-location").style.removeProperty("display");
      } else if (t.value === 2) {
        p.querySelector(".task-sourceSmb").style.removeProperty("display");
      } else if (t.value === 3) {
        p.querySelector(".task-sourceSftp").style.removeProperty("display");
      } else if (t.value === 4) {
        p.querySelector(".task-sourceFtp").style.removeProperty("display");
      } else if (t.value === 5) {
      } else if (t.value === 6) {
        p.querySelector(".task-sourceSsh").style.removeProperty("display");
        p.querySelector(".task-query-location").style.removeProperty("display");
      }
    } else if (e.target.closest('select[name="sourceQueryType"]')) {
      t = e.target.closest('select[name="sourceQueryType"]');
      p = t.closest("div");

      p.querySelector(".task-sourceGit").style.display = "none";
      p.querySelector(".task-sourceFtpQuery").style.display = "none";
      p.querySelector(".task-sourceSmbQuery").style.display = "none";
      p.querySelector(".task-sourceSftpQuery").style.display = "none";
      p.querySelector(".task-sourceURL").style.display = "none";
      p.querySelector(".task-sourceCode").style.display = "none";

      if (t.value === 1) {
        p.querySelector(".task-sourceGit").style.removeProperty("display");
      } else if (t.value === 2) {
        p.querySelector(".task-sourceSmbQuery").style.removeProperty("display");
      } else if (t.value === 3) {
        p.querySelector(".task-sourceURL").style.removeProperty("display");
      } else if (t.value === 4) {
        p.querySelector(".task-sourceCode").style.removeProperty("display");
      } else if (t.value === 5) {
        p.querySelector(".task-sourceSftpQuery").style.removeProperty(
          "display"
        );
      } else if (t.value === 6) {
        p.querySelector(".task-sourceFtpQuery").style.removeProperty("display");
      }
    } else if (e.target.closest('select[name="processingType"]')) {
      t = e.target.closest('select[name="processingType"]');
      p = t.closest("div");

      p.querySelector(".task-processingGit").style.display = "none";
      p.querySelector(".task-processingFtp").style.display = "none";
      p.querySelector(".task-processingSmb").style.display = "none";
      p.querySelector(".task-processingSftp").style.display = "none";
      p.querySelector(".task-processingUrl").style.display = "none";
      p.querySelector(".task-processingCode").style.display = "none";
      p.querySelector(".task-processingCommand").style.removeProperty(
        "display"
      );

      if (t.value === 1) {
        p.querySelector(".task-processingSmb").style.removeProperty("display");
      } else if (t.value === 2) {
        p.querySelector(".task-processingSftp").style.removeProperty("display");
      } else if (t.value === 3) {
        p.querySelector(".task-processingFtp").style.removeProperty("display");
      } else if (t.value === 4) {
        p.querySelector(".task-processingGit").style.removeProperty("display");
      } else if (t.value === 5) {
        p.querySelector(".task-processingUrl").style.removeProperty("display");
      } else if (t.value === 6) {
        p.querySelector(".task-processingCode").style.removeProperty("display");
        p.querySelector(".task-processingCommand").style.display = "none";
      }
    } else if (e.target.closest('select[name="fileType"]')) {
      t = e.target.closest('select[name="fileType"]');
      p = t.closest("div");
      p.querySelector(".task-delimiter").style.display = "none";

      if (t.value === 2 || t.value === 4) {
        p.querySelector(".task-delimiter").style.removeProperty("display");
      }
    }
    if (typeof mySourceCodeMirror != "undefined") mySourceCodeMirror.refresh();
    if (typeof myProcessingCodeMirror != "undefined")
      myProcessingCodeMirror.refresh();
  });

  try {
    flatpickr("#project_ooff_date", {
      enableTime: true,
      dateFormat: "Y-m-d H:i",
      weekNumbers: true,
      time_24hr: true,
    });
    flatpickr("#project_intv_edate", {
      enableTime: true,
      dateFormat: "Y-m-d H:i",
      weekNumbers: true,
      time_24hr: true,
    });
    flatpickr("#project_intv_sdate", {
      enableTime: true,
      dateFormat: "Y-m-d H:i",
      weekNumbers: true,
      time_24hr: true,
    });
    flatpickr("#project_cron_edate", {
      enableTime: true,
      dateFormat: "Y-m-d H:i",
      weekNumbers: true,
      time_24hr: true,
    });
    flatpickr("#project_cron_sdate", {
      enableTime: true,
      dateFormat: "Y-m-d H:i",
      weekNumbers: true,
      time_24hr: true,
    });
  } catch (e) {}
})();
