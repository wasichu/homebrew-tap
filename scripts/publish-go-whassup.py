#!/usr/bin/env python3
"""Complete only a verified stable go-whassup release bump; never general PRs."""
import base64
import hashlib
import json
import os
import re
import subprocess
import time
import urllib.request

UPSTREAM = "wasichu/go-whassup"
FORMULA = "Formula/go-whassup.rb"
TAG = re.compile(r"v([0-9]+)\.([0-9]+)\.([0-9]+)")


def gh(*args, payload=None):
    result = subprocess.run(
        ["gh", *args], input=None if payload is None else json.dumps(payload),
        text=True, stdout=subprocess.PIPE, check=True,
    )
    return result.stdout.strip()


def api(path, payload=None):
    args = ["api", path]
    if payload is not None:
        args += ["--method", "POST", "--input", "-"]
    return json.loads(gh(*args, payload=payload) or "null")


def version(tag):
    match = TAG.fullmatch(tag)
    if not match:
        raise ValueError(f"Not a stable version tag: {tag!r}")
    return tuple(map(int, match.groups()))


def formula(repo, ref):
    data = api(f"repos/{repo}/contents/{FORMULA}?ref={ref}")
    return base64.b64decode(data["content"]).decode()


def formula_tag(text):
    match = re.search(r'^  url "https://github.com/wasichu/go-whassup/archive/refs/tags/(v[0-9.]+)\.tar\.gz"$', text, re.M)
    if not match:
        raise ValueError("Unexpected formula source URL")
    version(match[1])
    return match[1]


def expected_formula(base, tag, digest):
    """Permit only the release URL/checksum, removal of old bottles/revision."""
    if version(tag) <= version(formula_tag(base)):
        raise ValueError("Release must advance the formula version")
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise ValueError("Invalid source checksum")
    text = re.sub(r"\n  bottle do\n.*?\n  end\n", "", base, flags=re.S)
    text = re.sub(r"^  revision [0-9]+\n", "", text, flags=re.M)
    text, urls = re.subn(r'^  url "[^"\n]+"$', f'  url "https://github.com/{UPSTREAM}/archive/refs/tags/{tag}.tar.gz"', text, count=1, flags=re.M)
    text, hashes = re.subn(r'^  sha256 "[0-9a-f]{64}"$', f'  sha256 "{digest}"', text, count=1, flags=re.M)
    if urls != 1 or hashes != 1:
        raise ValueError("Expected exactly one stable source URL/checksum")
    return text


def validate_formula(base, proposed, tag, digest):
    if proposed != expected_formula(base, tag, digest):
        raise ValueError("PR includes changes beyond the verified release URL/checksum and old bottles")


def checksum(tag):
    url = f"https://github.com/{UPSTREAM}/archive/refs/tags/{tag}.tar.gz"
    digest = hashlib.sha256()
    with urllib.request.urlopen(url, timeout=120) as response:
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def check_pr(repo, number, sha):
    pr = api(f"repos/{repo}/pulls/{number}")
    if (pr["state"] != "open" or pr["draft"] or pr["head"]["sha"] != sha
            or pr["head"]["repo"]["full_name"] != repo
            or pr["base"]["ref"] != "main"
            or pr["user"]["login"] != "github-actions[bot]"):
        raise ValueError("Release PR is closed, changed, or not a same-repo bot PR")
    files = api(f"repos/{repo}/pulls/{number}/files?per_page=100")
    if len(files) != 1 or files[0]["filename"] != FORMULA or files[0]["status"] != "modified":
        raise ValueError("Automatic publishing only accepts a formula-only release bump")
    return pr


def wait_run(repo, workflow, ref, inputs, matches):
    def find():
        runs = api(f"repos/{repo}/actions/workflows/{workflow}/runs?event=workflow_dispatch&per_page=100")["workflow_runs"]
        return next((run for run in runs if matches(run)), None)

    run = find()
    if run is None:
        api(f"repos/{repo}/actions/workflows/{workflow}/dispatches", {"ref": ref, "inputs": inputs})
        for _ in range(60):
            time.sleep(2)
            run = find()
            if run:
                break
        else:
            raise TimeoutError(f"Dispatched {workflow} did not appear")
    if run["status"] != "completed":
        subprocess.run(["gh", "run", "watch", str(run["id"]), "--repo", repo,
                        "--interval", "30", "--exit-status"], check=True, timeout=3600)
    result = api(f"repos/{repo}/actions/runs/{run['id']}")
    if result["conclusion"] != "success":
        raise RuntimeError(f"{workflow} failed; inspect/rerun {result['html_url']} before retrying")


def main():
    repo = os.environ["GITHUB_REPOSITORY"]
    if repo != "wasichu/homebrew-tap":
        raise ValueError("This release handoff is restricted to wasichu/homebrew-tap")
    release = api(f"repos/{UPSTREAM}/releases/latest")
    tag = release["tag_name"]
    version(tag)
    if release["draft"] or release["prerelease"]:
        raise ValueError("Only published stable releases may be distributed")
    base = formula(repo, "main")
    if version(formula_tag(base)) >= version(tag):
        print(f"go-whassup is current ({formula_tag(base)}); nothing to publish.")
        return
    branch = f"bump-go-whassup-{tag[1:]}"
    prs = api(f"repos/{repo}/pulls?state=open&head=wasichu:{branch}&per_page=100")
    digest = checksum(tag)
    if not prs:
        # Livecheck can lag or see an unpublished tag. Ensure the published
        # stable release gets its own normal Homebrew bump PR.
        subprocess.run([
            "brew", "bump-formula-pr", "--no-fork", "--no-browse",
            f"--url=https://github.com/{UPSTREAM}/archive/refs/tags/{tag}.tar.gz",
            f"--sha256={digest}", "wasichu/tap/go-whassup",
        ], check=True)
        prs = api(f"repos/{repo}/pulls?state=open&head=wasichu:{branch}&per_page=100")
    if len(prs) != 1:
        raise ValueError(f"Expected exactly one release bump PR on {branch}")
    number, sha = prs[0]["number"], prs[0]["head"]["sha"]
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Invalid PR commit")
    check_pr(repo, number, sha)
    validate_formula(base, formula(repo, sha), tag, digest)
    print(f"Validating {tag} in PR #{number} at {sha}", flush=True)
    wait_run(repo, "tests.yml", branch, {"formula": "go-whassup", "head_sha": sha},
             lambda run: run["head_sha"] == sha)
    check_pr(repo, number, sha)
    current = api(f"repos/{UPSTREAM}/releases/tags/{tag}")
    if current["draft"] or current["prerelease"]:
        raise ValueError("Release was withdrawn while building")
    # A moving base must be reviewed again, not silently cherry-picked.
    if formula(repo, "main") != base:
        raise ValueError("Formula changed while building; retry against the new base")
    title = f"Homebrew PR #{number} ({sha})"
    wait_run(repo, "publish.yml", "main", {"pull_request": str(number), "head_sha": sha},
             lambda run: run["display_title"] == title)
    if formula_tag(formula(repo, "main")) != tag:
        raise RuntimeError("Publisher finished without updating the formula")
    print(f"Published {tag} to Homebrew.")


if __name__ == "__main__":
    main()
