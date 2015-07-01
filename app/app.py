# Standard libraries
import os
import sys
import time
import logging
import threading

# Dependencies
import flask
import flask.ext.restful

# Local
import lib
import routes.home

logging.basicConfig(format="%(asctime)-15s %(message)s")
log = logging.getLogger()
log.setLevel(logging.DEBUG)

self = sys.modules[__name__]
self.cache = list()

self.app = flask.Flask(__name__)
self.app.route("/", defaults={"p": ""})(routes.home.route)
self.app.route("/<path:p>")(routes.home.route)  # All paths route to index.html

os.environ["APP_ROOT_PATH"] = self.app.root_path


def update():
    """Update cache of project presets

    Calling this will initiate a number of requests to GitHub and it's API
    in order to update the in-memory cache of each publicly avaialble project
    for be.

    """

    log.info("Updating..")

    raw = "https://raw.githubusercontent.com/{repo}/master/{fname}"
    api = "https://api.github.com/repos/{repo}/{endpoint}"
    repo_link = "https://github.com/{repo}"
    gist_link = "https://gist.github.com/{repo}"

    endpoint = raw.format(repo="mottosso/be-presets",
                          fname="presets.json")
    presets_json = lib.get(endpoint).json()
    presets = list()
    for preset in presets_json.get("presets", []):
        try:
            user, repo = preset["repository"].split("/", 1)
        except ValueError as e:
            log.error("Incorrectly formatted repository "
                      "name: %s" % preset["repository"])
            log.error(str(e))
            continue

        repo = preset["repository"]
        package, source = lib.package(repo)

        if not package:
            log.error("package.json not found in %s" % repo)
            continue

        thumbnail = package.get("thumbnail")
        if thumbnail:
            thumbnail = raw.format(repo=repo,
                                   fname=thumbnail)
        else:
            thumbnail = "static/img/default_thumbnail.png"
        print thumbnail

        stargazers_url = api.format(repo=repo,
                                    endpoint="stargazers")
        stargazers = len(lib.get(stargazers_url).json())

        label = (package.get("label") or
                 preset["name"].replace("-", " ").title())
        description = package.get("description")

        if not description:
            description = "No description"
        elif len(description) > 70:
            description = description[:67] + "..."

        link = gist_link if source == "gist" else repo_link
        link = package.get("link") or link.format(repo=repo)

        presets.append({
            "name": preset["name"],
            "label": label,
            "repository": preset["repository"],
            "likes": 10,
            "link": link,
            "description": description,
            "thumbnail": thumbnail,
            "likes": stargazers
        })

    self.cache[:] = presets
    log.info("Done")


def sync():
    while True:
        update()
        time.sleep(10 if os.environ.get("DEVELOP") else 60 * 30)

worker = threading.Thread(target=sync)
worker.daemon = True
worker.start()


class Presets(flask.ext.restful.Resource):
    def get(this):
        return self.cache

    def post(self):
        headers = flask.request.headers
        if headers.get("X-Github-Event") == "push":
            update()


api = flask.ext.restful.Api(self.app)
api.add_resource(Presets, "/presets")


def debug(app):
    os.environ["DEVELOP"] = "true"
    app.debug = True
    return app.run()


def production(app):
    return app.run()


if __name__ == "__main__":
    debug(self.app)
