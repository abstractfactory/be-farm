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

os.environ["APP_ROOT_PATH"] = app.root_path

def get(*args, **kwargs):
    token = os.environ.get("GITHUB_API_TOKEN")
    kwargs["headers"] = {"Authorization": "token %s" % token} if token else None
    return requests.get(*args, **kwargs)


def update():
    readme = "https://github.com/{user}/{repo}"
    github = "https://raw.githubusercontent.com/{user}/{repo}/master/{fname}"
    github_api = "https://api.github.com/repos/{user}/{repo}/{endpoint}"

    endpoint = github.format(user="mottosso",
                             repo="be-presets",
                             fname="presets.json")
    presets_json = get(endpoint).json()
    presets = list()
    for preset in presets_json["presets"]:
        user, repo = preset["repository"].split("/", 1)
        endpoint = github.format(user=user,
                                 repo=repo,
                                 fname="package.json")

        package = get(endpoint).json()

        thumbnail = package.get("thumbnail")
        if thumbnail:
            thumbnail = github.format(user=user,
                                      repo=repo,
                                      fname=thumbnail)
        else:
            thumbnail = github.format(user="mottosso",
                                      repo="be-presets",
                                      fname="default_thumbnail.png")

        stargazers_url = github_api.format(user=user, repo=repo, endpoint="stargazers")
        stargazers = len(get(stargazers_url).json())

        title = package.get("title") or preset["name"].title()
        description = package.get("description")

        if not description:
            description = "No description"
        elif len(description) > 70:
            description = description[:67] + "..."

        presets.append({
            "name": preset["name"],
            "title": title,
            "repository": preset["repository"],
            "likes": 10,
            "link": package.get("link") or readme.format(user=user, repo=repo),
            "description": description,
            "thumbnail": thumbnail,
            "likes": stargazers
        })

    self.cache[:] = presets


def sync():
    while True:
        log.info("Syncing..")
        update()
        log.info("Done")
        time.sleep(10 if os.environ.get("DEVELOP") else 60 * 30)

worker = threading.Thread(target=sync)
worker.daemon = True
worker.start()


class Presets(flask.ext.restful.Resource):
    def get(self):
        return cache


api = flask.ext.restful.Api(app)
api.add_resource(Presets, "/presets")


def debug(app):
    os.environ["DEVELOP"] = "true"
    app.debug = True
    return app.run()


def production(app):
    return app.run()


if __name__ == "__main__":
    debug(app)
