#!/bin/sh
# Existing system Python only. No installation, updates or private environment.
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd) || exit 1
for name in python3.15 python3.14 python3.13 python3.12 python3.11 python3.10 python3; do
    candidate=$(command -v "$name") || continue
    version=$("$candidate" -I "$ROOT/tools/probe_system_python.py" 2>/dev/null) || continue
    case "$version" in
        3.[1-9][0-9]*|[4-9].*) ;;
        *) continue ;;
    esac
    if "$candidate" -I "$ROOT/tools/probe_app_python.py"; then
        cd -- "$ROOT" || exit 1
        exec "$candidate" "$ROOT/main.pyw" "$@"
    fi
done
printf '%s\n' 'Ingen befintlig system-Python med fungerande app-tillagg hittades. Se README; ingen Python installerades.' >&2
exit 1
