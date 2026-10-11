import json

from actnode.core import Resolver, apply_fixes, find_uses, node_major, parse_using, scan, split_ref
from actnode.cli import main

RAW = "https://raw.githubusercontent.com/"
API = "https://api.github.com/repos/"


def node(v):
    return f"name: x\nruns:\n  using: 'node{v}'\n  main: index.js\n"


COMPOSITE = "runs:\n  using: composite\n  steps:\n    - uses: acme/old@v1\n    - uses: ./inner\n"
SHA5 = "b" * 40
FILES = {
    RAW + "acme/js/v4/action.yml": node(20),
    RAW + "acme/js/v5.2.0/action.yml": node(24),
    RAW + "acme/js/v6.0.0/action.yml": node(24),
    RAW + "acme/js/" + "a" * 40 + "/action.yml": node(20),
    RAW + "acme/new/v2/action.yml": node(24),
    RAW + "acme/stuck/v1/action.yaml": node(16),
    RAW + "acme/stuck/v1.0.0/action.yaml": node(16),
    RAW + "acme/comp/v1/action.yml": COMPOSITE,
    RAW + "acme/comp/v1/inner/action.yml": node(24),
    RAW + "acme/old/v1/action.yml": node(20),
    RAW + "acme/old/v1.0.0/action.yml": node(20),
    API + "acme/js/tags?per_page=100&page=1": json.dumps([
        {"name": n, "commit": {"sha": s}} for n, s in
        [("v6", "c" * 40), ("v6.0.0", "c" * 40), ("v5", SHA5), ("v5.2.0", SHA5), ("v4", "a" * 40), ("latest", "d" * 40)]
    ]),
    API + "acme/stuck/tags?per_page=100&page=1": json.dumps([{"name": "v1.0.0", "commit": {"sha": "e" * 40}}]),
    API + "acme/old/tags?per_page=100&page=1": json.dumps([{"name": "v1.0.0", "commit": {"sha": "f" * 40}}]),
}


def fake(url):
    return FILES.get(url)


WF = """jobs:
  t:
    steps:
      - uses: acme/js@v4
      - name: pinned
        uses: acme/js@{a} # v4.0.0
      - uses: 'acme/new@v2'
      - uses: acme/stuck@v1
      - uses: acme/comp@v1
      - uses: docker://alpine:3
      - run: echo uses: nothing
""".format(a="a" * 40)


def repo(tmp_path):
    d = tmp_path / ".github" / "workflows"
    d.mkdir(parents=True)
    (d / "ci.yml").write_text(WF)
    return tmp_path


def test_helpers():
    assert node_major("node20") == 20 and node_major("composite") is None
    assert parse_using(node(16)) == "node16"
    assert split_ref("a/b/c/d@v1") == ("a", "b", "c/d", "v1")
    assert split_ref("./x") is None and split_ref("docker://x") is None
    assert [r for _, r, _ in find_uses(WF)][:3] == ["acme/js@v4", "acme/js@" + "a" * 40, "acme/new@v2"]


def test_scan_classifies(tmp_path):
    fs = scan(repo(tmp_path), Resolver(fetch=fake))
    by = {(f.uses, f.via): f for f in fs}
    assert by[("acme/js@v4", None)].suggest == "acme/js@v5"  # smallest jump that is on node24
    assert by[("acme/js@" + "a" * 40, None)].suggest == f"acme/js@{SHA5} # v5.2.0"
    assert by[("acme/new@v2", None)].status == "ok"
    assert by[("acme/stuck@v1", None)].status == "no-fix"
    assert by[("acme/comp@v1", None)].status == "composite"
    assert by[("acme/old@v1", "acme/comp@v1")].status == "no-fix"
    assert by[("acme/comp/inner@v1", "acme/comp@v1")].status == "ok"
    assert by[("docker://alpine:3", None)].status == "docker"


def test_fix_rewrites_only_direct(tmp_path):
    r = repo(tmp_path)
    fs = scan(r, Resolver(fetch=fake))
    assert apply_fixes(r, fs) == 2
    txt = (r / ".github/workflows/ci.yml").read_text()
    assert "- uses: acme/js@v5\n" in txt
    assert f"uses: acme/js@{SHA5} # v5.2.0\n" in txt
    assert "acme/stuck@v1" in txt


def test_local_action(tmp_path):
    (tmp_path / "action.yml").write_text("runs:\n  using: composite\n  steps:\n    - uses: ./sub\n")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "action.yml").write_text(node(20))
    fs = scan(tmp_path, Resolver(fetch=fake))
    assert any(f.status == "no-fix" and f.uses == "./sub" for f in fs)


def test_cli_json_and_fail(tmp_path, monkeypatch, capsys):
    import actnode.core as core
    monkeypatch.setattr(core, "http_get", fake)
    monkeypatch.setattr(core.Resolver, "__init__", lambda self, fetch=fake: (setattr(self, "fetch", fake), setattr(self, "_yml", {}), setattr(self, "_tags", {}))[0])
    r = repo(tmp_path)
    assert main([str(r), "--fail"]) == 1
    capsys.readouterr()
    assert main(["scan", str(r), "--format", "json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["target"] == 24 and len(data["findings"]) >= 6
    out = tmp_path / "s.md"
    main([str(r), "--format", "md", "-o", str(out)])
    assert "| Where |" in out.read_text()
