(function () {
  document.addEventListener('click', function (e) {
    if (e.target.closest('.toggle-pass')) {
      var target = e.target.closest('.toggle-pass'),
        input = target.parentElement.parentElement.querySelector('input'),
        icon = target.querySelector('i.fas'),
        sensitive_input = target.querySelector('input');

      input.type = input.type === 'text' ? 'password' : 'text';
      icon.classList.remove('fa-eye', 'fa-eye-slash');

      if (input.type === 'text') {
        icon.classList.add('fa-eye-slash');
        if(sensitive_input){
            sensitive_input.value = 0;
        }
      } else {
        icon.classList.add('fa-eye');
        if(sensitive_input){
            sensitive_input.value = 1;
        }
      }
    } else if (e.target.closest('.copy-input')) {
      e.preventDefault();
      var txt = document.createElement('textarea');
      txt.value = e.target.closest('.copy-input').getAttribute('data-value');
      txt.setAttribute('readonly', '');
      txt.style = {
        position: 'absolute',
        left: '-9999px',
      };
      document.body.appendChild(txt);
      txt.select();
      document.execCommand('copy');
      document.body.removeChild(txt);
    }
  });
})();
