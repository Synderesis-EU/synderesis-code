#!/usr/bin/env bash
# Synderesis Code native installer. No administrator access required.
set -euo pipefail

main() {
  local version='0.1.0-alpha.1'
  local platform arch asset base temp expected actual install_dir
  platform="$(uname -s)"
  arch="$(uname -m)"
  case "$platform/$arch" in
    Darwin/arm64) platform='macos-arm64' ;;
    *) printf 'No verified native release for %s/%s yet. See https://github.com/Synderesis-EU/synderesis-code/releases\n' "$platform" "$arch" >&2; return 1 ;;
  esac
  command -v curl >/dev/null || { echo 'curl is required.' >&2; return 1; }
  asset="synderesis-code-${version}-${platform}.tar.gz"
  base="https://github.com/Synderesis-EU/synderesis-code/releases/download/v${version}"
  temp="$(mktemp -d)"
  trap "rm -rf -- $(printf %q "$temp")" EXIT
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 "$base/$asset" -o "$temp/$asset"
  curl --fail --silent --show-error --location --proto '=https' --tlsv1.2 "$base/SHA256SUMS" -o "$temp/SHA256SUMS"
  expected="$(awk -v name="$asset" '$2 == name { print $1 }' "$temp/SHA256SUMS")"
  [[ "$expected" =~ ^[0-9a-f]{64}$ ]] || { echo 'Missing or invalid release checksum.' >&2; return 1; }
  actual="$(shasum -a 256 "$temp/$asset" | awk '{print $1}')"
  [[ "$actual" == "$expected" ]] || { echo 'Release checksum mismatch.' >&2; return 1; }
  mkdir "$temp/unpacked"
  tar -xzf "$temp/$asset" -C "$temp/unpacked" --strip-components=1
  install_dir="${SYNDERESIS_INSTALL_DIR:-$HOME/.local/bin}"
  mkdir -p "$install_dir"
  "$temp/unpacked/synderesis-code" --version
  install -m 755 "$temp/unpacked/synderesis-code" "$install_dir/.synderesis-code.new"
  mv -f "$install_dir/.synderesis-code.new" "$install_dir/synderesis-code"
  printf '\nInstalled to %s/synderesis-code\n' "$install_dir"
  case ":$PATH:" in
    *":$install_dir:"*) ;;
    *) printf 'Add this directory to PATH, then reopen your terminal:\n  export PATH="%s:$PATH"\n' "$install_dir" ;;
  esac
  printf 'Sign in: synderesis-code login\nStart:   synderesis-code\n'
  rm -rf -- "$temp"
  trap - EXIT
}
main "$@"
