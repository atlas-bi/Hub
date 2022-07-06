(function (rhcTable, $, undefined) {
  var tables = document.getElementsByClassName('em-ajaxTable');

  for (var x = 0; x < tables.length; x++) {
    if (tables[x].hasAttribute('data-src')) table(tables[x]);
  }

  function table(el, dest, reload) {
    if (typeof dest == 'undefined') dest = el;
    if (typeof reload == 'undefined') reload = false;
    q = new XMLHttpRequest();
    q.open(
      'get',
      el.getAttribute('data-src'), //+ "&v=" + new Date().getTime(),
      true,
    );
    q.send();

    q.onload = function () {
      try {
        loadTable(JSON.parse(this.responseText), dest, reload);
        dest.style.removeProperty('opacity');
      } catch (e) {
        dest.innerHTML =
          "<span class='em-error'>Failed to load. " + e + '</span>';
      }
      dest.style.removeProperty('height');
    };
  }

  function loadTable(arr, el, enableReload) {
    var out = '',
      i,
      x,
      head = [],
      total = arr.length,
      key,
      page = 1,
      page_size = 10,
      sort = '',
      q,
      empty_msg = 'No data to show.',
      current_date = new Date()
        .toLocaleString()
        .replace(',', '')
        .replace(/:\d\d\s/, ' ');

    // get total rows
    for (x = 0; x < arr.length; x++) {
      if (arr[x].total || arr[x].total == 0) {
        total = parseInt(arr[x].total);
        arr.splice(x, 1);
        break;
      }
    }
    for (x = 0; x < arr.length; x++) {
      if (arr[x].page_size) {
        page_size = parseInt(arr[x].page_size);
        arr.splice(x, 1);
        break;
      }
    }
    for (x = 0; x < arr.length; x++) {
      if (arr[x].page || arr[x].page == 0) {
        page = parseInt(arr[x].page) + 1;
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
    if (el.classList.contains('no-box')) {
      r[++j] = '<div class="container">';
    } else {
      r[++j] = '<div class="box">';
    }
    if (!el.classList.contains('no-tools')) {
      var ticks = new Date().getTime();
      r[++j] =
        '<div class="em-tableTools">' +
        '<div class="field is-grouped">' +
        '<div class="field has-addons">' +
        '<p class="control"><button class="button em-tableReload" title="refresh"><span class="icon"><i class="fas fa-rotate"></i></span><span>Refresh</span></button></p>' +
        '<p class="control"><button class="button em-tableCopy" title="copy table"><span class="icon"><i class="fas fa-copy"></i></span><span>Copy</span></button></p>' +
        '<p class="control"><button class="button em-tableSave" title="download table"><span class="icon"><i class="fas fa-download"></i></span><span>Download</span></button></p>' +
        '</div>' +
        '<div class="field"><p class="control ml-2 mr-0 mt-2"><input id="reload-switch-' +
        ticks +
        '" type="checkbox" class="switch is-rounded is-info"><label for="reload-switch-' +
        ticks +
        '">Auto Refresh</label><p></div>' +
        '</div></div>';
    }

    if (total > page_size) {
      var pages = Math.ceil(total / page_size);

      var paginate = [],
        l = -1;
      paginate[++l] =
        '<nav class="level my-3"><div class="level-left"><div class="level-item"><nav class="pagination  is-close em-tablePag" role="navigation" aria-label="pagination"><ul class="pagination-list">';

      if (page - 3 > 0) {
        paginate[++l] =
          '<li><a class="em-tablePagItem pagination-link" data-src="' +
          el.getAttribute('data-src') +
          '?s=' +
          sort +
          '">first</a></li>';
        paginate[++l] =
          '<li><a class="em-tablePagItem pagination-link" data-src="' +
          el.getAttribute('data-src') +
          '?p=' +
          (page - 1) +
          '&s=' +
          sort +
          '"><span style="transform:rotate(-90deg);display:inline-block">▲</span></a></li>';
      }

      for (q = 1; q <= pages; q++) {
        if (
          q <= Math.max(page + 2, 5) &&
          (q >= Math.max(page - 2, 0) || pages - q < 5)
        ) {
          paginate[++l] = '<li><a class="em-tablePagItem pagination-link';
          if (q == page) paginate[++l] = ' is-disabled is-current';
          paginate[++l] =
            '" data-src="' +
            el.getAttribute('data-src') +
            '?p=' +
            q +
            '&s=' +
            sort +
            '">' +
            q +
            '</a></li>';
        }

        if (q >= Math.max(page + 2, 5) && q < pages) {
          paginate[++l] =
            '<li><a class="em-tablePagItem pagination-link" data-src="' +
            el.getAttribute('data-src') +
            '?p=' +
            (page + 1) +
            '&s=' +
            sort +
            '"><span style="transform:rotate(90deg);display:inline-block">▲</span></a></li>';
          paginate[++l] =
            '<li><a class="em-tablePagItem pagination-link" data-src="' +
            el.getAttribute('data-src') +
            '?p=' +
            pages +
            '&s=' +
            sort +
            '">last</a></li>';
          break;
        }
      }

      paginate[++l] = "</ul></nav></div><div class='level-item'>";
      var pageMessage = page ? page * page_size : page_size;

      r[++j] = '<div class="em-tableGetRows"><div>';
      r[++j] = paginate.join('');
      r[++j] =
        '<div class="em-tableCurrentRows">Showing records ' +
        (pageMessage - parseInt(page_size - 1)) +
        '-' +
        Math.min(pageMessage, total) +
        ' of ' +
        total +
        ". </div></div></div><div class='level-right'><div class='level-item'>";

      var sortSelect = [];
      q = -1;

      for (x = 0; x < head.length; x++) {
        sortSelect[++q] =
          '<option class="em-tableSortOption desc" data-src="' +
          el.getAttribute('data-src') +
          '?p=' +
          page +
          '&s=' +
          head[x] +
          '.desc">▲&ensp;' +
          head[x] +
          '</option>';
        sortSelect[++q] =
          '<option class="em-tableSortOption asc" data-src="' +
          el.getAttribute('data-src') +
          '?p=' +
          page +
          '&s=' +
          head[x] +
          '.asc">▼&ensp;' +
          head[x] +
          '</option>';
      }

      r[++j] =
        '<div class="level-item">Sort by</div><div class="em-tableSort"><div class="select"><select><option>';
      if (sort && sort.split('.').length > 0) {
        var ssplit = sort.split('.');
        r[++j] = ssplit[1] == 'asc' ? '▼&ensp;' : '▲&ensp;';
        r[++j] = ssplit[0];
      } else {
        r[++j] = '..select..';
      }

      r[++j] = sortSelect.join('');
      r[++j] = '</select></div></div></div></div></div>';
    } // table

    theme = '';
    if (el.hasAttribute('data-theme')) {
      theme = ' table' + el.getAttribute('data-theme');
    }

    r[++j] =
      '<div class="table-container"><table class="table is-narrow is-fullwidth sort ' +
      theme +
      '"><thead>';

    // add head to table

    r[++j] = '<tr>';

    for (i = 0; i < head.length; i++) {
      r[++j] = "<th style='text-align:left;white-space:pre'>" + head[i];

      if (arr.length > 1) {
        r[++j] = '<span class="icon"><i class="fas fa-sort"></i></span>';
      }

      r[++j] = '</th>';
    }

    r[++j] = '</th></tr></thead><tbody>'; // table body

    if (arr.length < 1 || total == 0) {
      r[++j] =
        '<tr><td colspan="' +
        (head.length || 1) +
        '">' +
        empty_msg +
        '</td></tr>';
    } else {
      for (key = 0; key < arr.length; key++) {
        if ('class' in arr[key]) {
          r[++j] = '<tr class="' + arr[key].class + '">';
        } else {
          r[++j] = '<tr>';
        }

        for (x = 0; x < head.length; x++) {
          var cell_value = (arr[key][head[x]] || '').toString();

          if (rhcTable.cellProcessor !== undefined) {
            cell_value = rhcTable.cellProcessor(cell_value);
          }

          r[++j] = '<td><div>' + cell_value + '</div></td>';
        }

        r[++j] = '</tr>';
      }
    }
    r[++j] = '</tbody>';
    r[++j] = '<caption class="em-tableLoad"><div></div></caption>';
    r[++j] = '</table></div>';
    r[++j] =
      "<div class='has-text-weight-light has-text-grey em-tableUpdated'>" +
      current_date +
      '</div></div>';

    el.innerHTML = r.join('');

    // add events - copy

    var copy = el.querySelector('.em-tableCopy');

    if (copy) {
      (function (copy, el) {
        copy.addEventListener('click', function () {
          var txt = document.createElement('textarea');
          txt.value = el.outerHTML;
          txt.setAttribute('readonly', '');
          txt.style = {
            position: 'absolute',
            left: '-9999px',
          };
          document.body.appendChild(txt);
          txt.select();
          document.execCommand('copy');
          document.body.removeChild(txt);
        });
      })(copy, el.querySelector('table')); // save
    }

    var save = el.querySelector('.em-tableSave');
    if (save) {
      (function (save, el) {
        save.addEventListener('click', function () {
          var data = '',
            tableData = [],
            rows = el.querySelectorAll('tr:not(.em-tableProg)');

          for (var row = 0; row < rows.length; row++) {
            var rowData = [];
            var c = rows[row].querySelectorAll('th, td');

            for (var i = 0; i < c.length; i++) {
              rowData.push('"' + c[i].innerText + '"');
            }

            tableData.push(rowData.join(','));
          }

          data += tableData.join('\n');
          var a = document.createElement('a');
          a.href = URL.createObjectURL(
            new Blob([data], {
              type: 'text/csv',
            }),
          );
          a.setAttribute('download', 'data.csv');
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
        });
      })(save, el); // reload
    }
    var reload = el.querySelector('.em-tableReload');

    if (reload) {
      (function (reload, el) {
        reload.addEventListener('click', function () {
          el.innerHTML = '<div class="loader"></div>';
          table(el);
        });
      })(reload, el);
    }

    var autoReload = el.querySelector('input.switch') ? el.querySelector('input.switch').parentElement : null;
    var reloadTimer;
    if (autoReload) {
      /* auto reload */
      (function (autoReload, el) {
        var load = function () {
            el.style.opacity = '0.5';
            table(el, undefined, true);
          },
          counter = 4,
          counting = function () {
            reloadTimer = window.setTimeout(countDown, 1000);
          },
          countDown = function () {
            counter = counter -= 1;
            if (counter < 1) {
              window.clearTimeout(reloadTimer);
              reloadTimer = null;
              load();
            } else {
              reloadTimer = window.setTimeout(countDown, 1000);
            }
          },
          input = autoReload.querySelector('input');

        if (enableReload) {
          input.checked = true;
          counter = 4;
          counting();
        } else {
          if (typeof reloadTimer != 'undefined') {
            window.clearTimeout(reloadTimer);
          }
        }

        input.addEventListener('click', function () {
          if (input.checked) {
            counting();
          } else {
            autoReload.removeAttribute('checked');
            input.checked = false;
            window.clearTimeout(reloadTimer);
          }
        });
      })(autoReload, el); // sort
    }
    var th = el.querySelectorAll('tr:not(.em-tableProg) th');
    function my_tr_clic(h, el) {
      h.addEventListener('click', function () {
        var table = el.querySelector('tbody'),
          r = Array.from(table.querySelectorAll('tr')).sort(
            comparer(index(h) - 1),
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

    var otherPages = el.querySelectorAll('.em-tablePagItem:not(.is-disabled)');

    function my_click_loader(h, el) {
      h.addEventListener('click', function () {
        autoReload.removeAttribute('checked');
        window.clearTimeout(reloadTimer);
        el.style.height = el.clientHeight + 'px';
        el.innerHTML = '<div class="loader"></div>';
        table(this, el);
      });
    }

    for (q = 0; q < otherPages.length; q++) {
      new my_click_loader(otherPages[q], el);
    }

    // sort
    if (el.querySelector('.em-tableSort select')) {
      el.querySelector('.em-tableSort select').addEventListener(
        'change',
        function (e) {
          var option = e.target.options[e.target.selectedIndex];
          if (option.hasAttribute('data-src')) {
            // set height so there is no resize
            autoReload.removeAttribute('checked');

            window.clearTimeout(reloadTimer);
            el.style.height = el.clientHeight + 'px';
            el.innerHTML = '<div class="loader"></div>';
            table(option, el);
          }
        },
      );
    }
  }

  var comparer = function comparer(index) {
      return function (a, b) {
        var valA = getCellValue(a, index).replace('$', ''),
          valB = getCellValue(b, index).replace('$', '');
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
      return row.getElementsByTagName('td')[index].textContent;
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
})((window.rhcTable = window.rhcTable || {}));
