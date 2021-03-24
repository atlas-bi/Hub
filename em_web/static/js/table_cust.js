(function (rhc_table, $, undefined) {
  rhc_table.cell_processor = function (cell_value) {
    // custom modifications to table cells happens here.
    var tmp_div, href;

    if (cell_value.indexOf("Enable") != -1) {
      tmp_div = document.createElement("div");
      tmp_div.innerHTML = cell_value;
      href = tmp_div.getElementsByTagName("a")[0].getAttribute("href");
      return (
        '<label class="em-switch"><input action="' +
        href +
        '" type="checkbox"><span class="slider"></span></label>'
      );
    }

    if (cell_value.indexOf("Disable") != -1) {
      tmp_div = document.createElement("div");
      tmp_div.innerHTML = cell_value;
      href = tmp_div.getElementsByTagName("a")[0].getAttribute("href");
      return (
        '<label class="em-switch"><input action="' +
        href +
        '" type="checkbox" checked><span class="slider"></span></label>'
      );
    }

    return cell_value;
  };
})((window.rhc_table = window.rhc_table || {}));
