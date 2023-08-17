(function () {
  // on click of checkbox change input value
  var d = document,
    l;

  var myTextArea = d.querySelector('textarea[name="sourceCode"]');
  if (myTextArea) {
    var mySourceCodeMirror = CodeMirror.fromTextArea(myTextArea, {
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
  var myProcessingTextArea = d.querySelector('textarea[name="processingCode"]');
  if (myProcessingTextArea) {
    var myProcessingCodeMirror = CodeMirror.fromTextArea(myProcessingTextArea, {
      theme: 'ttcn',
      mode: 'python',
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
  var projectGlobalParams = d.querySelector('textarea[name="globalParams"]');
  if (projectGlobalParams) {
    // eslint-disable-next-line no-undef,no-unused-vars
    var myprojectGlobalParams = CodeMirror.fromTextArea(projectGlobalParams, {
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
  var projectTaskParams = d.querySelector('textarea[name="taskParams"]');
  if (projectTaskParams) {
    // eslint-disable-next-line no-undef,no-unused-vars
    var myprojectTaskParams = CodeMirror.fromTextArea(projectTaskParams, {
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

  d.addEventListener('click', function (e) {
    if (e.target.closest('[type="checkbox"]')) {
      var checkbox = e.target.closest('[type="checkbox"]'),
        input = checkbox.parentElement.querySelector('input[type="hidden"]'),
        visible_target = document.querySelector(
          '.' + checkbox.getAttribute('data-target'),
        );

      if (checkbox.getAttribute('checked') === 'checked') {
        checkbox.removeAttribute('checked');
        if (input) input.value = 0;
        if (visible_target) {
          visible_target.style.display = 'None';
        }
      } else {
        checkbox.setAttribute('checked', 'checked');
        if (input) input.value = 1;
        if (visible_target) {
          visible_target.style.removeProperty('display');
        }
      }
    }
  });

  d.addEventListener('change', function (e) {
    var t, p, q;
    if (e.target.closest('select[name="smb_destination"]')) {
      t = e.target.closest('select[name="smb_destination"]');
      if (t.value == 'none') {
        t.parentElement.querySelector(
          '.' + t.getAttribute('data-smb'),
        ).innerHTML = '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/smb-dest?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = document.querySelector('.' + t.getAttribute('data-smb'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="sftp_destination"]')) {
      t = e.target.closest('select[name="sftp_destination"]');
      if (t.value == 'none') {
        document.querySelector('.' + t.getAttribute('data-sftp')).innerHTML =
          '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/sftp-dest?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = document.querySelector('.' + t.getAttribute('data-sftp'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="gpg_file"]')) {
      t = e.target.closest('select[name="gpg_file"]');
      if (t.value == 'none') {
        document.querySelector('.' + t.getAttribute('data-gpg')).innerHTML = '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/gpg-file?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = document.querySelector('.' + t.getAttribute('data-gpg'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="sftp_processing"]')) {
      t = e.target.closest('select[name="sftp_processing"]');
      if (t.value == 'none') {
        document.querySelector('.' + t.getAttribute('data-sftp')).innerHTML =
          '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/sftp-processing?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = document.querySelector('.' + t.getAttribute('data-sftp'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="sftp_source"]')) {
      t = e.target.closest('select[name="sftp_source"]');
      if (t.value == 'none') {
        document.querySelector('.' + t.getAttribute('data-sftp')).innerHTML =
          '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/sftp-source?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = document.querySelector('.' + t.getAttribute('data-sftp'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="sftp_query"]')) {
      t = e.target.closest('select[name="sftp_query"]');
      if (t.value == 'none') {
        document.querySelector('.' + t.getAttribute('data-sftp')).innerHTML =
          '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/sftp-query?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = document.querySelector('.' + t.getAttribute('data-sftp'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="ftp_source"]')) {
      t = e.target.closest('select[name="ftp_source"]');
      if (t.value == 'none') {
        document.querySelector('.' + t.getAttribute('data-ftp')).innerHTML = '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/ftp-source?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = document.querySelector('.' + t.getAttribute('data-ftp'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="ssh_source"]')) {
      t = e.target.closest('select[name="ssh_source"]');
      if (t.value == 'none') {
        document.querySelector('.' + t.getAttribute('data-ssh')).innerHTML = '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/ssh-source?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = document.querySelector('.' + t.getAttribute('data-ssh'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="ftp_processing"]')) {
      t = e.target.closest('select[name="ftp_processing"]');
      if (t.value == 'none') {
        document.querySelector('.' + t.getAttribute('data-ftp')).innerHTML = '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/ftp-processing?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = document.querySelector('.' + t.getAttribute('data-ftp'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="ftp_destination"]')) {
      t = e.target.closest('select[name="ftp_destination"]');
      if (t.value == 'none') {
        document.querySelector('.' + t.getAttribute('data-ftp')).innerHTML = '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/ftp-dest?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = document.querySelector('.' + t.getAttribute('data-ftp'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="ftp_query"]')) {
      t = e.target.closest('select[name="ftp_query"]');
      if (t.value == 'none') {
        document.querySelector('.' + t.getAttribute('data-ftp')).innerHTML = '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/ftp-query?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = document.querySelector('.' + t.getAttribute('data-ftp'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="smb_source"]')) {
      t = e.target.closest('select[name="smb_source"]');
      if (t.value == 'none') {
        document.querySelector('.' + t.getAttribute('data-smb')).innerHTML = '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/smb-source?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = document.querySelector('.' + t.getAttribute('data-smb'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="smb_processing"]')) {
      t = e.target.closest('select[name="smb_processing"]');
      if (t.value == 'none') {
        document.querySelector('.' + t.getAttribute('data-smb')).innerHTML = '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/smb-processing?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = document.querySelector('.' + t.getAttribute('data-smb'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="smb_query"]')) {
      t = e.target.closest('select[name="smb_query"]');
      if (t.value == 'none') {
        document.querySelector('.' + t.getAttribute('data-smb')).innerHTML = '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/smb-query?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = document.querySelector('.' + t.getAttribute('data-smb'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="database_source"]')) {
      t = e.target.closest('select[name="database_source"]');
      if (t.value == 'none') {
        document.querySelector(
          '.' + t.getAttribute('data-database'),
        ).innerHTML = '';
        return;
      }
      q = new XMLHttpRequest();
      q.open('get', '/task/database-source?org=' + t.value, true);
      q.setRequestHeader(
        'Content-Type',
        'application/x-www-form-urlencoded; charset=UTF-8',
      );
      q.setRequestHeader('Ajax', 'True');
      q.send();
      q.onload = function () {
        var p = t
          .closest('body')
          .querySelector('.' + t.getAttribute('data-database'));
        p.innerHTML = q.responseText;

        var s = p.querySelector('script');
        if (s) {
          l = document.createElement('script');
          l.innerHTML = s.innerText;
          document.querySelector('body').appendChild(l);
        }
        if (t.closest('.clps-o')) {
          t.closest('.clps-o').dispatchEvent(
            new Event('change', {
              bubbles: true,
            }),
          );
        }
      };
    } else if (e.target.closest('select[name="sourceType"]')) {
      t = e.target.closest('select[name="sourceType"]');

      p = t.closest('body');
      p.querySelector('.task-sourceDatabase').style.display = 'none';
      p.querySelector('.task-sourceSmb').style.display = 'none';
      p.querySelector('.task-sourceSftp').style.display = 'none';
      p.querySelector('.task-sourceFtp').style.display = 'none';
      p.querySelector('.task-query-location').style.display = 'none';
      p.querySelector('.task-sourceSsh').style.display = 'none';
      p.querySelector('.task-query-headers').style.display = 'none';

      if (t.value === '1') {
        p.querySelector('.task-sourceDatabase').style.removeProperty('display');
        p.querySelector('.task-query-location').style.removeProperty('display');
        p.querySelector('.task-query-headers').style.removeProperty('display');
      } else if (t.value === '2') {
        p.querySelector('.task-sourceSmb').style.removeProperty('display');
      } else if (t.value === '3') {
        p.querySelector('.task-sourceSftp').style.removeProperty('display');
      } else if (t.value === '4') {
        p.querySelector('.task-sourceFtp').style.removeProperty('display');
      } else if (t.value === '5') {
        // nothing
      } else if (t.value === '6') {
        p.querySelector('.task-sourceSsh').style.removeProperty('display');
        p.querySelector('.task-query-location').style.removeProperty('display');
      }
    } else if (e.target.closest('select[name="sourceQueryType"]')) {
      t = e.target.closest('select[name="sourceQueryType"]');
      p = t.closest('body');

      p.querySelector('.task-sourceGit').style.display = 'none';      
      p.querySelector('.task-sourceDevops').style.display = 'none';
      p.querySelector('.task-sourceFtpQuery').style.display = 'none';
      p.querySelector('.task-sourceSmbQuery').style.display = 'none';
      p.querySelector('.task-sourceSftpQuery').style.display = 'none';
      p.querySelector('.task-sourceURL').style.display = 'none';
      p.querySelector('.task-sourceCode').style.display = 'none';

      if (t.value === '1') {
        p.querySelector('.task-sourceGit').style.removeProperty('display');
      } else if (t.value === '2') {
        p.querySelector('.task-sourceSmbQuery').style.removeProperty('display');
      } else if (t.value === '3') {
        p.querySelector('.task-sourceURL').style.removeProperty('display');
      } else if (t.value === '4') {
        p.querySelector('.task-sourceCode').style.removeProperty('display');
      } else if (t.value === '5') {
        p.querySelector('.task-sourceSftpQuery').style.removeProperty(
          'display',
        );
      } else if (t.value === '6') {
        p.querySelector('.task-sourceFtpQuery').style.removeProperty('display');
      } else if (t.value === '7') {
        p.querySelector('.task-sourceDevops').style.removeProperty('display');
      }
    } else if (e.target.closest('select[name="processingType"]')) {
      t = e.target.closest('select[name="processingType"]');
      p = t.closest('body');

      p.querySelector('.task-processingGit').style.display = 'none';
      p.querySelector('.task-processingDevops').style.display = 'none';
      p.querySelector('.task-processingFtp').style.display = 'none';
      p.querySelector('.task-processingSmb').style.display = 'none';
      p.querySelector('.task-processingSftp').style.display = 'none';
      p.querySelector('.task-processingUrl').style.display = 'none';
      p.querySelector('.task-processingCode').style.display = 'none';
      p.querySelector('.task-processingCommand').style.removeProperty(
        'display',
      );

      if (t.value === '1') {
        p.querySelector('.task-processingSmb').style.removeProperty('display');
      } else if (t.value === '2') {
        p.querySelector('.task-processingSftp').style.removeProperty('display');
      } else if (t.value === '3') {
        p.querySelector('.task-processingFtp').style.removeProperty('display');
      } else if (t.value === '4') {
        p.querySelector('.task-processingGit').style.removeProperty('display');
      } else if (t.value === '5') {
        p.querySelector('.task-processingUrl').style.removeProperty('display');
      } else if (t.value === '6') {
        p.querySelector('.task-processingCode').style.removeProperty('display');
        p.querySelector('.task-processingCommand').style.display = 'none';
      } else if (t.value === '7') {
        p.querySelector('.task-processingDevops').style.removeProperty('display');
      } else {
        p.querySelector('.task-processingCommand').style.display = 'none';
      }
    } else if (e.target.closest('select[name="fileType"]')) {
      t = e.target.closest('select[name="fileType"]');
      p = t.closest('body');
      p.querySelector('.task-delimiter').style.display = 'none';

      if (t.value === '2' || t.value === '4') {
        p.querySelector('.task-delimiter').style.removeProperty('display');
      }
    }
    if (typeof mySourceCodeMirror != 'undefined') mySourceCodeMirror.refresh();
    if (typeof myProcessingCodeMirror != 'undefined')
      myProcessingCodeMirror.refresh();
  });

  try {
    flatpickr('#project_ooff_date', {
      enableTime: true,
      dateFormat: 'Y-m-d H:i',
      weekNumbers: true,
      time_24hr: true,
    });
    flatpickr('#project_intv_edate', {
      enableTime: true,
      dateFormat: 'Y-m-d H:i',
      weekNumbers: true,
      time_24hr: true,
    });
    flatpickr('#project_intv_sdate', {
      enableTime: true,
      dateFormat: 'Y-m-d H:i',
      weekNumbers: true,
      time_24hr: true,
    });
    flatpickr('#project_cron_edate', {
      enableTime: true,
      dateFormat: 'Y-m-d H:i',
      weekNumbers: true,
      time_24hr: true,
    });
    flatpickr('#project_cron_sdate', {
      enableTime: true,
      dateFormat: 'Y-m-d H:i',
      weekNumbers: true,
      time_24hr: true,
    });
  } catch (e) {
    // nothing
  }
})();
