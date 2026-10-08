import asyncio
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

import httpx
from fastmcp import FastMCP
from fastmcp.utilities.types import Image
from mcp.types import ToolAnnotations

FEED_URL = "https://www.irasutoya.com/feeds/posts/summary"
IMAGE_HOST = "blogger.googleusercontent.com"
THUMB_SIZE = "s200"
ORIGINAL_SIZE = "s1000"  # ponytail: s1000 기준, 원본 해상도 경로(s0 등)는 미검증
MAX_LIMIT = 20
SIZE_SEGMENT = re.compile(r"/s\d+(-c)?/")
HEADERS = {"User-Agent": "irasutoya-mcp/0.1 (personal use)"}

mcp = FastMCP("irasutoya")


def resize(url: str, size: str) -> str:
    return SIZE_SEGMENT.sub(f"/{size}/", url, count=1)


def parse_entry(entry: dict) -> dict | None:
    thumb = entry.get("media$thumbnail", {}).get("url")
    if not thumb:
        return None
    page_url = next(l["href"] for l in entry["link"] if l["rel"] == "alternate")
    return {
        "title": entry["title"]["$t"],
        "labels": [c["term"] for c in entry.get("category", [])],
        "description": entry.get("summary", {}).get("$t", "").strip(),
        "page_url": page_url,
        "image_url": resize(thumb, ORIGINAL_SIZE),
    }


async def search_one(client: httpx.AsyncClient, keyword: str, limit: int) -> list[dict]:
    resp = await client.get(FEED_URL, params={"alt": "json", "q": keyword, "max-results": limit})
    resp.raise_for_status()
    entries = resp.json()["feed"].get("entry", [])
    return [p for p in map(parse_entry, entries) if p]


def merge(results: list[list[dict]], limit: int) -> list[dict]:
    """여러 표기로 검색한 결과를 합친다. 더 많은 키워드에 걸린 게시물이 앞에 온다."""
    hits = Counter(p["page_url"] for posts in results for p in posts)
    by_url = {p["page_url"]: p for posts in results for p in posts}
    ranked = sorted(by_url, key=lambda u: -hits[u])  # sorted는 안정 정렬이라 동점이면 먼저 나온 순서를 유지함
    return [by_url[u] for u in ranked[:limit]]


async def fetch_thumb(client: httpx.AsyncClient, image_url: str) -> Image:
    resp = await client.get(resize(image_url, THUMB_SIZE))
    resp.raise_for_status()
    fmt = "jpeg" if image_url.lower().endswith((".jpg", ".jpeg")) else "png"
    return Image(data=resp.content, format=fmt)


@mcp.tool(
    annotations=ToolAnnotations(title="Search irasutoya illustrations", readOnlyHint=True, openWorldHint=True)
)
async def search_illustrations(keywords_ja: list[str], limit: int = 8) -> list:
    """Search いらすとや (irasutoya.com) free illustrations.

    keywords_ja: Japanese noun keywords. Search is exact-orthography, so pass several
    spellings of the same concept (e.g. ["猿 バナナ", "サル バナナ", "猿"]); results are merged.
    Returns a JSON list (title, labels, description, page_url, image_url, has_thumbnail)
    followed by thumbnail images, in the same order, for the results whose has_thumbnail is true.
    """
    keywords = [k.strip() for k in keywords_ja if k.strip()]
    if not keywords:
        raise ValueError("keywords_ja must contain at least one non-empty keyword")
    limit = max(1, min(limit, MAX_LIMIT))

    async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
        results = await asyncio.gather(*(search_one(client, k, limit) for k in keywords))
        posts = merge(results, limit)
        # 썸네일은 보조 정보라 일부가 실패해도 검색 결과는 그대로 돌려줌
        thumbs = await asyncio.gather(
            *(fetch_thumb(client, p["image_url"]) for p in posts), return_exceptions=True
        )

    ok = [not isinstance(t, BaseException) for t in thumbs]
    posts = [{**p, "has_thumbnail": has} for p, has in zip(posts, ok)]
    images = [t for t, has in zip(thumbs, ok) if has]
    meta = json.dumps(posts, ensure_ascii=False, indent=1) if posts else f"No results for {keywords}"
    return [meta, *images]


@mcp.tool(
    annotations=ToolAnnotations(
        title="Download irasutoya illustration",
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    )
)
async def download_illustration(image_url: str, dest_dir: str) -> str:
    """Download an illustration PNG (image_url from search_illustrations) into dest_dir.

    Returns the saved file path.
    """
    parsed = urlparse(image_url)
    if parsed.scheme != "https" or parsed.hostname != IMAGE_HOST:
        raise ValueError(f"image_url must be an https URL on {IMAGE_HOST}")

    dest = Path(dest_dir).expanduser()
    dest.mkdir(parents=True, exist_ok=True)
    path = dest / Path(parsed.path).name

    async with httpx.AsyncClient(headers=HEADERS, timeout=30, follow_redirects=True) as client:
        resp = await client.get(image_url)
        resp.raise_for_status()
    path.write_bytes(resp.content)
    return str(path)


if __name__ == "__main__":
    mcp.run()
