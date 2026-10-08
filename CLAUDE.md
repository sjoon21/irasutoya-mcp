# irasutoya-mcp

이라스토야(いらすとや) 일러스트를 검색하고, 후보 썸네일을 이미지로 AI에게 보여 주고, 고른 원본 PNG를 내려받는 로컬 MCP 서버다. 포스터나 슬라이드를 만들 때 소재를 직접 찾아다니는 수고를 없애는 것이 목표다.

## 설계 결정

| 항목 | 결정 | 이유 |
|---|---|---|
| 배포 형태 | 로컬 stdio | 개인용이고, 다운로드가 로컬 파일시스템에 쓴다. 배포가 필요해지면 MCPB로 옮긴다. |
| 언어·프레임워크 | Python 3.12 + FastMCP 4.x (`fastmcp`), `httpx`, `uv` | 참고 구현이 Python이고 외부 의존성이 거의 없다. |
| Tool 패턴 | Tool 하나당 동작 하나, 2개 | 동작이 검색과 다운로드뿐이다. |
| 인증 | 없음 | Blogger 공개 피드를 쓴다. |
| 사용 클라이언트 | Claude Code, Claude Desktop, Cursor | |

## Tool 명세

### `search_illustrations` (읽기 전용)

- 입력: `keywords_ja: list[str]`, `limit: int = 8`
- 출력
  - 텍스트(JSON): 후보마다 `title`, `labels`, `description`, `page_url`, `image_urls`(원본 목록), `thumbnail_url`, `has_thumbnail`
  - 한 게시물에 변형(남녀, 색상 등)이 여러 장이면 `image_urls`에 모두 담고, 썸네일은 그 변형들을 한 장에 모은 대표 이미지를 씀
  - 이미지: `has_thumbnail`이 참인 후보만 같은 순서로 `s200` 썸네일을 `ImageContent`로 반환함
  - 썸네일 요청이 실패해도(예: `503`) 검색 결과 전체를 실패시키지 않음
- annotations: `readOnlyHint: true`, `openWorldHint: true`, `title`

### `download_illustration` (쓰기)

- 입력: `image_url: str` (`image_urls` 중 하나), `dest_dir: str`
- 동작: 원본 투명 PNG를 저장하고 저장 경로를 반환함
- annotations: `readOnlyHint: false`, `destructiveHint: false`, `openWorldHint: true`, `title`
- `image_url`의 호스트가 `blogger.googleusercontent.com`인지 검증함

읽기와 쓰기를 한 tool에 섞지 않는다. Tool description에 "항상 ~하라" 같은 행동 지시를 넣지 않는다(prompt injection으로 간주된다). 대신 "키워드는 일본어 명사를 기대한다"처럼 입력 형식을 설명한다.

## 데이터 소스: Blogger JSON 피드

이라스토야는 Blogger 위에서 운영된다. 공식 API는 없지만 Blogger 피드를 인증 없이 쓸 수 있다. 2026-10-08에 직접 호출해 확인했다.

| 용도 | 엔드포인트 |
|---|---|
| 키워드 검색 | `https://www.irasutoya.com/feeds/posts/default?alt=json&q=<키워드>&max-results=<n>` |
| 라벨 필터 | `https://www.irasutoya.com/feeds/posts/default/-/<라벨>?alt=json` |
| 페이지 넘김 | `&start-index=<n>` (1부터 시작) |

- 전체 게시물: 25,424건 (`openSearch$totalResults`)
- `summary` 피드는 응답이 약 40% 작지만 본문(`content`)이 없어 게시물의 대표 썸네일만 알 수 있다. 그래서 `default` 피드를 쓴다.
- 응답 필드 경로
  - 제목: `entry[].title.$t`
  - 라벨: `entry[].category[].term`
  - 본문 HTML: `entry[].content.$t` (개별 이미지 링크와 설명문이 들어 있음)
  - 썸네일: `entry[].media$thumbnail.url` (`s72-c` 크기)
  - 페이지 URL: `entry[].link[rel=alternate].href`
- 이미지 크기 변경: URL의 `/s72-c/`를 `/s200/`, `/s400/`, `/s0/`으로 바꾼다.
  - `s0`은 리사이즈하지 않은 원본이다. `s1000`은 1000px보다 큰 원본을 줄인다(`eto_uma_family.png`: `s1000` 469KB, `s0` 673KB).
- 한 게시물에 이미지가 여러 장인 경우: 900건 표본에서 14%였다.
  - 이런 게시물의 대표 썸네일은 여러 장을 묶은 `thumbnail_*.jpg` 콜라주다. 흰 배경 JPG라 소재로 쓸 수 없다.
  - 콜라주는 본문에도 링크로 들어 있으므로, 본문에서 이미지를 꺼낼 때 `thumbnail_` 접두사 파일은 제외한다.

