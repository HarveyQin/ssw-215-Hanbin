from unittest.mock import MagicMock, patch

from github_service import fetch_readme


def test_fetch_readme_truncates_long_readme():
    response = MagicMock()
    response.status_code = 200
    response.text = "x" * 5000

    with patch("github_service.requests.get", return_value=response):
        readme = fetch_readme("owner", "repo")

    assert len(readme) == 4000