"""Find GitHub Actions steps whose action runs on an old Node.js runtime, and the release that fixes it."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Callable, Optional

CURRENT = 24  # the Node.js runtime GitHub-hosted runners default to since 2026-06-02
USES_RE = re.compile(r"""^(?P<pre>\s*(?:-\s+)?uses:\s*)(?P<q>['"]?)(?P<ref>[^'"\s#]+)(?P=q)(?P<post>.*)$""")
USING_RE = re.compile(r"""^\s+using:\s*['"]?([A-Za-z0-9_-]+)""", re.M)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
VER_RE = re.compile(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?$")

Fetcher = Callable[[str], Optional[str]]


def _token() -> Optional[str]:
    return os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")


def http_get(url: str) -> Optional[str]:
    """GET a URL, return text or None on 404. Uses GITHUB_TOKEN/GH_TOKEN for api.github.com."""
    req = urllib.request.Request(url, headers={"User-Agent": "actnode"})
    tok = _token()
    if tok and url.startswith("https://api.github.com/"):
        req.add_header("Authorization", f"Bearer {tok}")
        req.add_header("Accept", "application/vnd.github+json")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        if e.code in (403, 429):
            raise RuntimeError(
                f"GitHub rate limit hit on {url}. Set GITHUB_TOKEN (or GH_TOKEN) and retry."
            ) from e
        raise


def node_major(using: Optional[str]) -> Optional[int]:
    if not using:
        return None
    m = re.fullmatch(r"node(\d+)", using.strip().lower())
    return int(m.group(1)) if m else None


def parse_using(action_yml: str) -> Optional[str]:
    m = USING_RE.search(action_yml)
    return m.group(1) if m else None


def find_uses(text: str):
    """Yield (line_no, ref, comment) for every `uses:` in a workflow or composite action."""
    for i, line in enumerate(text.splitlines(), 1):
        m = USES_RE.match(line)
        if m:
            yield i, m.group("ref"), m.group("post").strip()


def split_ref(ref: str):
    """'owner/repo/sub/path@ref' -> (owner, repo, subpath, ref). None for local/docker refs."""
    if ref.startswith("./") or ref.startswith("docker://") or "@" not in ref:
        return None
    spec, _, at = ref.rpartition("@")
    parts = spec.split("/")
    if len(parts) < 2:
        return None
    return parts[0], parts[1], "/".join(parts[2:]), at


def _ver(tag: str):
    m = VER_RE.match(tag)
    if not m:
        return None
    return tuple(int(x) if x else -1 for x in m.groups())


@dataclass
class Finding:
    file: str
    line: int
    uses: str
    runtime: Optional[str]
    status: str  # ok | old | unknown | no-fix | local | docker | composite
    suggest: Optional[str] = None
    via: Optional[str] = None  # composite action that pulled this in
    note: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class Resolver:
    fetch: Fetcher = http_get
    _yml: dict = field(default_factory=dict)
    _tags: dict = field(default_factory=dict)

    def action_yml(self, owner, repo, sub, ref) -> Optional[str]:
        key = (owner, repo, sub, ref)
        if key not in self._yml:
            base = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/" + (sub + "/" if sub else "")
            txt = None
            for name in ("action.yml", "action.yaml"):
                txt = self.fetch(base + name)
                if txt is not None:
                    break
            self._yml[key] = txt
        return self._yml[key]

    def tags(self, owner, repo):
        """Return list of (name, sha) for version-like tags, newest first."""
        key = (owner, repo)
        if key not in self._tags:
            out = []
            for page in (1, 2, 3):
                body = self.fetch(f"https://api.github.com/repos/{owner}/{repo}/tags?per_page=100&page={page}")
                if not body:
                    break
                data = json.loads(body)
                out += [(t["name"], t["commit"]["sha"]) for t in data if _ver(t["name"])]
                if len(data) < 100:
                    break
            out.sort(key=lambda t: (_ver(t[0]), len(t[0])), reverse=True)
            self._tags[key] = out
        return self._tags[key]

    def suggest(self, owner, repo, sub, ref, target=CURRENT) -> Optional[str]:
        """Smallest-surprise replacement ref whose action runs on node>=target, in the same ref style."""
        tags = self.tags(owner, repo)
        if not tags:
            return None
        majors = []
        for name, sha in tags:
            mj = _ver(name)[0]
            if mj not in majors:
                majors.append(mj)
        cur = _ver(ref)[0] if _ver(ref) else None
        best = None
        for mj in majors[:6]:  # newest majors first; keep the smallest jump that is still new enough
            if cur is not None and mj < cur:
                break
            in_major = [(n, s) for n, s in tags if _ver(n)[0] == mj]
            full = [t for t in in_major if _ver(t[0])[2] >= 0] or in_major
            newest_name, newest_sha = full[0]
            y = self.action_yml(owner, repo, sub, newest_name)
            ul = (parse_using(y) or "") if y else ""
            nm = node_major(ul)
            if y is None or (nm is not None and nm < target):
                if best:
                    break
                continue
            best = (mj, in_major, newest_name, newest_sha)
        if not best:
            return None
        mj, in_major, newest_name, newest_sha = best
        spec = f"{owner}/{repo}" + (f"/{sub}" if sub else "")
        if SHA_RE.match(ref):
            return f"{spec}@{newest_sha} # {newest_name}"
        v = _ver(ref)
        if v and v[1] == -1:
            short = [n for n, _ in in_major if _ver(n)[1] == -1]
            return f"{spec}@{short[0] if short else newest_name}"
        return f"{spec}@{newest_name}"
        return None


def workflow_files(root: Path):
    files = []
    for d in (root / ".github" / "workflows",):
        if d.is_dir():
            files += sorted(p for p in d.iterdir() if p.suffix in (".yml", ".yaml"))
    for name in ("action.yml", "action.yaml"):
        if (root / name).is_file():
            files.append(root / name)
    return files


def scan(root: Path, resolver: Optional[Resolver] = None, target: int = CURRENT, depth: int = 3):
    resolver = resolver or Resolver()
    findings: list[Finding] = []
    for f in workflow_files(root):
        rel = str(f.relative_to(root))
        for line, ref, _c in find_uses(f.read_text(encoding="utf-8")):
            findings += _check(root, rel, line, ref, resolver, target, depth, via=None)
    return findings


def _check(root, rel, line, ref, r: Resolver, target, depth, via):
    if ref.startswith("docker://"):
        return [Finding(rel, line, ref, "docker", "docker", via=via)]
    if ref.startswith("./"):
        p = root / ref[2:]
        y = None
        for name in ("action.yml", "action.yaml"):
            if (p / name).is_file():
                y = (p / name).read_text(encoding="utf-8")
                break
        if y is None:
            return [Finding(rel, line, ref, None, "unknown", via=via, note="local action.yml not found")]
        return _classify(root, rel, line, ref, y, None, r, target, depth, via)
    parts = split_ref(ref)
    if not parts:
        return [Finding(rel, line, ref, None, "unknown", via=via, note="unpinned or unparseable ref")]
    y = r.action_yml(*parts)
    if y is None:
        return [Finding(rel, line, ref, None, "unknown", via=via, note="action.yml not found at that ref")]
    return _classify(root, rel, line, ref, y, parts, r, target, depth, via)


def _classify(root, rel, line, ref, y, parts, r, target, depth, via):
    using = parse_using(y)
    nm = node_major(using)
    out = []
    if nm is not None:
        if nm >= target:
            out.append(Finding(rel, line, ref, using, "ok", via=via))
        else:
            sug = r.suggest(*parts, target=target) if parts else None
            st = "old" if sug else "no-fix"
            note = "" if sug else ("local action: bump runs.using" if not parts
                                   else f"no release on node{target} yet; ask upstream or fork")
            out.append(Finding(rel, line, ref, using, st, suggest=sug, via=via, note=note))
    elif using == "composite":
        out.append(Finding(rel, line, ref, using, "composite", via=via))
        if depth > 0:
            for _l, sub_ref, _c in find_uses(y):
                if sub_ref.startswith("./") and parts:
                    o, rp, _s, at = parts
                    sub_ref = f"{o}/{rp}/{sub_ref[2:].rstrip('/')}@{at}"
                for f in _check(root, rel, line, sub_ref, r, target, depth - 1, via=ref):
                    out.append(f)
    else:
        out.append(Finding(rel, line, ref, using, "docker" if using == "docker" else "unknown", via=via))
    return out


def apply_fixes(root: Path, findings) -> int:
    """Rewrite direct `uses:` lines that have a suggestion. Returns number of lines changed."""
    by_file: dict = {}
    for f in findings:
        if f.status == "old" and f.suggest and f.via is None:
            by_file.setdefault(f.file, {})[f.line] = f
    changed = 0
    for rel, lines in by_file.items():
        p = root / rel
        src = p.read_text(encoding="utf-8").splitlines(keepends=True)
        for ln, f in lines.items():
            raw = src[ln - 1]
            nl = raw[len(raw.rstrip("\r\n")):]
            m = USES_RE.match(raw.rstrip("\r\n"))
            if not m or m.group("ref") != f.uses:
                continue
            new_ref, _, comment = f.suggest.partition(" # ")
            post = m.group("post")
            if comment:
                post = f" # {comment}"
            src[ln - 1] = f"{m.group('pre')}{m.group('q')}{new_ref}{m.group('q')}{post}{nl}"
            changed += 1
        p.write_text("".join(src), encoding="utf-8")
    return changed
