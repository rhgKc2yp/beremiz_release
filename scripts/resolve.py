#!/usr/bin/env python3
"""Resolve official release sources and upstream's dependency revisions."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import urllib.request

RECIPE = "d80eb660b83473df8e767f28f6980ecbaa9e1024"


def get(url):
    headers = {"User-Agent": "beremiz-community-release"}
    if url.startswith("https://api.github.com/") and os.getenv("GH_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["GH_TOKEN"]
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as response:
        return response.read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="")
    parser.add_argument("--revision", default="1")
    args = parser.parse_args()
    if not re.fullmatch(r"[1-9][0-9]*", args.revision):
        parser.error("revision must be a positive integer")
    endpoint = "tags/" + args.tag if args.tag else "latest"
    release = json.loads(get("https://api.github.com/repos/beremiz/beremiz/releases/" + endpoint))
    tag = release["tag_name"]
    if release["draft"] or release["prerelease"] or not re.fullmatch(r"v[0-9]+(?:\.[0-9]+)+", tag):
        raise SystemExit("Only stable upstream version tags are accepted")
    recipe = get(f"https://raw.githubusercontent.com/beremiz/beremiz_public_dist/{RECIPE}/.github/workflows/prep_sources.yml").decode()
    pins = dict(re.findall(r"^\s*(\w+)_revisionid:\s*([0-9a-f]{40})", recipe, re.M))
    sources = {"beremiz": ("beremiz/beremiz", tag),
               "matiec": ("beremiz/matiec", pins["matiec"]),
               "Modbus": ("beremiz/Modbus", pins["Modbus"]),
               "canfestival": ("beremiz/canfestival", pins["canfestival"]),
               "open62541": ("open62541/open62541", pins["open62541"])}
    root = Path("build/sources")
    root.mkdir(parents=True, exist_ok=True)
    records = {}
    for name, (repo, ref) in sources.items():
        commit = json.loads(get(f"https://api.github.com/repos/{repo}/commits/{ref}"))["sha"] if name == "beremiz" else ref
        url = f"https://codeload.github.com/{repo}/tar.gz/{commit}"
        archive = root / (name + ".tar.gz")
        archive.write_bytes(get(url))
        destination = root / name
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir()
        subprocess.run(["tar", "--no-same-owner", "--strip-components=1", "-xzf", str(archive), "-C", str(destination)], check=True)
        records[name] = {"repository": repo, "commit": commit, "url": url,
                         "sha256": hashlib.sha256(archive.read_bytes()).hexdigest()}
    lock = {"tag": tag + "-" + args.revision, "upstream_tag": tag,
            "release_url": release["html_url"], "release_date": release["published_at"][:10],
            "recipe_commit": RECIPE, "runtime": "org.gnome.Platform//51",
            "sdk": "org.gnome.Sdk//51", "sources": records}
    Path("build/inputs.lock.json").write_text(json.dumps(lock, indent=2) + "\n")
    print(lock["tag"])


if __name__ == "__main__":
    main()
