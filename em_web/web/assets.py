"""Web assets.

Each route in EM Web has its own css and js bundle in an effort
to keep bundle size as small as possible.

Specific css and js that is not always required can be kept in their
own bundles and imported as needed.
"""
# Extract Management 2.0
# Copyright (C) 2020  Riverside Healthcare, Kankakee, IL

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


from flask_assets import Bundle

from em_web import web_assets

# login page
css = Bundle(
    "./css/base.css", "./css/login.css", filters="rcssmin", output="css/login.min.css"
)
web_assets.register("css_login", css)

js = Bundle("./js/login.js", filters="jsmin", output="js/login.min.js")
web_assets.register("js_login", js)

# logout page
css = Bundle(
    "./css/base.css", "./css/logout.css", filters="rcssmin", output="css/logout.min.css"
)
web_assets.register("css_logout", css)

js = Bundle("./js/logout.js", filters="jsmin", output="js/logout.min.js")
web_assets.register("js_logout", js)

# demo
css = Bundle(
    "./css/demo.css",
    filters="rcssmin",
    output="css/emo.min.css",
)
web_assets.register("css_demo", css)

# error
css = Bundle(
    "./css/base.css",
    "./css/head.css",
    "./css/nav.css",
    filters="rcssmin",
    output="css/error.min.css",
)
web_assets.register("css_error", css)

# admin
css = Bundle(
    "./css/base.css",
    "./css/head.css",
    "./css/nav.css",
    "./css/input.css",
    "./css/table.css",
    filters="rcssmin",
    output="css/admin.min.css",
)
web_assets.register("css_admin", css)


js = Bundle(
    "./js/table.js",
    "./js/ajax.js",
    "./js/executor_status.js",
    "./js/flashes.js",
    filters="jsmin",
    output="js/project.min.js",
)
web_assets.register("js_admin", js)


# dashboard
css = Bundle(
    "./css/base.css",
    "./css/head.css",
    "./css/nav.css",
    "./css/table.css",
    "./css/dashboard.css",
    "./css/collapse.css",
    "./css/input.css",
    "./css/gauge.css",
    filters="rcssmin",
    output="css/dashboard.min.css",
)
web_assets.register("css_dashboard", css)

js = Bundle(
    "./js/table.js",
    "./js/ajax.js",
    "./js/collapse.js",
    "./js/dashboard.js",
    "./js/executor_status.js",
    "./js/flashes.js",
    filters="jsmin",
    output="js/dashboard.min.js",
)
web_assets.register("js_dashboard", js)

# all project
css = Bundle(
    "./css/base.css",
    "./css/head.css",
    "./css/nav.css",
    "./css/collapse.css",
    "./css/project.css",
    "./css/input.css",
    "./css/table.css",
    filters="rcssmin",
    output="css/project.min.css",
)
web_assets.register("css_project", css)

js = Bundle(
    "./js/collapse.js",
    "./js/table.js",
    "./js/executor_status.js",
    "./js/flashes.js",
    filters="jsmin",
    output="js/project.min.js",
)
web_assets.register("js_project", js)

# new project
css = Bundle(
    "./css/base.css",
    "./css/head.css",
    "./css/nav.css",
    "./css/collapse.css",
    "./css/project.css",
    "./css/input.css",
    "./lib/flatpickr/flatpickr.css",
    "./lib/codemirror/codemirror.css",
    "./lib/codemirror/nord.css",
    "./lib/codemirror/simplescrollbars.css",
    filters="rcssmin",
    output="css/project_new.min.css",
)
web_assets.register("css_project_new", css)

js = Bundle(
    "./lib/codemirror/codemirror.js",
    "./lib/codemirror/gfm.js",
    "./lib/codemirror/overlay.js",
    "./lib/codemirror/sql.js",
    "./lib/codemirror/python.js",
    "./lib/codemirror/matchbrackets.js",
    "./lib/codemirror/simplescrollbars.js",
    "./lib/flatpickr/flatpickr.js",
    "./js/functions.js",
    "./js/project.js",
    "./js/collapse.js",
    "./js/password.js",
    "./js/executor_status.js",
    "./js/flashes.js",
    filters="jsmin",
    output="js/project_new.min.js",
)
web_assets.register("js_project_new", js)

# project details
css = Bundle(
    "./css/base.css",
    "./css/head.css",
    "./css/nav.css",
    "./css/table.css",
    "./css/project.css",
    "./css/input.css",
    "./css/scroll.css",
    "./lib/prism/prism.css",
    "./css/collapse.css",
    filters="rcssmin",
    output="css/project.min.css",
)
web_assets.register("css_project_details", css)

js = Bundle(
    "./js/project.js",
    "./js/table.js",
    "./js/password.js",
    "./js/scroll.js",
    "./js/ajax.js",
    "./js/collapse.js",
    "./js/executor_status.js",
    "./js/flashes.js",
    filters="jsmin",
    output="js/project.min.js",
)
web_assets.register("js_project_details", js)

js = Bundle(
    "./js/task.js",
    filters="jsmin",
    output="js/task.min.js",
)
web_assets.register("js_task", js)

# connections
css = Bundle(
    "./css/base.css",
    "./css/head.css",
    "./css/nav.css",
    "./css/collapse.css",
    "./css/table.css",
    "./css/input.css",
    "./css/connection.css",
    "./lib/codemirror/codemirror.css",
    "./lib/codemirror/nord.css",
    "./lib/codemirror/simplescrollbars.css",
    filters="rcssmin",
    output="css/project.min.css",
)
web_assets.register("css_connections", css)

js = Bundle(
    "./lib/codemirror/codemirror.js",
    "./lib/codemirror/gfm.js",
    "./lib/codemirror/overlay.js",
    "./lib/codemirror/shell.js",
    "./lib/codemirror/matchbrackets.js",
    "./lib/codemirror/simplescrollbars.js",
    "./js/functions.js",
    "./js/password.js",
    "./js/table.js",
    "./js/collapse.js",
    "./js/connection.js",
    "./js/executor_status.js",
    "./js/flashes.js",
    filters="jsmin",
    output="js/project.min.js",
)
web_assets.register("js_connections", js)


# prism
css = Bundle("./lib/prism/prism.css", filters="rcssmin", output="css/prism.min.css")
web_assets.register("css_prism", css)

js = Bundle("./lib/prism/prism.js", filters="jsmin", output="js/prism.min.js")
web_assets.register("js_prism", js)
