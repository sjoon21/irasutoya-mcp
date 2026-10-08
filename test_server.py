import asyncio
import json

import pytest
from fastmcp import Client
from fastmcp.utilities.types import Image

import server
from server import IMAGE_HOST, merge, mcp, resize


def test_resize_replaces_size_segment():
    url = "https://blogger.googleusercontent.com/img/b/abc/s72-c/monkey.png"
    assert resize(url, "s1000") == "https://blogger.googleusercontent.com/img/b/abc/s1000/monkey.png"


def test_merge_dedupes_and_ranks_by_hit_count():
    a, b, c = ({"page_url": u} for u in ("a", "b", "c"))
    assert merge([[a, b], [c, b]], limit=10) == [b, a, c]
    assert merge([[a, b], [c, b]], limit=1) == [b]


def test_search_survives_failed_thumbnail(monkeypatch):
    posts = [{"page_url": u, "image_url": f"https://{IMAGE_HOST}/s72-c/{u}.png"} for u in ("ok", "broken")]

    async def fake_search(client, keyword, limit):
        return posts

    async def fake_thumb(client, image_url):
        if "broken" in image_url:
            raise RuntimeError("503")
        return Image(data=b"\x89PNG", format="png")

    monkeypatch.setattr(server, "search_one", fake_search)
    monkeypatch.setattr(server, "fetch_thumb", fake_thumb)

    async def run():
        async with Client(mcp) as client:
            return await client.call_tool("search_illustrations", {"keywords_ja": ["x"]})

    res = asyncio.run(run())
    assert [c.type for c in res.content] == ["text", "image"]
    assert [p["has_thumbnail"] for p in json.loads(res.content[0].text)] == [True, False]


@pytest.mark.integration
def test_search_and_download_via_mcp(tmp_path):
    async def run():
        async with Client(mcp) as client:
            res = await client.call_tool("search_illustrations", {"keywords_ja": ["猿 バナナ", "サル バナナ"], "limit": 3})
            kinds = [c.type for c in res.content]
            assert kinds[0] == "text" and "image" in kinds
            image_url = res.content[0].text.split('"image_url": "')[1].split('"')[0]

            res = await client.call_tool("download_illustration", {"image_url": image_url, "dest_dir": str(tmp_path)})
            saved = tmp_path / res.content[0].text.rsplit("/", 1)[1]
            assert saved.read_bytes()[:4] == b"\x89PNG"

            with pytest.raises(Exception):
                await client.call_tool("download_illustration", {"image_url": "https://evil.example/x.png", "dest_dir": str(tmp_path)})

    asyncio.run(run())
