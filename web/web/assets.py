"""Web assets.

CSS assets are compiles from scss to css with gulp. Webassets combines the output css and versions them nicely.
"""


from flask_assets import Bundle

from web import web_assets

# font
css = Bundle(
    "./css/base.css",
    "./lib/codemirror/codemirror.css",
    "./lib/codemirror/ttcn.css",
    "./lib/codemirror/simplescrollbars.css",
    "./lib/scroll/scroll.css",
    "./lib/prism/prism.css",
    "./lib/table/table.css",
    "./lib/prism/prism_line_numbers.css",
    "./lib/flatpickr/flatpickr.css",
    "./lib/table/table.css",
    filters="rcssmin",
    output="css/base.min.css",
)
web_assets.register("css", css)


js = Bundle(
    "./lib/codemirror/codemirror.js",
    "./lib/codemirror/gfm.js",
    "./lib/codemirror/overlay.js",
    "./lib/codemirror/sql.js",
    "./lib/codemirror/python.js",
    "./lib/codemirror/matchbrackets.js",
    "./lib/codemirror/simplescrollbars.js",
    "./lib/flatpickr/flatpickr.js",
    "./js/base.js",
    "./js/ajax.js",
    "./lib/prism/prism.js",
    "./lib/prism/prism_line_numbers.js",
    "./js/task.js",
    "./lib/table/table.js",
    "./lib/table/logs.js",
    "./lib/scroll/scroll.js",
    "./js/password.js",
    "./js/project.js",
    "./js/tabs.js",
    "./js/executor_status.js",
    "./js/flashes.js",
    "./js/functions.js",
    "./js/connection.js",
    filters="jsmin",
    output="js/base.min.js",
)
web_assets.register("js", js)

js = Bundle(
    "./js/search.js",
    filters="jsmin",
    output="js/demo.min.js",
)
web_assets.register("js_search", js)
