(function () {
  document.addEventListener("click", function (e) {
    if (
      e.target.closest(".em-eraseInput") &&
      e.target.closest(".em-eraseInput").hasAttribute("data-toggle") &&
      e.target.closest(".em-eraseInput").hasAttribute("data-target") &&
      e.target.closest(".em-eraseInput").getAttribute("data-toggle") ===
        "erasor"
    ) {
      var t = document.querySelector(
        'input[name="' +
          e.target.closest(".em-eraseInput").getAttribute("data-target") +
          '"]'
      );

      t.value = "";
    }
  });
})();
