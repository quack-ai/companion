# Copyright (C) 2023, Quack AI.

# All rights reserved.
# Copying and/or distributing is strictly prohibited without the express permission of its copyright owner.

import argparse
import os
import time
from typing import Any, Dict, Optional

import requests
from dotenv import load_dotenv


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
    load_dotenv()

    # Log as superuser
    superuser_login = str(os.environ.get("SUPERUSER_LOGIN", ""))
    superuser_pwd = str(os.environ.get("SUPERUSER_PWD", ""))

    start_ts = time.time()
    # Retrieve superuser token
    superuser_auth = {
        "Authorization": f"Bearer {get_token(args.endpoint, superuser_login, superuser_pwd)}",
        "Content-Type": "application/json",
    }

    # Hardcoded info
    user_login = "karpathy"
    user_id = 241138
    user_pwd = "my_pwd"  # noqa S105
    repo_id = 582822129
    # repo_name = "karpathy/nanoGPT"

    # create an access
    api_request(
        "post", f"{args.endpoint}/users/", superuser_auth, {"id": user_id, "password": user_pwd, "scope": "user"}
    )
    user_auth = {
        "Authorization": f"Bearer {get_token(args.endpoint, user_login, user_pwd)}",
        "Content-Type": "application/json",
    }
    # Get & Fetch access
    api_request("get", f"{args.endpoint}/users/{user_id}/", superuser_auth)
    api_request("get", f"{args.endpoint}/users/", superuser_auth)
    # Modify access
    new_pwd = "my_new_pwd"  # nosec B105  # noqa S105
    api_request("put", f"{args.endpoint}/users/{user_id}/", superuser_auth, {"password": new_pwd})

    # Repos
    api_request("post", f"{args.endpoint}/repos/", user_auth, {"id": repo_id})
    api_request("get", f"{args.endpoint}/repos/{repo_id}/", user_auth)
    api_request("get", f"{args.endpoint}/repos/", user_auth)
    api_request("put", f"{args.endpoint}/repos/{repo_id}/disable", user_auth, {})
    api_request("put", f"{args.endpoint}/repos/{repo_id}/enable", user_auth, {})

    # Guidelines
    payload = {
        "title": "My custom guideline",
        "details": "Don't mispell any word",
        "repo_id": repo_id,
        "order": 0,
    }
    guideline_id = api_request("post", f"{args.endpoint}/guidelines/", user_auth, payload)["id"]
    payload = {
        "title": "My second guideline",
        "details": "Always document public interface",
        "repo_id": repo_id,
        "order": 1,
    }
    guideline_2 = api_request("post", f"{args.endpoint}/guidelines/", user_auth, payload)["id"]
    guideline = api_request("get", f"{args.endpoint}/guidelines/{guideline_id}/", user_auth)
    api_request("get", f"{args.endpoint}/guidelines/", superuser_auth)
    api_request("get", f"{args.endpoint}/repos/{repo_id}/guidelines", user_auth)
    api_request(
        "put",
        f"{args.endpoint}/guidelines/{guideline_id}",
        user_auth,
        {"title": "Updated title", "details": "Updated details"},
    )
    api_request(
        "put",
        f"{args.endpoint}/guidelines/{guideline_2}/order/2",
        user_auth,
        {},
    )
    api_request(
        "put",
        f"{args.endpoint}/repos/{repo_id}/guidelines/order",
        user_auth,
        {"guideline_ids": [guideline_2, guideline_id]},
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

    parser.add_argument("--endpoint", type=str, default="http://localhost:8050/api/v1", help="the API endpoint")

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    args = parse_args()
    main(args)
