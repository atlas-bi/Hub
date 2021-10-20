
document.addEventListener('click', function(e) {
  if(e.target.closest('.notification .delete')){
    el = e.target.closest('.notification');
    el.parentNode.removeChild(el);
  }

})
