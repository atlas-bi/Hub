(function () {
  var myTimeout = 1000;
  function executorStatus() {
    if (window.ajaxOn == true) {
      // only do ajax if enabled.
      var q = new XMLHttpRequest();
      q.open('get', '/executor/status', true);
      q.send();

      q.onload = function () {
        var jobs = JSON.parse(this.responseText);

        if (Object.keys(jobs).length > 0) {
          var box = document.getElementById('executor-status'),
            message;

          if (box == undefined) {
            box = document.createElement('div');
            box.setAttribute('id', 'executor-status');
            box.classList.add('notification', 'is-warning');
            var content = document.getElementById('content');
            content.insertBefore(box, content.firstChild);

            var button = document.createElement('button');
            button.classList.add('delete');
            box.appendChild(button);

            message = document.createElement('span');
            box.appendChild(message);
          } else {
            message = box.querySelector('span');
          }

          var jobText = message.innerHTML;
          for (var key in jobs) {
            if (jobText !== '') {
              jobText += '<br />';
            }
            jobText += jobs[key];
          }

          message.innerHTML = jobText;
          // slow down check after first time
          myTimeout = 2000;
        }
      };
    }

    setTimeout(executorStatus, myTimeout);
  }

  executorStatus();
})();
