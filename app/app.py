# Standard libraries
import os
import sys
import time
import logging
import threading

# Dependencies
import flask
import flask.ext.restful
import requests

# Local
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

def get(*args, **kwargs):
    token = os.environ.get("GITHUB_API_TOKEN")
    kwargs["headers"] = {"Authorization": "token %s" % token} if token else None
    try:
        return requests.get(*args, **kwargs).json()
    except Exception as e:
        log.error(str(e))
        return {}


def update():
    log.info("Updating..")

    raw = "https://raw.githubusercontent.com/{user}/{repo}/master/{fname}"
    api = "https://api.github.com/repos/{user}/{repo}/{endpoint}"
    link = "https://github.com/{user}/{repo}"

    endpoint = raw.format(user="mottosso",
                          repo="be-presets",
                          fname="presets.json")
    presets_json = get(endpoint)
    presets = list()
    for preset in presets_json.get("presets", []):
        try:
            user, repo = preset["repository"].split("/", 1)
        except ValueError as e:
            log.error("Incorrectly formatted repository "
                      "name: %s" % preset["repository"])
            log.error(str(e))
            continue

        endpoint = raw.format(user=user,
                              repo=repo,
                              fname="package.json")

        package = get(endpoint)

        thumbnail = package.get("thumbnail")
        if thumbnail:
            thumbnail = raw.format(user=user,
                                   repo=repo,
                                   fname=thumbnail)
        else:
            thumbnail = raw.format(user="mottosso",
                                   repo="be-presets",
                                   fname="default_thumbnail.png")

        stargazers_url = api.format(user=user, repo=repo, endpoint="stargazers")
        stargazers = len(get(stargazers_url))

        label = package.get("label") or preset["name"].title()
        description = package.get("description")

        if not description:
            description = "No description"
        elif len(description) > 70:
            description = description[:67] + "..."

        presets.append({
            "name": preset["name"],
            "label": label,
            "repository": preset["repository"],
            "likes": 10,
            "link": package.get("link") or link.format(user=user, repo=repo),
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
    def get(self):
        return cache

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
