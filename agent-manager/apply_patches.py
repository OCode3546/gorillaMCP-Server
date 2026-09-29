"""Apply patch artifacts into a git repo and create a commit/branch.

Usage:
  python apply_patches.py --repo /path/to/repo --patch outgoing_patches/xyz.patch --branch apply/patch-xyz --message "Apply agent patch"

Notes:
- This script shells out to `git` and must be run where git is available and the repo is clean or changes understood.
- It will create the branch, apply the patch with `git apply --index`, and commit.
"""
import argparse
import json
import os
import subprocess


def run_git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--patch", required=True)
    p.add_argument("--branch", required=True)
    p.add_argument("--message", default="Apply agent patch")
    args = p.parse_args(argv)

    repo = os.path.abspath(args.repo)
    if not os.path.isdir(repo):
        print(json.dumps({"status": "failed", "summary": "Repo not found"}))
        return 2

    steps = [
        (("checkout", "-b", args.branch), "Failed to create branch"),
        (("apply", "--index", os.path.abspath(args.patch)), "Failed to apply patch"),
        (("commit", "-m", args.message), "Failed to commit patch"),
    ]
    for git_args, failure in steps:
        r = run_git(repo, *git_args)
        if r.returncode != 0:
            print(json.dumps({"status": "failed", "summary": failure, "stderr": r.stderr}))
            return 2

    print(json.dumps({"status": "success", "summary": "Applied patch and committed", "branch": args.branch}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
