"""Command-line interface for cronwrap."""

import argparse
import sys
from typing import List, Optional

from cronwrap.runner import RunnerConfig, run_job
from cronwrap.notifier import NotifierConfig, send_failure_email


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronwrap",
        description="Lightweight wrapper around cron jobs with retry logic and failure notifications.",
    )
    parser.add_argument(
        "command",
        nargs=argparse.REMAINDER,
        help="The command to run (everything after --).",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=0,
        metavar="N",
        help="Number of times to retry on failure (default: 0).",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=0.0,
        metavar="SECONDS",
        help="Seconds to wait between retries (default: 0).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Maximum seconds the command may run before being killed.",
    )
    parser.add_argument(
        "--job-name",
        default=None,
        metavar="NAME",
        help="Human-readable job name used in notifications.",
    )
    parser.add_argument(
        "--notify-email",
        default=None,
        metavar="ADDRESS",
        help="Email address to notify on failure.",
    )
    parser.add_argument(
        "--smtp-host",
        default="localhost",
        metavar="HOST",
        help="SMTP host for sending notifications (default: localhost).",
    )
    parser.add_argument(
        "--smtp-port",
        type=int,
        default=25,
        metavar="PORT",
        help="SMTP port (default: 25).",
    )
    parser.add_argument(
        "--from-email",
        default="cronwrap@localhost",
        metavar="ADDRESS",
        help="Sender address for notification emails.",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    command = [c for c in args.command if c != "--"]
    if not command:
        parser.error("No command provided. Use: cronwrap [options] -- <command>")

    job_name = args.job_name or " ".join(command)

    runner_cfg = RunnerConfig(
        command=command,
        retries=args.retries,
        retry_delay=args.retry_delay,
        timeout=args.timeout,
    )

    result = run_job(runner_cfg)

    if not result.success and args.notify_email:
        notifier_cfg = NotifierConfig(
            job_name=job_name,
            to_email=args.notify_email,
            from_email=args.from_email,
            smtp_host=args.smtp_host,
            smtp_port=args.smtp_port,
        )
        send_failure_email(notifier_cfg, result)

    return 0 if result.success else 1


if __name__ == "__main__":
    sys.exit(main())
