(function (rhcTable, $, undefined) {
  rhcTable.cellProcessor = function (cellValue) {
    // custom modifications to table cells happens here.
    var tmpDiv, href;

    if (cellValue.indexOf("Enable") !== -1) {
      tmpDiv = document.createElement("div");
      tmpDiv.innerHTML = cellValue;
      href = tmpDiv.getElementsByTagName("a")[0].getAttribute("href");
      return (
        '<label class="em-switch"><input action="' +
        href +
        '" type="checkbox"><span class="slider"></span></label>'
      );
    }

    if (cellValue.indexOf("Disable") !== -1) {
      tmpDiv = document.createElement("div");
      tmpDiv.innerHTML = cellValue;
      href = tmpDiv.getElementsByTagName("a")[0].getAttribute("href");
      return (
        '<label class="em-switch"><input action="' +
        href +
        '" type="checkbox" checked><span class="slider"></span></label>'
      );
    }

    return cellValue;
  };
})((window.rhcTable = window.rhcTable || {}));