## 알려진 난관

- **표기 민감도**: 검색이 표기에 매우 민감하다. `サル バナナ`는 0건이지만 `猿 バナナ`는 2건이다. `リンゴを食べる`는 0건이고 `リンゴ 食べる`는 결과가 나온다.
  - 대응: 입력을 `list[str]`로 받아 여러 표기를 병렬로 검색하고 결과를 합친다. 번역과 표기 변형은 LLM이 만든다.
  - 참고 구현: [hsol/irasutoya](https://github.com/hsol/irasutoya) (MIT). 조사 제거, 가나·한자 변환, 부분 일치 강등 로직이 있다. 코드를 가져오면 라이선스 고지를 남긴다.
- **여러 단어는 AND 검색**: 한 검색어의 단어가 모두 맞아야 결과가 나온다. 단어 수가 늘면 결과가 급격히 줄어든다.
  - 실측: `疲れた 会社員 女性 パソコン` 1건, `疲れた 女性 ノートパソコン` 0건, `疲れた 会社員` 8건, `パソコン 女性` 50건
  - 대응: tool 설명에 "검색어 하나에 1~2단어"라고 입력 형식을 적어 두었다. 적용 후 Claude가 2단어 검색어만 만들었고, 후보가 1건에서 8~10건으로 늘었다.
- **의미 검색 한계**: 피드 검색은 문자열 매칭이다. 품질이 부족하다고 확인되면 전체 메타데이터를 로컬 인덱스로 받는다(100건씩 약 255회 요청).

## 이용 약관 제약 ([FAQ](https://www.irasutoya.com/p/faq.html))

- 상업적 이용은 제작물 하나당 **20점까지** 가능하다. 같은 이미지는 1점으로 센다.
- 가공 여부와 관계없이 **소재 재배포는 금지**다. 이미지를 미러링하는 공개 서버, 공개 캐시, 공개 데이터셋을 만들지 않는다. 로컬 개인 캐시는 괜찮다.
- 원래 이미지가 유지되는 가공은 허용된다. 이라스토야 그림인지 **알아볼 수 없게 만드는 가공은 자제**를 요청한다. 이미지 생성 AI에 넣어 다시 그리게 하는 용도는 회색 지대이므로 기본 흐름으로 삼지 않는다.
- AI 학습과 스크래핑에 관한 조항은 FAQ에 없다. 그래도 요청 빈도를 제한하고 응답을 캐시한다.

## 하지 않는 것

- 원격 HTTP 배포, OAuth: 개인용이므로 필요 없다.
- 비전 모델로 전체 이미지 캡션 사전 생성: 썸네일을 직접 보여 주는 편이 싸고 정확하다.
- 로컬 전체 인덱스, 임베딩 검색: 피드 검색 품질이 부족하다고 확인된 뒤에 추가한다.

## 구조와 명령

| 파일 | 역할 |
|---|---|
| `server.py` | MCP 서버 전체 (피드 검색, 결과 병합, 두 tool) |
| `test_server.py` | 단위 테스트 2건, 실제 네트워크를 쓰는 통합 테스트 1건 |
| `.mcp.json` | Claude Code 프로젝트 범위 등록 |

```bash
uv run pytest -q                       # 전체 테스트
uv run pytest -q -m "not integration"  # 네트워크 없이 단위 테스트만
uv run python server.py                # stdio 서버 직접 실행
```

## 진행 상황

- [x] `uv` 프로젝트 생성, `fastmcp`, `httpx` 추가
- [x] 키워드 병렬 검색, 게시물 URL 기준 중복 제거, 적중 키워드 수 기준 정렬
- [x] `search_illustrations`: 텍스트 JSON과 `s200` 썸네일 `ImageContent` 반환 확인
- [x] `download_illustration`: 호스트 검증 후 PNG 저장 확인
- [x] `.mcp.json`으로 Claude Code에 등록
- [x] `claude -p`로 실제 요청 4종 확인 (포스터 소재 3장, 특정 장면, 여러 장 게시물의 특정 변형, 없는 그림의 대안 제시)
- [x] 한 게시물에 이미지가 여러 장인 경우 처리 (`default` 피드의 `content.$t` 파싱, 콜라주 제외)
- [x] 원본 해상도 경로 검증 (`s0`)
- [x] 썸네일 하나가 실패해도 검색 결과를 유지 (`has_thumbnail`)
- [ ] 같은 검색을 반복할 때 쓸 로컬 응답 캐시
