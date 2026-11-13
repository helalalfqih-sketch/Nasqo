"""Trusted local operator CLI. No public SaaS control-plane API in this pilot."""
import argparse
import json
from pathlib import Path
import sys

from .backup import backup, restore
from .registry import Registry, provision
from .runtime import ROOT, Runtime, preflight


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", type=Path, default=ROOT / ".m2")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("provision")
    create.add_argument("slug")
    create.add_argument("--key", required=True, help="A non-secret idempotency key (16–200 characters)")
    commands.add_parser("status")
    commands.add_parser("gateway")
    for name in ("backup", "restore"):
        command = commands.add_parser(name)
        command.add_argument("slug")
        command.add_argument("--key-file", required=True, type=Path)
        if name == "restore":
            command.add_argument("--archive", required=True, type=Path)
    args = parser.parse_args()
    if args.command != "status":
        preflight()
    registry = Registry(args.state)
    runtime = Runtime(registry)
    try:
        if args.command == "status":
            print(json.dumps([{k: s[k] for k in ("slug", "state", "phase", "error_code")} for s in registry.stores()]))
        elif args.command == "provision":
            store = provision(registry, runtime, args.slug, args.key)
            print(json.dumps({"slug": store["slug"], "state": store["state"]}))
        elif args.command == "gateway":
            with registry.lock():
                runtime.gateway()
            print("Gateway ready on loopback port 18069; use <slug>.nasqo.test Host.")
        elif args.command == "backup":
            print(backup(registry, runtime, args.slug, args.key_file))
        else:
            restored, store = restore(registry, args.slug, args.archive, args.key_file)
            print(json.dumps({"slug": store["slug"], "restore_project": restored.project(store), "public_route": False}))
    finally:
        registry.close()


if __name__ == "__main__":
    try:
        main()
    except (ValueError, PermissionError, RuntimeError, OSError) as error:
        print(f"M2 operation failed: {error}", file=sys.stderr)
        sys.exit(1)
