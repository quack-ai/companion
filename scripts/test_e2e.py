# Copyright (C) 2023-2024, Quack AI.

# This program is licensed under the Apache License 2.0.
# See LICENSE or go to <https://www.apache.org/licenses/LICENSE-2.0> for full license details.

import argparse
import time
from typing import Any, Dict, Optional

import requests


def get_token(api_url: str, login: str, pwd: str, timeout: int = 5) -> str:
    response = requests.post(
        f"{api_url}/login/creds",
        data={"username": login, "password": pwd},
        timeout=timeout,
    )
    if response.status_code != 200:
        raise ValueError(response.json()["detail"])
    return response.json()["access_token"]


def api_request(
    method_type: str, route: str, headers: Dict[str, str], payload: Optional[Dict[str, Any]] = None, timeout: int = 5
):
    kwargs = {"json": payload} if isinstance(payload, dict) else {}

    response = getattr(requests, method_type)(route, headers=headers, timeout=timeout, **kwargs)
    try:
        detail = response.json()
    except (requests.exceptions.JSONDecodeError, KeyError):
        detail = response.text
    assert response.status_code // 100 == 2, print(detail)
    return response.json()


def main(args):
    # Log as superuser
    superuser_login = "superadmin_login"
    superuser_pwd = "superadmin_pwd"  # noqa S105

    start_ts = time.time()
    # Retrieve superuser token
    superuser_auth = {
        "Authorization": f"Bearer {get_token(args.endpoint, superuser_login, superuser_pwd)}",
        "Content-Type": "application/json",
    }

    # Hardcoded info
    user_login = "karpathy"
    provider_id = 241138
    user_pwd = "my_pwd"  # noqa S105
    provider_repo_id = 582822129
    # repo_name = "karpathy/nanoGPT"

    # create an access
    user_id = api_request(
        "post",
        f"{args.endpoint}/users/",
        superuser_auth,
        {"login": user_login, "password": user_pwd, "provider_user_id": provider_id, "scope": "user"},
    )["id"]
    user_auth = {
        "Authorization": f"Bearer {get_token(args.endpoint, user_login, user_pwd)}",
        "Content-Type": "application/json",
    }
    # Get & Fetch access
    api_request("get", f"{args.endpoint}/users/{user_id}/", superuser_auth)
    api_request("get", f"{args.endpoint}/users/", superuser_auth)
    # Check that redirect is working
    api_request("get", f"{args.endpoint}/users", superuser_auth)
    # Modify access
    new_pwd = "my_new_pwd"  # noqa S105
    api_request("patch", f"{args.endpoint}/users/{user_id}/", superuser_auth, {"password": new_pwd})

    # Repos
    repo_id = api_request("post", f"{args.endpoint}/repos/", superuser_auth, {"provider_repo_id": provider_repo_id})[
        "id"
    ]
    api_request("get", f"{args.endpoint}/repos/{repo_id}/", user_auth)
    api_request("get", f"{args.endpoint}/repos/", superuser_auth)

    # Guidelines
    payload = {"content": "Don't mispell any word"}
    guideline_id = api_request("post", f"{args.endpoint}/guidelines/", user_auth, payload)["id"]
    payload = {"content": "Always document public interface"}
    api_request("post", f"{args.endpoint}/guidelines/", user_auth, payload)["id"]
    guideline = api_request("get", f"{args.endpoint}/guidelines/{guideline_id}/", user_auth)
    api_request("get", f"{args.endpoint}/guidelines/", superuser_auth)
    # api_request("get", f"{args.endpoint}/repos/{repo_id}/guidelines", user_auth)
    api_request(
        "patch",
        f"{args.endpoint}/guidelines/{guideline_id}",
        user_auth,
        {"content": "Updated details"},
    )

    # Delete
    for guideline in api_request("get", f"{args.endpoint}/guidelines/", superuser_auth):
        api_request("delete", f"{args.endpoint}/guidelines/{guideline['id']}/", user_auth, {})
    for repo in api_request("get", f"{args.endpoint}/repos/", superuser_auth):
        api_request("delete", f"{args.endpoint}/repos/{repo['id']}/", superuser_auth, {})
    api_request("delete", f"{args.endpoint}/users/{user_id}/", superuser_auth)

    print(f"SUCCESS in {time.time() - start_ts:.3}s")

    return


def parse_args():
    parser = argparse.ArgumentParser(
        description="Quack API End-to-End test", formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--endpoint", type=str, default="http://localhost:5050/api/v1", help="the API endpoint")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args)
