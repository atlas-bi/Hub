(function () {
  var myTextArea = document.querySelectorAll('textarea.connection_string');
  for (var x = 0; x < myTextArea.length; x++) {
    if (myTextArea[x]) {
      // eslint-disable-next-line no-undef,no-unused-vars
      var myCodeMirror = CodeMirror.fromTextArea(myTextArea[x], {
        theme: 'ttcn',
        mode: 'sql',
        autoRefresh: true,
        viewportMargin: Infinity,
        lineWrapping: true,
        lineNumbers: true,
        matchBrackets: true,
        enableSearchTools: true,
        enableCodeFormatting: true,
        scrollbarStyle: 'overlay',
      });
    }
  }
})();
