(function () {
  document.addEventListener('click', function (e) {
    if (
      e.target.closest('.em-eraseInput') &&
      e.target.closest('.em-eraseInput').hasAttribute('data-toggle') &&
      e.target.closest('.em-eraseInput').hasAttribute('data-target') &&
      e.target.closest('.em-eraseInput').getAttribute('data-toggle') ===
        'erasor'
    ) {
      var t = document.querySelector(
        'input[name="' +
          e.target.closest('.em-eraseInput').getAttribute('data-target') +
          '"]',
      );

      t.value = '';
    }
  });

  // add documentation links
  var doc_links = [].slice.call(document.querySelectorAll('[data-docs]'));
  for (var x = 0; x < doc_links.length; x++) {
    doc_links[x].innerHTML +=
      `<a class="is-pulled-right has-text-info" href="https://atlas.bi/docs/automation-hub/` +
      doc_links[x].getAttribute('data-docs') +
      `" target="_blank" rel="noopener"><span class="icon">
    <i class="far fa-circle-question"></i>
  </span></a>`;
  }
})();
