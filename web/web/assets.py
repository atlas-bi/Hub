"""Web assets.

CSS assets are compiles from scss to css with gulp. Webassets combines the output css and versions them nicely.
"""

from flask_assets import Bundle
from webassets.filter import register_filter
from webassets_rollup import Rollup

from web import web_assets

register_filter(Rollup)  # type: ignore[no-untyped-call]


# font
css = Bundle(
    "./css/base.css",
    filters="rcssmin",
    output="css/base.min.css",
)
web_assets.register("css", css)

js = Bundle(
    # codemirror 5 comes from npm (see package.json). only the modes and addons we use are included.
    "../../node_modules/codemirror/lib/codemirror.js",
    "../../node_modules/codemirror/mode/sql/sql.js",
    "../../node_modules/codemirror/mode/python/python.js",
    "../../node_modules/codemirror/addon/edit/matchbrackets.js",
    "../../node_modules/codemirror/addon/scroll/simplescrollbars.js",
    filters=("uglifyjs"),
    output="js/codemirror.min.js",
)
web_assets.register("codemirror", js)

js = Bundle(
    # "./lib/flatpickr/flatpickr.js",
    "./js/base.js",
    "./js/ajax.js",
    # prismjs comes from npm (see package.json). only the languages we highlight are included.
    "../../node_modules/prismjs/components/prism-core.js",
    "../../node_modules/prismjs/components/prism-markup.js",
    "../../node_modules/prismjs/components/prism-css.js",
    "../../node_modules/prismjs/components/prism-clike.js",
    "../../node_modules/prismjs/components/prism-javascript.js",
    "../../node_modules/prismjs/components/prism-ini.js",
    "../../node_modules/prismjs/components/prism-python.js",
    "../../node_modules/prismjs/components/prism-sql.js",
    "../../node_modules/prismjs/components/prism-toml.js",
    "../../node_modules/prismjs/plugins/line-numbers/prism-line-numbers.js",
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
