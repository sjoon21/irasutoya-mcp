# irasutoya-mcp

[いらすとや](https://www.irasutoya.com) 일러스트를 검색하고 내려받는 MCP 서버입니다. 검색 결과를 썸네일 이미지로 함께 돌려주므로, AI가 그림을 직접 보고 포스터나 슬라이드에 맞는 소재를 고를 수 있습니다.

> 이라스토야와 관계없는 비공식 도구입니다. 이 저장소는 이미지를 포함하거나 재배포하지 않습니다. 이미지는 이라스토야 [이용 약관](https://www.irasutoya.com/p/faq.html)에 따라 사용해야 합니다.

## Tool

| Tool | 동작 | 입력 |
|---|---|---|
| `search_illustrations` | 검색 결과 JSON(제목, 라벨, 설명, 원본 URL)과 200px 썸네일 이미지를 반환합니다. 읽기 전용입니다. | `keywords_ja: list[str]`, `limit: int = 8` |
| `download_illustration` | 원본 PNG를 지정한 폴더에 저장하고 경로를 반환합니다. | `image_url: str`, `dest_dir: str` |
## 설치

[uv](https://docs.astral.sh/uv/)가 필요합니다.

```bash
git clone https://github.com/sjoon21/irasutoya-mcp
cd irasutoya-mcp
uv sync
```

### Claude Code

이 폴더에서 `claude`를 실행하면 `.mcp.json`에 등록된 서버가 자동으로 잡힙니다. 다른 폴더에서도 쓰려면 사용자 범위로 등록합니다.

```bash
claude mcp add -s user irasutoya -- uv run --directory /path/to/irasutoya-mcp server.py
```

### Claude Desktop, Cursor

설정 파일의 `mcpServers`에 아래 항목을 추가합니다.

```json
{
  "irasutoya": {
    "command": "uv",
    "args": ["run", "--directory", "/path/to/irasutoya-mcp", "server.py"]
  }
}
```

## 사용 예

> 회사 송년회 포스터에 쓸 일러스트 3개를 골라서 `~/Downloads/poster`에 받아줘.

## 이용 약관 요약

- 상업적 이용은 제작물 하나당 20점까지 가능합니다.
- 가공 여부와 관계없이 소재를 재배포하면 안 됩니다.
- 이라스토야 그림인지 알아볼 수 없게 만드는 가공은 자제해 달라고 요청하고 있습니다.

## 개발

```bash
uv run pytest -q                       # 전체 테스트 (실제 네트워크 사용)
uv run pytest -q -m "not integration"  # 단위 테스트만
```

설계 결정과 피드 구조는 [`CLAUDE.md`](CLAUDE.md)에 정리되어 있습니다.

## License

MIT
