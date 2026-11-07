#!/bin/sh
# ai-sdlc-kit hook shim: finds a Python 3 and runs sdlc_hooks.py with the given subcommand.
# Fails open: with no usable Python it allows everything (and warns for secret checks).
# Turn every kit hook off with SDLC_HOOKS=off. Force an interpreter with SDLC_PYTHON=/path/to/python.

case "${SDLC_HOOKS:-}" in off|OFF|Off|0|false|no) exit 0 ;; esac
sub=${1:-}

# Fast paths that skip Python entirely (Python start-up costs 0.2-0.5 s on Windows).
cfg="${CLAUDE_PROJECT_DIR:-}/.sdlc/gates.json"
case "$sub" in
  post-write)
    # Only the optional formatter runs here.
    if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
      [ -f "$cfg" ] || exit 0
      grep -q '"format"' "$cfg" 2>/dev/null || exit 0
    fi
    ;;
  stop)
    if [ -n "${CLAUDE_PROJECT_DIR:-}" ]; then
      [ -f "$cfg" ] || exit 0
      grep -q '"stop"' "$cfg" 2>/dev/null || exit 0
    fi
    ;;
  pre-bash)
    # Every rule needs either a git command or a secret-looking file name in the command.
    input=$(cat)
    case "$input" in
      *git*|*.env*|*.pem*|*.key*|*.p12*|*.pfx*|*id_rsa*|*id_ed25519*|*id_ecdsa*|*id_dsa*) ;;
      *) exit 0 ;;
    esac
    ;;
esac

case "$0" in
  *\\*) self=$(printf '%s' "$0" | tr '\\' '/') ;;
  *) self=$0 ;;
esac
dir=${self%/*}
[ "$dir" = "$self" ] && dir=.
script="$dir/sdlc_hooks.py"
export PYTHONIOENCODING=utf-8 PYTHONUTF8=1 PYTHONDONTWRITEBYTECODE=1

py=""
extra=""
if [ -n "${SDLC_PYTHON:-}" ]; then
  py=$SDLC_PYTHON
else
  if [ "${OS:-}" = Windows_NT ]; then candidates="python py python3"; else candidates="python3 python"; fi
  # First choice: an interpreter outside WindowsApps (there, python/python3 are often Store stubs).
  for c in $candidates; do
    p=$(command -v "$c" 2>/dev/null) || continue
    case "$p" in *WindowsApps*) continue ;; esac
    py=$c
    break
  done
  # Fallback: probe WindowsApps aliases (a real Store install also lives there).
  if [ -z "$py" ]; then
    for c in $candidates; do
      command -v "$c" >/dev/null 2>&1 || continue
      if "$c" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" </dev/null >/dev/null 2>&1; then
        py=$c
        break
      fi
    done
  fi
fi

if [ -z "$py" ]; then
  case "$sub" in
    pre-write|pre-bash) echo "ai-sdlc-kit: no Python 3 found; secret and command checks skipped" >&2 ;;
  esac
  exit 0
fi
[ "$py" = py ] && extra="-3"

if [ "$sub" = pre-bash ]; then
  printf '%s\n' "$input" | "$py" $extra "$script" "$@"
  exit 0
fi
exec "$py" $extra "$script" "$@"
