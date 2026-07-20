"""Command-line interface for CHAKRAVYUH.

    chakravyuh demo                 run the narrated demo
    chakravyuh analyze [--out DIR]  run the pipeline, optionally export a bundle
    chakravyuh serve                start the REST API (needs the [api] extra)
"""
from __future__ import annotations

import argparse
import json
import sys

from .adapters import ScenarioAdapter
from .config import load_settings
from .export import result_to_dict, write_bundle
from .orchestrator import Orchestrator
from .scenarios import redecho


def _cmd_demo(_args: argparse.Namespace) -> int:
    from .demo import main as demo_main

    return demo_main()


def _cmd_analyze(args: argparse.Namespace) -> int:
    orch = Orchestrator()
    result = orch.run_adapter(ScenarioAdapter(redecho))
    if args.out:
        paths = write_bundle(result, orch, args.out)
        print(json.dumps(paths, indent=2))
    else:
        print(json.dumps(result_to_dict(result, orch), indent=2, default=str))
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    try:
        import uvicorn
    except ImportError:
        print("The API needs the [api] extra:  pip install 'chakravyuh[api]'",
              file=sys.stderr)
        return 2
    settings = load_settings()
    uvicorn.run(
        "chakravyuh.api.app:app",
        host=args.host or settings.api_host,
        port=args.port or settings.api_port,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="chakravyuh")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("demo", help="run the narrated demo")

    p_analyze = sub.add_parser("analyze", help="run the pipeline")
    p_analyze.add_argument("--out", help="directory to write an incident bundle")

    p_serve = sub.add_parser("serve", help="start the REST API")
    p_serve.add_argument("--host", default=None)
    p_serve.add_argument("--port", type=int, default=None)

    args = parser.parse_args(argv)
    return {
        "demo": _cmd_demo,
        "analyze": _cmd_analyze,
        "serve": _cmd_serve,
    }[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
