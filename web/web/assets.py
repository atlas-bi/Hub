"""Web assets.

CSS assets are compiles from scss to css with gulp. Webassets combines the output css and versions them nicely.
"""


from flask_assets import Bundle

from web import web_assets

# font
css = Bundle(
    "./css/base.css",
    filters="rcssmin",
    output="css/base.min.css",
)
web_assets.register("css", css)


js = Bundle(
    "./js_build/scripts.js",
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
