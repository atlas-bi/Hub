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

  document.addEventListener('click', function (element) {
    // add a parameter input
    if (element.target.closest('button.new-parameter')) {
      document.querySelector('#new-parameters').insertAdjacentHTML(
        'beforeend',
        `<div class="field is-horizontal new-parameter">
                    <div class="field-body is-align-items-center">
                        <div class="field">
                            <p class="control is-expanded">
                                <input name="param-key" class="input" type="text" placeholder="name">
                            </p>
                        </div>
                        <div class="field has-addons">
                            <p class="control is-expanded">
                                <input name="param-value" class="input" type="text" placeholder="***">
                            </p>
                            <div class="control">
                                <a class="button toggle-pass "data-target="password">
                                    <span class="icon">
                                        <i class="fas fa-eye-slash"></i>
                                        <input name="param-sensitive" type="hidden"/>
                                    </span>
                                </a>
                            </div>
                        </div>
                        <p class="control mb-1 ">
                            <button type="button" class="delete is-large new-remove-parameter"></button>
                        </p>
                    </div>
                </div>`,
      );
    } else if (element.target.closest('button.new-remove-parameter')) {
      element.target.closest('.new-parameter').remove();
    } else if (element.target.closest('button.show-params')) {
      var prev = document.querySelector('.param-preview');
      var real = document.querySelector('.param-real');

      if (prev.classList.contains('is-hidden')) {
        prev.classList.remove('is-hidden');
      } else {
        prev.classList.add('is-hidden');
      }

      if (real.classList.contains('is-hidden')) {
        real.classList.remove('is-hidden');
      } else {
        real.classList.add('is-hidden');
      }
    }
  });
})();
