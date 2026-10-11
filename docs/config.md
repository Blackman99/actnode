# Configuration

actnode has no config file. Everything is a flag or an environment variable.

| Setting | How | Default |
|---|---|---|
| Minimum Node major | `--target 24` | 24 |
| GitHub token | `GITHUB_TOKEN` or `GH_TOKEN` env | none (60 API requests/hour) |
| Composite depth | fixed at 3 levels | 3 |

## Choosing the target

GitHub runners support `node24` today. When a newer runtime arrives, run `actnode --target 26` to see what still needs to move.
