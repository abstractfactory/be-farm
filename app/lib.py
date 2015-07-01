import os
import json
import logging
import requests

log = logging.getLogger()
log.setLevel(logging.DEBUG)


def get(*args, **kwargs):
    """Wrapper around requests.get with implicit authentication"""
    token = os.environ.get("GITHUB_API_TOKEN")
    if token:
        log.info("Using GitHub API Token")
        kwargs["headers"] = {
            "Authorization": "token %s" % token
        }
    try:
        return requests.get(*args, **kwargs)
    except Exception as e:
        log.error(str(e))
        return {}


def package(repo):
    """Return package from username/id pair, e.g. mottosso/be-ad"""
    source = "gist"
    package = _package_from_gist(repo)
    if not package:
        source = "repo"
        package = _package_from_repo(repo)
    return package, source


def _package_from_gist(repo):
    """Evaluate whether gist is a be package

    Arguments:
        gist (str): username/id pair e.g. mottosso/2bb4651a05af85711cde

    """

    _, gistid = repo.split("/")

    gist_template = "https://api.github.com/gists/{}"
    gist_path = gist_template.format(gistid)

    response = get(gist_path)
    if response.status_code == 404:
        return None

    try:
        data = response.json()
    except:
        return None

    files = data.get("files", {})
    package = files.get("package.json", {})

    try:
        content = json.loads(package.get("content", ""))
    except:
        return None

    return content


def _package_from_repo(repo):
    """Evaluate whether GitHub repository is a be package

    Arguments:
        gist (str): username/id pair e.g. mottosso/be-ad

    """

    package_template = "https://raw.githubusercontent.com"
    package_template += "/{repo}/master/package.json"
    package_path = package_template.format(repo=repo)

    response = get(package_path)
    if response.status_code == 404:
        return None

    try:
        content = response.json()
    except:
        return None

    return content
