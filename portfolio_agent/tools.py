import requests

def get_github_repos() -> dict:
    """Fetches Amayas's public GitHub repositories in real time.

    Use this tool whenever the user asks about Amayas's projects,
    repositories, recent work, or what he is currently building.
    Returns repository names, descriptions, main language, stars,
    and last update date.
    """
    try:
        r = requests.get(
            "https://api.github.com/users/amayasmh/repos",
            params={"sort": "updated", "per_page": 10},
            timeout=5,
        )
        r.raise_for_status()
        repos = [
            {
                "name": repo["name"],
                "description": repo["description"],
                "language": repo["language"],
                "stars": repo["stargazers_count"],
                "updated_at": repo["updated_at"][:10],
                "url": repo["html_url"],
            }
            for repo in r.json()
        ]
        return {"status": "success", "repos": repos}
    except requests.RequestException as e:
        return {"status": "error", "message": f"GitHub API unavailable: {e}"}