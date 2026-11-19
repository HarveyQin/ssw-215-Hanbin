import os
import re
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_URL = "https://api.github.com"
README_LIMIT = 4000


class GitHubRepositoryNotFoundError(Exception):
    pass


class GitHubServiceUnavailableError(Exception):
    pass


class InvalidGitHubRepositoryError(Exception):
    pass


def fetch_readme(owner, repo):
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", owner or ""):
        raise InvalidGitHubRepositoryError("Invalid GitHub owner")
    if not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", repo or ""):
        raise InvalidGitHubRepositoryError("Invalid GitHub repository")

    headers = {"Accept": "application/vnd.github.raw"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    url = "{}/repos/{}/{}/readme".format(
        GITHUB_API_URL,
        quote(owner, safe=""),
        quote(repo, safe=""),
    )
    try:
        response = requests.get(url, headers=headers, timeout=10)
    except requests.RequestException as error:
        raise GitHubServiceUnavailableError(
            "The GitHub API request failed"
        ) from error

    if response.status_code == 404:
        raise GitHubRepositoryNotFoundError("Repository or README not found")
    try:
        response.raise_for_status()
    except requests.RequestException as error:
        raise GitHubServiceUnavailableError(
            "The GitHub API request failed"
        ) from error

    return response.text[:README_LIMIT]
