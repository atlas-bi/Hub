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
  document.addEventListener("click", function (e) {
    if (
      e.target.closest(".em-showPass") &&
      e.target.closest(".em-showPass").hasAttribute("data-toggle") &&
      e.target.closest(".em-showPass").hasAttribute("data-target") &&
      e.target.closest(".em-showPass").getAttribute("data-toggle") == "password"
    ) {
      var t = document.querySelector(
        'input[name="' +
          e.target.closest(".em-showPass").getAttribute("data-target") +
          '"]'
      );

      if (!t.classList.contains("em-inputPassword"))
        t.classList.add("em-inputPassword");

      t.type = t.type == "text" ? "password" : "text";
    } else if (e.target.closest(".em-inputPlainCopy")) {
      e.preventDefault();
      var txt = document.createElement("textarea");
      txt.value = e.target
        .closest(".em-inputPlainCopy")
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
