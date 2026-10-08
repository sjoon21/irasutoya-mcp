# irasutoya-mcp

[한국어](README.md) | **English** | [日本語](README.ja.md)

An MCP server that searches and downloads illustrations from [いらすとや (Irasutoya)](https://www.irasutoya.com). Search results come back with thumbnail images, so the AI can actually see each illustration and pick the right one for your poster or slides.

> This is an unofficial tool, not affiliated with Irasutoya. This repository does not contain or redistribute any images. Use the images in accordance with Irasutoya's [terms of use](https://www.irasutoya.com/p/faq.html).

## Tools

| Tool | What it does | Input |
|---|---|---|
| `search_illustrations` | Returns search results as JSON (title, labels, description, original image URL) plus a 200px thumbnail image for each result. Read-only. | `keywords_ja: list[str]`, `limit: int = 8` |
| `download_illustration` | Saves the original PNG to the given directory and returns the file path. | `image_url: str`, `dest_dir: str` |

## Installation

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/sjoon21/irasutoya-mcp
cd irasutoya-mcp
uv sync
```

### Claude Code

Run `claude` inside this directory and the server registered in `.mcp.json` is picked up automatically. To use it from any directory, register it at user scope:

```bash
claude mcp add -s user irasutoya -- uv run --directory /path/to/irasutoya-mcp server.py
```

### Claude Desktop, Cursor

Add the following entry under `mcpServers` in the config file:

```json
{
  "irasutoya": {
    "command": "uv",
    "args": ["run", "--directory", "/path/to/irasutoya-mcp", "server.py"]
  }
}
```

## Example

> Pick three illustrations for our company year-end party poster and save them to `~/Downloads/poster`.

## Terms of use (summary)

- Commercial use is allowed for up to 20 illustrations per work.
- Redistributing the materials is not allowed, whether modified or not.
- Irasutoya asks that you avoid edits that make the illustration unrecognizable as Irasutoya's.

## Development

```bash
uv run pytest -q                       # all tests (hits the real network)
uv run pytest -q -m "not integration"  # unit tests only
```

Design decisions and the feed structure are documented in [`CLAUDE.md`](CLAUDE.md) (Korean).

## License

MIT
