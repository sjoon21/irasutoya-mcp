# irasutoya-mcp

<img src="assets/banner.png" alt="irasutoya-mcp: search, see & pick, use いらすとや illustrations" width="100%">

[한국어](README.md) | **English** | [日本語](README.ja.md)

An MCP server that searches and downloads illustrations from [いらすとや (Irasutoya)](https://www.irasutoya.com). Search results come back with thumbnail images, so the AI can actually see each illustration and pick the right one for your poster or slides.

> This is an unofficial tool, not affiliated with Irasutoya. This repository does not redistribute any illustration materials. The banner above is a work made with いらすとや illustrations. Use the images in accordance with Irasutoya's [terms of use](https://www.irasutoya.com/p/faq.html).

## Tools

| Tool | What it does | Input |
|---|---|---|
| `search_illustrations` | Returns search results as JSON (title, labels, description, original image URLs) plus a 200px thumbnail image for each result. When a post has several variants (e.g. male/female, colors), every original URL is included. Read-only. | `keywords_ja: list[str]`, `limit: int = 8` |
| `download_illustration` | Saves the original PNG to the given directory and returns the file path. | `image_url: str`, `dest_dir: str` |

## Installation

All you need is [uv](https://docs.astral.sh/uv/). No need to clone the repository.

### Claude Code

```bash
claude mcp add -s user irasutoya -- uvx --from git+https://github.com/sjoon21/irasutoya-mcp irasutoya-mcp
```

### Claude Desktop, Cursor

Add the following entry under `mcpServers` in the config file:

```json
{
  "irasutoya": {
    "command": "uvx",
    "args": ["--from", "git+https://github.com/sjoon21/irasutoya-mcp", "irasutoya-mcp"]
  }
}
```

If Claude Desktop on macOS can't find `uvx`, put its absolute path in `command` (the output of `which uvx`, e.g. `/Users/<you>/.local/bin/uvx`).

### Updating

`uvx` caches the version it first downloaded. To get the latest version, run the command below once and restart your client.

```bash
uvx --refresh --from git+https://github.com/sjoon21/irasutoya-mcp irasutoya-mcp </dev/null
```

## Example

> Pick three illustrations for our company year-end party poster and save them to `~/Downloads/poster`.

## Terms of use (summary)

- Commercial use is allowed for up to 20 illustrations per work.
- Redistributing the materials is not allowed, whether modified or not.
- Irasutoya asks that you avoid edits that make the illustration unrecognizable as Irasutoya's.

## Development

```bash
git clone https://github.com/sjoon21/irasutoya-mcp && cd irasutoya-mcp && uv sync
uv run pytest -q                       # all tests (hits the real network)
uv run pytest -q -m "not integration"  # unit tests only
```

Design decisions and the feed structure are documented in [`CLAUDE.md`](CLAUDE.md) (Korean).

## License

MIT
