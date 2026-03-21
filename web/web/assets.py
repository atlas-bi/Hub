"""Web assets.

CSS assets are compiles from scss to css with gulp. Webassets combines the output css and versions them nicely.
"""

from flask_assets import Bundle
from webassets.filter import register_filter
from webassets_rollup import Rollup

from web import web_assets

register_filter(Rollup)


# font
css = Bundle(
    "./css/base.css",
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
    filters=("uglifyjs"),
    output="js/codemirror.min.js",
)
web_assets.register("codemirror", js)

js = Bundle(
    # "./lib/flatpickr/flatpickr.js",
    "./js/base.js",
    "./js/ajax.js",
    "./lib/prism/prism.js",
    "./lib/prism/prism_line_numbers.js",
    "./js/task.js",
    "./js/password.js",
    "./js/project.js",
    "./js/tabs.js",
    "./js/executor_status.js",
    "./js/flashes.js",
    "./js/functions.js",
    "./js/connection.js",
    filters=("rollup", "uglifyjs"),
    output="js/base.min.js",
)
web_assets.register("js", js)

js = Bundle(
    "./lib/scroll/scroll.js",
    filters=("uglifyjs",),
    output="js/scroll.min.js",
)
web_assets.register("scroll", js)

js = Bundle(
    "./lib/flatpickr/flatpickr.js",
    filters=("uglifyjs"),
    output="js/flatpickr.min.js",
)
web_assets.register("js_flatpickr", js)
js = Bundle(
    "./lib/table/table.js",
    "./lib/table/logs.js",
    filters=("uglifyjs"),
    output="js/tables.min.js",
)
web_assets.register("js_tables", js)

js = Bundle(
    "./js/search.js",
    filters=("rollup", "uglifyjs"),
    output="js/search.min.js",
)
web_assets.register("js_search", js)
