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

# font
css_font = Bundle(
    "./fonts/Inter/stylesheet.css", filters="rcssmin", output="css/inter.min.css"
)
web_assets.register("css_font", css_font)

# table
css_table = Bundle(
    "./lib/table/table.css",
    "./lib/table/table-exec.css",
    filters="rcssmin",
    output="css/table.min.css",
)
web_assets.register("css_table", css_table)

# scroll
css_scroll = Bundle(
    "./lib/scroll/scroll.css", filters="rcssmin", output="css/scroll.min.css"
)
web_assets.register("css_scroll", css_scroll)

# login page
css_login = Bundle(
    "./assets/base.scss",
    "./assets/login.scss",
    filters="pyscss,rcssmin",
    output="css/login.min.css",
)
web_assets.register("css_login", css_login)

js = Bundle("./js/login.js", filters="jsmin", output="js/login.min.js")
web_assets.register("js_login", js)

# logout page
css_logout = Bundle(
    "./assets/base.scss",
    "./assets/logout.scss",
    filters="pyscss,rcssmin",
    output="css/logout.min.css",
)
web_assets.register("css_logout", css_logout)

js = Bundle("./js/logout.js", filters="jsmin", output="js/logout.min.js")
web_assets.register("js_logout", js)

# demo
css_demo = Bundle(
    "./assets/demo.scss",
    filters="pyscss,rcssmin",
    output="css/demo.min.css",
)
web_assets.register("css_demo", css_demo)


css_error = Bundle(
    "./assets/base.scss",
    "./assets/head.scss",
    "./assets/nav.scss",
    filters="pyscss,rcssmin",
    output="css/error.min.css",
)
web_assets.register("css_error", css_error)

# admin
css_admin = Bundle(
    "./assets/base.scss",
    "./assets/head.scss",
    "./assets/nav.scss",
    "./assets/input.scss",
    filters="pyscss,rcssmin",
    output="css/admin.min.css",
)
web_assets.register("css_admin", css_admin)

js = Bundle(
    "./lib/table/table.js",
    "./js/table_cust.js",
    "./js/ajax.js",
    "./js/tabs.js",
    "./js/executor_status.js",
    "./js/flashes.js",
    filters="jsmin",
    output="js/project.min.js",
)
web_assets.register("js_admin", js)


# dashboard
css_dashboard = Bundle(
    "./assets/base.scss",
    "./assets/head.scss",
    "./assets/nav.scss",
    "./assets/dashboard.scss",
    "./assets/collapse.scss",
    "./assets/input.scss",
    "./assets/gauge.scss",
    filters="pyscss,rcssmin",
    output="css/dashboard.min.css",
)
web_assets.register("css_dashboard", css_dashboard)

js = Bundle(
    "./lib/table/table.js",
    "./js/table_cust.js",
    "./js/ajax.js",
    "./js/tabs.js",
    "./js/collapse.js",
    "./js/dashboard.js",
    "./js/executor_status.js",
    "./js/flashes.js",
    filters="jsmin",
    output="js/dashboard.min.js",
)
web_assets.register("js_dashboard", js)

# all project
css_project = Bundle(
    "./assets/base.scss",
    "./assets/head.scss",
    "./assets/nav.scss",
    "./assets/collapse.scss",
    "./assets/input.scss",
    filters="pyscss,rcssmin",
    output="css/project.min.css",
)
web_assets.register("css_project", css_project)

js = Bundle(
    "./js/collapse.js",
    "./lib/table/table.js",
    "./js/table_cust.js",
    "./js/executor_status.js",
    "./js/flashes.js",
    "./js/tabs.js",
    "./js/ajax.js",
    filters="jsmin",
    output="js/project.min.js",
)
web_assets.register("js_project", js)

# search
css_search = Bundle(
    "./assets/search.scss",
    filters="pyscss,rcssmin",
    output="css/search.min.css",
)
web_assets.register("css_search", css_search)

js = Bundle(
    "./js/search.js",
    filters="jsmin",
    output="js/search.min.js",
)
web_assets.register("js_search", js)

# new project
scss_project_new = Bundle(
    "./assets/base.scss",
    "./assets/head.scss",
    "./assets/nav.scss",
    "./assets/collapse.scss",
    "./assets/input.scss",
    filters="pyscss,rcssmin",
    output="css/project_new.min.css",
)
web_assets.register("scss_project_new", scss_project_new)

css_project_new = Bundle(
    scss_project_new,
    "./lib/flatpickr/flatpickr.css",
    "./lib/codemirror/codemirror.css",
    "./lib/codemirror/nord.css",
    "./lib/codemirror/simplescrollbars.css",
    filters="rcssmin",
    output="css/search.min.css",
)
web_assets.register("css_project_new", css_project_new)

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
    "./js/ajax.js",
    "./js/tabs.js",
    filters="jsmin",
    output="js/project_new.min.js",
)
web_assets.register("js_project_new", js)

# project details
css_project_details = Bundle(
    "./assets/base.scss",
    "./assets/head.scss",
    "./assets/nav.scss",
    "./assets/input.scss",
    "./lib/prism/prism.css",
    "./assets/collapse.scss",
    filters="pyscss,rcssmin",
    output="css/project.min.css",
)
web_assets.register("css_project_details", css_project_details)

js = Bundle(
    "./js/project.js",
    "./lib/table/table.js",
    "./js/table_cust.js",
    "./js/password.js",
    "./lib/scroll/scroll.js",
    "./js/ajax.js",
    "./js/tabs.js",
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
css_connections = Bundle(
    "./assets/base.scss",
    "./assets/head.scss",
    "./assets/nav.scss",
    "./assets/collapse.scss",
    "./assets/input.scss",
    "./assets/connection.scss",
    "./lib/codemirror/codemirror.css",
    "./lib/codemirror/nord.css",
    "./lib/codemirror/simplescrollbars.css",
    filters="pyscss,rcssmin",
    output="css/project.min.css",
)
web_assets.register("css_connections", css_connections)

js = Bundle(
    "./lib/codemirror/codemirror.js",
    "./lib/codemirror/gfm.js",
    "./lib/codemirror/overlay.js",
    "./lib/codemirror/shell.js",
    "./lib/codemirror/matchbrackets.js",
    "./lib/codemirror/simplescrollbars.js",
    "./js/functions.js",
    "./js/password.js",
    "./lib/table/table.js",
    "./js/table_cust.js",
    "./js/collapse.js",
    "./js/connection.js",
    "./js/executor_status.js",
    "./js/flashes.js",
    "./js/tabs.js",
    "./js/ajax.js",
    filters="jsmin",
    output="js/project.min.js",
)
web_assets.register("js_connections", js)


# prism
css_prism = Bundle(
    "./lib/prism/prism.css", filters="pyscss,rcssmin", output="css/prism.min.css"
)
web_assets.register("css_prism", css_prism)

js = Bundle("./lib/prism/prism.js", filters="jsmin", output="js/prism.min.js")
web_assets.register("js_prism", js)
