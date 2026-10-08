import asyncio
import json

import pytest
from fastmcp import Client
from fastmcp.utilities.types import Image

import irasutoya_mcp as server
from irasutoya_mcp import IMAGE_HOST, merge, mcp, parse_entry, resize


def test_resize_replaces_size_segment():
    url = "https://blogger.googleusercontent.com/img/b/abc/s72-c/monkey.png"
    assert resize(url, "s1000") == "https://blogger.googleusercontent.com/img/b/abc/s1000/monkey.png"


def test_merge_dedupes_and_ranks_by_hit_count():
    a, b, c = ({"page_url": u} for u in ("a", "b", "c"))
    assert merge([[a, b], [c, b]], limit=10) == [b, a, c]
    assert merge([[a, b], [c, b]], limit=1) == [b]


def test_parse_entry_returns_every_image_of_a_collage_post_at_original_size():
    base = f"https://{IMAGE_HOST}/img/b/x"
    entry = {
        "title": {"$t": "色々な額縁のイラスト"},
        "category": [{"term": "美術"}],
        "link": [{"rel": "alternate", "href": "https://www.irasutoya.com/frame.html"}],
        "media$thumbnail": {"url": f"{base}/s72-c/thumbnail_frame.jpg"},
        "content": {"$t": (
            f'<div><a href="{base}/s1600/thumbnail_frame.jpg"><img src="{base}/s400/thumbnail_frame.jpg" /></a>'
            f'<a href="{base}/s1000/painting_frame1.png"><img src="{base}/s400/painting_frame1.png" /></a>'
            f'<a href="{base}/s1000/painting_frame2.png"><img src="{base}/s400/painting_frame2.png" /></a>'
            "<br />いろいろな額縁の\nイラストです。</div>"
        )},
    }
    post = parse_entry(entry)
    assert post["image_urls"] == [f"{base}/s0/painting_frame1.png", f"{base}/s0/painting_frame2.png"]
    assert post["thumbnail_url"] == f"{base}/s72-c/thumbnail_frame.jpg"
    assert post["description"] == "いろいろな額縁の イラストです。"
    assert post["labels"] == ["美術"]


def test_search_survives_failed_thumbnail(monkeypatch):
    posts = [{"page_url": u, "thumbnail_url": f"https://{IMAGE_HOST}/s72-c/{u}.png"} for u in ("ok", "broken")]

    async def fake_search(client, keyword, limit):
        return posts

    async def fake_thumb(client, thumbnail_url):
        if "broken" in thumbnail_url:
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
            image_url = json.loads(res.content[0].text)[0]["image_urls"][0]

            res = await client.call_tool("download_illustration", {"image_url": image_url, "dest_dir": str(tmp_path)})
            saved = tmp_path / res.content[0].text.rsplit("/", 1)[1]
            assert saved.read_bytes()[:4] == b"\x89PNG"

            with pytest.raises(Exception):
                await client.call_tool("download_illustration", {"image_url": "https://evil.example/x.png", "dest_dir": str(tmp_path)})

    asyncio.run(run())
