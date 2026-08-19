#!/usr/bin/env bash
set -euo pipefail

# Load common shell startup files so non-interactive runs can still access env vars.
for f in "$HOME/.bash_profile" "$HOME/.zprofile" "$HOME/.zshrc" "$HOME/.bashrc"; do
  if [[ -f "$f" ]]; then
    # shellcheck disable=SC1090
    source "$f"
  fi
done

: "${XFYUN_APPID:?Missing XFYUN_APPID after loading shell profiles}"
: "${XFYUN_API_KEY:?Missing XFYUN_API_KEY after loading shell profiles}"
: "${XFYUN_API_SECRET:?Missing XFYUN_API_SECRET after loading shell profiles}"

if [[ $# -eq 0 ]]; then
  echo "Usage: with_xfyun_env.sh <command> [args...]" >&2
  exit 2
fi

exec "$@"
