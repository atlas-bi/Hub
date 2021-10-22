(function (rhcTable, $, undefined) {
  var tables = document.getElementsByClassName("em-ajaxLogs");

  for (var x = 0; x < tables.length; x++) {
    if (tables[x].hasAttribute("data-src")) table(tables[x]);
  }
var log_id_min=0,
    log_id_max=0;

function debounce(func, wait, immediate) {
  var timeout;
  return function() {
    var context = this, args = arguments;
    var later = function() {
      timeout = null;
      if (!immediate) func.apply(context, args);
    };
    var callNow = immediate && !timeout;
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    if (callNow) func.apply(context, args);
  };
};

  function table(el) {
    if (typeof dest == "undefined") dest = el;
    if (typeof reload == "undefined") reload = false;
    var q = new XMLHttpRequest();
    q.open(
      "get",
      el.getAttribute("data-src"), //+ "&v=" + new Date().getTime(),
      true
    );
    q.send();

    q.onload = function () {
      try {
        loadLogs(JSON.parse(this.responseText), dest,el.getAttribute("data-src"));
        dest.style.removeProperty("opacity");
      } catch (e) {
      console.log(e)
      }
    };
  }

  function loadLogs(arr, el, url) {
    var box = document.createElement('div');
    box.classList.add(
      "box",
      "has-background-grey-dark",
      "has-text-light",
      "is-size-6-5",
      "px-0",
    );
    box.setAttribute("style","height:600px;")

    var container = document.createElement("div");
    container.classList.add("container", "scroll-bottom", "light");
    container.setAttribute("ss-container","ss-container")
    container.setAttribute("style","height:100%")

    var scroll_ajax=null;
    container.addEventListener('scroll',debounce(function(){

      // if within x of top and no "at-start" class, then get more logs.
      if(container.querySelector('.ss-content').scrollTop < 500 && !container.classList.contains('at-start')){
        // add loader
        var loader = container.querySelector('div.loader');

        if(!loader){
          loader = document.createElement('div')
          loader.classList.add('loader','m-5');
          loader.setAttribute("style", "position:absolute;top:-30px;left:-13px;")
          container.insertBefore(loader, container.firstChild)
        }

        // get logs

        if(scroll_ajax){scroll_ajax.abort()}
        scroll_ajax = new XMLHttpRequest();

        scroll_ajax.open(
          "get",
          url + "?lt="+log_id_min,
          true
        );
        scroll_ajax.send();

        scroll_ajax.onload = function() {

         try {
              appendLogs(JSON.parse(this.responseText), container);
              if(loader !== undefined && loader.parentElement) {loader.parentElement.removeChild(loader);}
            } catch (e) {
            console.log(e)
            }
      }}
    },10))
    box.appendChild(container);
    el.innerHTML="";
    el.appendChild(box);

    appendLogs(arr, container);

    // trigger scroll
    document.dispatchEvent(
      new CustomEvent("ss-load", {
        cancelable: true,
        detail: {
          el: container,
        },
      })
    );


    /* auto reload */
    (function (container, url) {
      var q = null;
      var reloadTimer,
        get_new_logs = function () {
          if(q){q.abort()}

          // get the latest log row and reload from there.
          // we will reload the full last block.. as last
          // row is sometimes dynamic.

          last_id = container.querySelector('nav.log-group:last-of-type div[log_id]').getAttribute('log_id')
          q = new XMLHttpRequest();
          q.open(
            "get",
            url + "?gte="+last_id,
            true
          );
          q.send();

          q.onload = function () {
            try {
              appendLogs(JSON.parse(this.responseText), container);
            } catch (e) {
            console.log(e)
            }
          };
            reloadTimer = window.setTimeout(get_new_logs, 2000);
          };
        window.setTimeout(get_new_logs, 2000);

    })(container, url);
  }

  function appendLogs(arr, container){

    var   empty_msg = "No data to show.",
      current_date = new Date()
        .toLocaleString()
        .replace(",", "")
        //.replace(/:\d\d\s/, " ");

    // get total rows
    for (x = 0; x < arr.length; x++) {
      if (arr[x].total || arr[x].total == 0) {
        total = arr[x].total;
        arr.splice(x, 1);
        break;
      }
    }

    for (x = 0; x < arr.length; x++) {
      if (arr[x].empty_msg) {
        empty_msg = arr[x].empty_msg;
        arr.splice(x, 1);
        break;
      }
    }

    // what to do if empty?!

    arr = arr.reverse();

    // get current log id max and min
    log_id_els = Array.prototype.slice.call(
     container.querySelectorAll("[log_id]")
    );

    for(var e=0;e<log_id_els.length;e++){
      var log_id = log_id_els[e].getAttribute("log_id");

      log_id_max = Math.max(parseInt(log_id), log_id_max);

      log_id_min = log_id_min == 0 ? parseInt(log_id)   :Math.min(parseInt(log_id), log_id_min);

    }

    // build split array of logs from json. group results by "status", "job_id"
    var group = [];
    var section = {};
    var job_id = "", status="";


   for (x = 0; x < arr.length; x++) {
      var v = arr[x];
      // if the log exists, then update it.
      var existing_log = container.querySelector('div[log_id="'+v["log_id"]+'"]');
      if(existing_log){
        existing_log.innerHTML=v["message"];
      }
      else{
        if(status==v["status"] && job_id==v["job_id"]){
          section["message"].push({"message": v["message"], "date":v["date"], "log_id": v["log_id"]})
          section["class"] = v["class"] ? v["class"] !== "" : v["class"];
        }else {

          section={}
          // create new section
          section["status"]=v["status"] || "";
          section["job_id"]=v["job_id"];
          section["class"]=v["class"];
          section["message"] = [{"message": v["message"], "date":v["date"], "log_id": v["log_id"]}]
          status=v["status"];
          job_id=v["job_id"];
          if(v["log_id"] < log_id_min){
            section["location"]="before";
            if(Object.keys(section).length){
            group.unshift(section)
          }
          }else{
            section["location"]="after";
            if(Object.keys(section).length){
            group.push(section)
          }
          }

        };
      }
    }


    var updated = container.querySelector('.last-load-date')
    if (updated == undefined){
      updated = document.createElement("div")
      updated.classList.add(
        "has-text-weight-light",
        "has-text-grey",
        "last-load-date",
        "mb-1",
        "mx-5"
      )
      container.appendChild(updated);
    }
    updated.innerHTML = current_date


    // group results by "status", "job_id"
    var job_id = "", status="", nav, left, right;

    for (var x = 0; x < group.length; x++) {


      var level = document.createElement('nav');
      level.classList.add(
        "level",
        "mb-1",
        "mx-3",
        "is-align-items-start"
      );
      var level_item = document.createElement("div");
      level_item.classList.add("level-item")

      var icon_wrapper = document.createElement("span");
      icon_wrapper.classList.add("icon","mt-1", "is-small", "is-block");

      var icon = document.createElement("i");
      icon.classList.add("fas");


      nav = level.cloneNode();
      nav.classList.add("log-group");
      nav.addEventListener("click", function(e){
        collapses=this.querySelectorAll('div[log_id]');
        var angle = this.querySelector('.icon i.fa-angle-right, .icon i.fa-angle-down')

        if(angle.classList.contains('fa-angle-right')){
          for (var c=0;c<collapses.length;c++){
          collapse=collapses[c]
            collapse.classList.remove('is-collapsed');
          }

          angle.classList.remove('fa-angle-right')
          angle.classList.add('fa-angle-down');

        } else {
          for (var c=0;c<collapses.length;c++){
            collapse=collapses[c]
              collapse.classList.add('is-collapsed');
            }
            angle.classList.remove('fa-angle-down')
            angle.classList.add('fa-angle-right');
          }
        })

        if (group[x]["location"] == "before"){
           updated.parentElement.insertBefore(nav, updated.parentElement.firstChild)
        } else {
          updated.parentElement.insertBefore(nav, updated);
        }
      left = document.createElement('div');
      left.classList.add(
        "level-left",
        "is-flex-shrink-1",
        "is-flex-grow-1",
        "is-align-items-start"
      );
      nav.appendChild(left)

      // chevron
      var chevron_level = level_item.cloneNode();
      var chevron_wrapper = icon_wrapper.cloneNode();
      var chevron = icon.cloneNode();

      chevron.classList.add("fa-angle-right", "mr-5");
      chevron_level.appendChild(chevron_wrapper)
      chevron_wrapper.appendChild(chevron)
      left.appendChild(chevron_level)

      // status icon
      var status_icon_level = level_item.cloneNode();
      var status_icon_wrapper = icon_wrapper.cloneNode();
      var status_icon = icon.cloneNode();

      if(group[x]["class"]=="error"){
        status_icon.classList.add("has-text-danger");
        status_icon.classList.add("fa-times-circle")
      } else {
        status_icon.classList.add("has-text-grey-light");
        status_icon.classList.add("fa-check-circle")
      }

      status_icon_level.appendChild(status_icon_wrapper)
      status_icon_wrapper.appendChild(status_icon)
      left.appendChild(status_icon_level)

      // status
      var status_box = level_item.cloneNode();
      status_box.classList.add("is-justify-content-left")
      status_box.setAttribute('style',"min-width:110px;")
      status_box.innerHTML=group[x]["status"]
      left.appendChild(status_box);

      // message
      var message = level_item.cloneNode();
      message.classList.add("is-flex-grow-1", "is-flex-shrink-1")

      var message_container = document.createElement('div')
      message_container.classList.add('container');
      message.appendChild(message_container)
      for(var m=0; m< group[x]["message"].length; m++){

        var message_nav = level.cloneNode()

        var message_right = document.createElement('div');
        message_right.classList.add(
          "level-right",
          "is-align-items-start",
          "ml-3"
        );

        var message_left = document.createElement('div');
        message_left.classList.add(
          "level-right",
          "is-align-items-start",
          "is-flex-grow-1",
          "is-flex-shrink-1"
        );

        text = level_item.cloneNode();
        text.classList.add("is-flex-grow-1", "is-flex-shrink-1", 'is-justify-content-start', 'is-family-code','is-collapsed');
        text.setAttribute("style","white-space:pre-wrap;word-break:break-word");
        text.innerHTML = group[x]["message"][m]["message"];
        text.setAttribute("log_id",group[x]["message"][m]["log_id"]);

        date = level_item.cloneNode();
        date.innerHTML = group[x]["job_id"] + " " + group[x]["message"][m]["date"]

        message_left.appendChild(text)
        message_nav.appendChild(message_left)
        message_right.appendChild(date)
        message_nav.appendChild(message_right)
        message_container.appendChild(message_nav)

      }

      left.appendChild(message);
      // scroll to bottom if has attribute ss-bottom
      if (container.hasAttribute("ss-bottom")){
        scroller = container.querySelector('.ss-content');
          scroller.scroll({
            top: scroller.scrollHeight,
            behavior: 'smooth'
          });
        }
      }
  }

})((window.rhcTable = window.rhcTable || {}));
