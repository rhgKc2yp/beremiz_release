#!/usr/bin/env bash
# Creates the explicitly requested repository and starts its verified release job.
# Does not open a FlatPark PR or contact upstream.
set -euo pipefail
cd "$(dirname "$0")/.."
repo="${1:?usage: publish-github.sh OWNER/beremiz_release}"
[[ "$repo" =~ ^[A-Za-z0-9-]+/beremiz_release$ ]] || { echo 'Expected OWNER/beremiz_release' >&2; exit 1; }
gh auth status
[ -z "$(git status --porcelain)" ] || { echo 'Commit the reviewed build recipe first' >&2; exit 1; }
if git remote get-url origin >/dev/null 2>&1; then
    remote=$(git remote get-url origin)
    case "$remote" in
        "https://github.com/$repo.git"|"git@github.com:$repo.git") ;;
        *) echo "Origin does not match $repo" >&2; exit 1 ;;
    esac
    git push -u origin main
else
    gh repo create "$repo" --public --source . --remote origin --push
fi
gh workflow run release.yml -R "$repo" --ref main -f publish=true -f revision=1
echo "Build and release: https://github.com/$repo/actions/workflows/release.yml"
