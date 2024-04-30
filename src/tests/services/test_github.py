import pytest
from fastapi import HTTPException

from app.services.github import GitHubClient
from app.services.utils import execute_in_parallel


@pytest.mark.parametrize(
    ("repo_id", "status_code", "status_detail", "expected_name"),
    [
        (100, 404, "Not Found", None),
        (249513553, 200, None, "frgfm/torch-cam"),
    ],
)
def test_githubclient_get_repo(repo_id, status_code, status_detail, expected_name):
    github_client = GitHubClient()
    if isinstance(expected_name, str):
        response = github_client.get_repo(repo_id)
        assert response["full_name"] == expected_name
    else:
        response = github_client._get(f"repositories/{repo_id}", status_code_tolerance=status_code)
        assert response.status_code == status_code
        if isinstance(status_detail, str):
            assert response.json()["message"] == status_detail


@pytest.mark.parametrize(
    ("user_id", "status_code", "status_detail", "expected_name"),
    [
        (1000000000, 404, "Not Found", None),
        (26927750, 200, None, "frgfm"),
    ],
)
def test_githubclient_get_user(user_id, status_code, status_detail, expected_name):
    github_client = GitHubClient()
    if isinstance(expected_name, str):
        response = github_client.get_user(user_id)
        assert response["login"] == expected_name
    else:
        response = github_client._get(f"user/{user_id}", status_code_tolerance=status_code)
        assert response.status_code == status_code
        if isinstance(status_detail, str):
            assert response.json()["message"] == status_detail


@pytest.mark.parametrize(
    ("repo_name", "status_code", "status_detail", "expected_path"),
    [
        ("frgfm/hola", 404, "Not Found", None),
        ("frgfm/torch-cam", 200, None, "README.md"),
    ],
)
def test_githubclient_get_readme(repo_name, status_code, status_detail, expected_path):
    github_client = GitHubClient()
    if isinstance(expected_path, str):
        response = github_client.get_readme(repo_name)
        assert response["path"] == expected_path
    else:
        response = github_client._get(f"repos/{repo_name}/readme", status_code_tolerance=status_code)
        assert response.status_code == status_code
        if isinstance(status_detail, str):
            assert response.json()["message"] == status_detail


@pytest.mark.parametrize(
    ("repo_name", "file_path", "status_code", "status_detail"),
    [
        ("frgfm/hola", "CONTRIBUTING.md", 404, "Not Found"),
        ("frgfm/torch-cam", "Hola.md", 404, "Not Found"),
        ("frgfm/torch-cam", "CONTRIBUTING.md", 200, None),
    ],
)
def test_githubclient_get_file(repo_name, file_path, status_code, status_detail):
    github_client = GitHubClient()
    if status_code // 100 == 2:
        response = github_client.get_file(repo_name, file_path)
        assert isinstance(response, dict)
        assert response["path"] == file_path
    else:
        response = github_client._get(f"repos/{repo_name}/contents/{file_path}", status_code_tolerance=status_code)
        assert response.status_code == status_code
        if isinstance(status_detail, str):
            assert response.json()["message"] == status_detail


@pytest.mark.parametrize(
    ("repo_name", "status_code", "status_detail"),
    [
        ("frgfm/hola", 404, "Not Found"),
        ("frgfm/torch-cam", 200, None),
    ],
)
def test_githubclient_list_pulls(repo_name, status_code, status_detail):
    github_client = GitHubClient()
    if status_code // 100 == 2:
        response = github_client.list_pulls(repo_name)
        assert isinstance(response, list)
        assert all(isinstance(elt, dict) for elt in response)
    else:
        with pytest.raises(HTTPException):
            github_client.list_pulls(repo_name)


@pytest.mark.parametrize(
    ("repo_name", "issue_number", "status_code", "status_detail"),
    [
        ("frgfm/hola", 1, 404, "Not Found"),
        ("frgfm/torch-cam", 181, 200, None),
    ],
)
def test_githubclient_list_comments_from_issue(repo_name, issue_number, status_code, status_detail):
    github_client = GitHubClient()
    if status_code // 100 == 2:
        response = github_client.list_comments_from_issue(issue_number, repo_name)
        assert isinstance(response, list)
        assert all(isinstance(elt, dict) for elt in response)
    else:
        with pytest.raises(HTTPException):
            github_client.list_comments_from_issue(issue_number, repo_name)


