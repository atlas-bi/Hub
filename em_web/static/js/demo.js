var coll = document.getElementsByClassName("demo-collapse")[0];

coll.addEventListener("click", function () {
  this.classList.toggle("active");
  var content = document.getElementsByClassName("demo-collapseContent")[0];
  if (content.style.display === "block") {
    content.style.display = "none";
  } else {
    content.style.display = "block";
  }
});
