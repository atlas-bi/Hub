(function () {
  String.prototype.format = function () {
    var i = 0,
      args = arguments;
    return this.replace(/{}/g, function () {
      return typeof args[i] != 'undefined' ? args[i++] : '';
    });
  };

  var d = document,
    task_id = d.querySelector('h1.title[task_id]');

  function taskHello(task_id) {
    if (window.ajaxOn === true) {
      var q = new XMLHttpRequest();
      q.open('get', '/task/{}/hello'.format(task_id), true);
      q.send();
      q.onload = function () {
        var data = JSON.parse(q.responseText);
        for (var key in data) {
          var els = Array.prototype.slice.call(
            d.querySelectorAll('.hello_{}'.format(key)),
          );

          for (var x = 0; x < els.length; x++) {
            els[x].innerHTML = data[key];

            if (key === 'status') {
              els[x].classList.remove('is-danger');
              els[x].classList.remove('is-success');
              els[x].classList.remove('is-warning');
              switch (data[key].split(' ')[0]) {
                case 'Running':
                  els[x].classList.add('is-warning');
                  break;
                case 'Completed':
                  els[x].classList.add('is-success');
                  break;
                case 'Errored':
                  els[x].classList.add('is-danger');
                  break;
              }
            }
          }
        }
      };
    }
  }
  if (task_id) {
    setInterval(function () {
      taskHello(task_id.getAttribute('task_id'));
    }, 3000);
  }
})();
