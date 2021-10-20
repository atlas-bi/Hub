(function () {
Function.prototype.debounce = function (delay) {
  var outter = this,
    timer;

  return function () {
    var inner = this,
      args = [].slice.apply(arguments);

    clearTimeout(timer);
    timer = setTimeout(function () {
      outter.apply(inner, args);
    }, delay);
  };
};
var d= document;
search_data = {};
window.addEventListener("load", function () {
  var q = new XMLHttpRequest();

  searchResultsContainer = document.getElementById("search-results");

  // if data exists in localstorage, then enable search immediately.
  if(localStorage.getItem('atlas_hub_search')){
    try{
    search_data = JSON.parse(localStorage.getItem('atlas_hub_search'));

    d.getElementById('search').addEventListener("input",  search.debounce(250));
    d.getElementById('search-form').addEventListener("submit", (e) => e.preventDefault());
    d.getElementById('search').removeAttribute("disabled");
  } catch(e){console.log(e)}
  }


  // load search data
  q.open("get", "/search", true);
  q.send();

  q.onload = function () {
    localStorage.setItem('atlas_hub_search', q.responseText);
    search_data = JSON.parse(q.responseText);

    d.getElementById('search').addEventListener("input",  search.debounce(250));
    d.getElementById('search-form').addEventListener("submit", (e) => e.preventDefault());
    d.getElementById('search').removeAttribute("disabled");

  };
});


function search(){
  searchResultsContainer.textContent = "";
  var search_text = d.getElementById('search').value;

  var regex = new RegExp(search_text.replace(" ", ".* .*"), "gmi");
  output = ""
  count = 0
  for (var key in search_data) {
    for (var subkey in search_data[key]) {
      // if we have a match
      var sMatch = search_data[key][subkey].match(regex);
      if (sMatch) {
        output +=
          '<a class="panel-block p-3 is-block" href="' + subkey +
          '"><span class="is-flex is-justify-content-space-between"><p>' +
          search_data[key][subkey].replace(regex, function (m) {
            return "<strong>" + m + "</strong>";
          }) +
         "</p><span class='tag is-light ml-3'>" + key + "</span>"
          "</span></a>";
        count += 1;
      }
    }
  }

  if (count === 0) {
    output += "<div class='m-3'>Nothing found.</div>";
  }

  searchResultsContainer.innerHTML = output;


}
})();
