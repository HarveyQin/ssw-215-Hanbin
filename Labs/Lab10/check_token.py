from github_service import (
    GitHubRepositoryNotFoundError,
    GitHubServiceUnavailableError,
    fetch_readme,
)

try:
    readme = fetch_readme("pallets", "flask")
except GitHubRepositoryNotFoundError:
    print("GitHub repository or README not found.")
except GitHubServiceUnavailableError:
    print("GitHub is unavailable. Check GITHUB_TOKEN in .env.")
else:
    print("status: 200")
    print("README:", readme[:80])