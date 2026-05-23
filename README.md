# cronwrap

A lightweight wrapper around cron jobs that adds retry logic and failure notifications.

## Installation

```bash
pip install cronwrap
```

## Usage

Wrap any cron command with `cronwrap` to automatically retry on failure and receive notifications:

```bash
# Basic usage with retry and email notification
cronwrap --retries 3 --notify you@example.com -- /path/to/your/script.sh

# With a delay between retries (in seconds)
cronwrap --retries 3 --retry-delay 10 --notify you@example.com -- python backup.py
```

In your crontab:

```
0 2 * * * cronwrap --retries 3 --notify ops@example.com -- /usr/local/bin/backup.sh
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--retries` | Number of retry attempts on failure | `0` |
| `--retry-delay` | Seconds to wait between retries | `5` |
| `--notify` | Email address to notify on final failure | None |
| `--timeout` | Max execution time in seconds | None |

### Python API

```python
from cronwrap import CronWrap

job = CronWrap(
    command="python backup.py",
    retries=3,
    retry_delay=10,
    notify="ops@example.com"
)

job.run()
```

## Requirements

- Python 3.8+
- A configured mail transfer agent (MTA) for email notifications

## License

MIT