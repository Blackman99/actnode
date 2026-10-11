# Install

actnode is a single Python package with **no dependencies** (Python 3.9+).

```bash
pipx install git+https://github.com/Blackman99/actnode
# or
pip install git+https://github.com/Blackman99/actnode@v0.1.0
```

Wheels are attached to every [GitHub release](https://github.com/Blackman99/actnode/releases).

Check it works (needs network access to github.com):

```bash
actnode --version
actnode demo
```

## Token

actnode reads `action.yml` files from `raw.githubusercontent.com` (no token needed) and lists tags through the GitHub API, which allows 60 unauthenticated requests per hour. For bigger repos set a token:

```bash
export GITHUB_TOKEN=$(gh auth token)   # or any token; no scopes needed for public actions
```

Inside GitHub Actions the [Action](action.md) uses `github.token` automatically.