@pytest.mark.parametrize(
    ("repo_name", "pull_number", "status_code", "status_detail"),
    [
        ("frgfm/hola", 1, 404, "Not Found"),
        ("frgfm/Holocron", 279, 200, None),
    ],
)
def test_githubclient_list_reviews_from_pull(repo_name, pull_number, status_code, status_detail):
    github_client = GitHubClient()
    if status_code // 100 == 2:
        response = github_client.list_reviews_from_pull(repo_name, pull_number)
        assert isinstance(response, list)
        assert all(isinstance(elt, dict) for elt in response)
    else:
        with pytest.raises(HTTPException):
            github_client.list_reviews_from_pull(repo_name, pull_number)


@pytest.mark.parametrize(
    ("repo_name", "pull_number", "status_code", "status_detail"),
    [
        ("frgfm/hola", 1, 404, "Not Found"),
        ("frgfm/Holocron", 279, 200, None),
    ],
)
def test_githubclient_list_review_comments_from_pull(repo_name, pull_number, status_code, status_detail):
    github_client = GitHubClient()
    if status_code // 100 == 2:
        response = github_client.list_review_comments_from_pull(pull_number, repo_name)
        assert isinstance(response, list)
        assert all(isinstance(elt, dict) for elt in response)
    else:
        with pytest.raises(HTTPException):
            github_client.list_review_comments_from_pull(pull_number, repo_name)


@pytest.mark.parametrize(
    ("repo_name", "status_code", "status_detail"),
    [
        ("frgfm/hola", 404, "Not Found"),
        ("frgfm/Holocron", 200, None),
    ],
)
def test_githubclient_fetch_reviews_from_repo(repo_name, status_code, status_detail):
    github_client = GitHubClient()
    if status_code // 100 == 2:
        response = github_client.fetch_reviews_from_repo(repo_name, num_pulls=1)
        assert isinstance(response, list)
        assert all(isinstance(elt, dict) for elt in response)
    else:
        with pytest.raises(HTTPException):
            github_client.fetch_reviews_from_repo(repo_name, num_pulls=1)


@pytest.mark.parametrize(
    ("repo_name", "status_code", "status_detail"),
    [
        ("frgfm/hola", 404, "Not Found"),
        ("frgfm/Holocron", 200, None),
    ],
)
def test_githubclient_fetch_pull_comments_from_repo(repo_name, status_code, status_detail):
    github_client = GitHubClient()
    if status_code // 100 == 2:
        response = github_client.fetch_pull_comments_from_repo(repo_name, num_pulls=1)
        assert isinstance(response, list)
        assert all(isinstance(elt, dict) for elt in response)
    else:
        with pytest.raises(HTTPException):
            github_client.fetch_pull_comments_from_repo(repo_name, num_pulls=1)


@pytest.mark.parametrize(
    ("comments", "expected_output"),
    [
        # cf. https://github.com/StanGirard/quivr/pull/1883
        (
            [
                {"id": 1425674031},
                {"id": 1425677116},
                {"id": 1425684351},
                {"id": 1425692412},
                {"id": 1425694380, "in_reply_to_id": 1425692412},
                {"id": 1425696753},
                {"id": 1425696853, "in_reply_to_id": 1425696753},
                {"id": 1426417539, "in_reply_to_id": 1425684351},
            ],
            [[1425674031], [1425677116], [1425684351, 1426417539], [1425692412, 1425694380], [1425696753, 1425696853]],
        ),
    ],
)
def test_githubclient_arrange_in_threads(comments, expected_output):
    assert GitHubClient.arrange_in_threads(comments) == expected_output


@pytest.mark.parametrize(
    ("func", "arr", "output"),
    [
        (lambda x: x**2, [1, 2, 3], [1, 4, 9]),
    ],
)
def test_execute_in_parallel(func, arr, output):
    assert list(execute_in_parallel(func, arr, num_threads=1)) == output
    assert list(execute_in_parallel(func, arr, num_threads=2)) == output
