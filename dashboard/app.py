# Copyright (C) 2023, Quack AI.

# This program is licensed under the GNU Affero General Public License v3.0 or later.
# See LICENSE or go to <https://www.gnu.org/licenses/agpl-3.0.txt> for full license details.

import os

import requests
import streamlit as st

# API_ENDPOINT: str = os.environ["API_ENDPOINT"]
API_ENDPOINT: str = "http://api.localhost:8050/api/v1"
HTTP_TIMEOUT: int = int(os.getenv("HTTP_TIMEOUT", 10))
GHAPI_ENDPOINT = "https://api.github.com"


def main():
    # Wide mode
    st.set_page_config(
        page_title="Quack AI - Guideline management",
        page_icon="https://avatars.githubusercontent.com/u/118990213?s=200&v=4",
        layout="wide",
        menu_items={
            "Report a bug": "https://github.com/quack-ai/contribution-api/issues/new",
            "About": "https://github.com/quack-ai/contribution-api",
        },
    )
    st.title("Guideline edition dashboard")
    st.header("Editor")
    # Sidebar
    st.sidebar.title("Credentials")
    # Authentication
    gh_token = st.sidebar.text_input("GitHub token", type="password", value=st.session_state.get("gh_token", ""))
    if st.sidebar.button("Authenticate", disabled=len(gh_token) == 0):
        st.session_state["gh_token"] = gh_token
        with st.spinner("Authenticating..."):
            st.session_state["token"] = st.session_state.get(
                "token",
                requests.post(
                    f"{API_ENDPOINT}/login/token",
                    json={"github_token": st.session_state["gh_token"]},
                    timeout=HTTP_TIMEOUT,
                ).json()["access_token"],
            )

    if st.session_state.get("gh_token") is not None:
        if st.session_state.get("available_repos") is None:
            with st.spinner("Fetching repos..."):
                st.session_state["available_repos"] = requests.get(
                    f"{GHAPI_ENDPOINT}/user/repos",
                    params={"affiliation": "owner", "visibility": "public", "per_page": 100},
                    headers={"Authorization": f"Bearer {st.session_state['gh_token']}"},
                    timeout=HTTP_TIMEOUT,
                ).json()

    st.sidebar.title("Selection")
    selected_repo = st.sidebar.selectbox(
        "Available repos",
        tuple(repo["full_name"] for repo in st.session_state.get("available_repos", [])),
    )
    st.session_state["is_repo_selected"] = st.session_state.get("is_repo_selected", False)
    st.session_state["is_repo_registered"] = st.session_state.get("is_repo_registered", False)
    if isinstance(selected_repo, str):
        st.session_state["is_repo_selected"] = True
        # Installed repos
        installed_repos = requests.get(
            f"{API_ENDPOINT}/repos",
            headers={"Authorization": f"Bearer {st.session_state['token']}"},
            timeout=HTTP_TIMEOUT,
        ).json()
        installed_names = [repo["full_name"] for repo in installed_repos]
        st.session_state["is_repo_registered"] = selected_repo in installed_names

    if st.session_state["is_repo_selected"] and not st.session_state["is_repo_registered"]:
        # Register the repo
        st.sidebar.info(f"The repository {selected_repo} is not yet registered. Would you like to install it?")
        if st.sidebar.button("Register repository"):
            gh_repo = [
                repo for repo in st.session_state.get("available_repos", []) if repo["full_name"] == selected_repo
            ][0]
            response = requests.post(
                f"{API_ENDPOINT}/repos",
                json={"id": gh_repo["id"], "owner_id": gh_repo["owner"]["id"], "full_name": gh_repo["full_name"]},
                headers={"Authorization": f"Bearer {st.session_state['token']}"},
                timeout=HTTP_TIMEOUT,
            )
            if response.status_code == 201:
                st.session_state["is_repo_registered"] = True
                st.balloons()
                st.sidebar.success(f"Repository {selected_repo} registered", icon="✅")

    if st.session_state["is_repo_selected"] and st.session_state["is_repo_registered"]:
        st.session_state["selected_repo"] = selected_repo

    # Fetch guidelines
    st.session_state["guidelines"] = []
    if st.session_state.get("token") is not None and st.session_state.get("selected_repo") is not None:
        gh_repo = [
            repo
            for repo in st.session_state.get("available_repos", [])
            if repo["full_name"] == st.session_state["selected_repo"]
        ][0]
        with st.spinner("Fetching guidelines..."):
            st.session_state["guidelines"] = requests.get(
                f"{API_ENDPOINT}/guidelines/from/{gh_repo['id']}",
                headers={"Authorization": f"Bearer {st.session_state['token']}"},
                timeout=HTTP_TIMEOUT,
            ).json()
    st.session_state["default_guideline_idx"] = 0
    selected_title = st.sidebar.selectbox(
        "Repo guidelines",
        tuple(guideline["title"] for guideline in st.session_state["guidelines"]),
        # index=st.session_state["default_guideline_idx"],
    )
    # Guideline selection
    if isinstance(selected_title, str):
        st.session_state["selected_guideline"] = [
            _guideline for _guideline in st.session_state["guidelines"] if _guideline["title"] == selected_title
        ][0]

    # Guideline registration
    if st.sidebar.button("Add new guideline", disabled=len(st.session_state["guidelines"]) == 0):
        gh_repo = [
            repo
            for repo in st.session_state.get("available_repos", [])
            if repo["full_name"] == st.session_state["selected_repo"]
        ][0]
        # Create an entry
        payload = {
            "repo_id": gh_repo["id"],
            "title": f"Guideline title {len(st.session_state['guidelines'])}",
            "details": "Guideline description",
        }
        response = requests.post(
            f"{API_ENDPOINT}/guidelines",
            json=payload,
            headers={"Authorization": f"Bearer {st.session_state['token']}"},
            timeout=HTTP_TIMEOUT,
        )
        if response.status_code == 201:
            st.sidebar.success(f"Guideline {payload['title']} created", icon="✅")
            st.session_state["guidelines"].append(st.session_state["selected_guideline"])
            st.session_state["default_guideline_idx"] = len(st.session_state["guidelines"]) - 1
            st.session_state["selected_guideline"] = response.json()
        else:
            st.error("Unable to create guideline", icon="🚨")

    if st.sidebar.button("Delete guideline", disabled=st.session_state.get("selected_guideline") is None):
        # Push the edit to the API
        response = requests.delete(
            f"{API_ENDPOINT}/guidelines/{st.session_state['selected_guideline']['id']}",
            headers={"Authorization": f"Bearer {st.session_state['token']}"},
            timeout=HTTP_TIMEOUT,
        )
        if response.status_code == 200:
            st.sidebar.success(f"Guideline {st.session_state['selected_guideline']['title']} deleted", icon="✅")
            st.session_state["guidelines"] = [
                guideline
                for guideline in st.session_state["guidelines"]
                if guideline["id"] != st.session_state["selected_guideline"]["id"]
            ]
            st.session_state["default_guideline_idx"] = 0
            st.session_state["selected_guideline"] = (
                st.session_state["guidelines"][0] if len(st.session_state["guidelines"]) > 0 else None
            )

    guideline_title = st.text_input(
        "Title",
        max_chars=100,
        value=st.session_state.get("selected_guideline", {}).get("title", ""),
        disabled=len(st.session_state["guidelines"]) == 0,
    )
    guideline_details = st.text_area(
        "Details",
        value=st.session_state.get("selected_guideline", {}).get("details", ""),
        disabled=len(st.session_state["guidelines"]) == 0,
    )
    if st.button("Save guideline", disabled=st.session_state.get("selected_guideline") is None):
        # Form check
        if len(guideline_title) == 0 or len(guideline_details) == 0:
            st.error("Both the title & details sections need to be filled", icon="🚨")

        # Push the edit to the API
        response = requests.put(
            f"{API_ENDPOINT}/guidelines/{st.session_state['selected_guideline']['id']}",
            json={"title": guideline_title, "details": guideline_details},
            headers={"Authorization": f"Bearer {st.session_state['token']}"},
            timeout=HTTP_TIMEOUT,
        )
        if response.status_code == 200:
            st.session_state["selected_guideline"] = response.json()
            st.balloons()
            st.sidebar.success(f"Guideline {guideline_title} saved", icon="✅")


if __name__ == "__main__":
    main()
