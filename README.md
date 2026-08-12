# onbid-mcp

**온비드(공매) MCP 서버 — 차세대 API 대응.**

원본 프로젝트에서 *"유지보수 불가"* 로 제거된 온비드 기능을, 이관된 신규 엔드포인트로 되살렸습니다.
9종 전부 실제 호출로 검증했습니다.

```
차량 목록      258건        동산 목록      2,650건       공고 목록       590건
용도 코드      420건        물건 소재지    17,744건      물건(낙찰결과)  53,804건
차량 상세      85개 필드    동산 상세      93개 필드     입찰 조건       17개 필드
```

---

## 왜 이 저장소가 있나

[tae0y/real-estate-mcp](https://github.com/tae0y/real-estate-mcp)는 국토교통부 실거래가 등을
MCP로 제공하는 훌륭한 프로젝트입니다. 여기에 온비드(공매) 도구 11종이 있었지만,
2026년 7월 **의도적으로 제거**됐습니다.

> **[BREAKING CHANGES] Remove Onbid (공매) tools (#31)**
> Onbid's API required repeated patches, making it unsustainable to maintain as a
> personal project (announced deprecation, effective 2026-06-01).

타당한 판단이었습니다. 실제로 온비드 API는 예고 없이 갈아엎어졌고, 구 엔드포인트는
**지금도 응답하지 않습니다.**

그런데 확인해보니 **폐기가 아니라 이관**이었습니다. 캠코가 *차세대 온비드*로 옮기면서
서비스 주소·응답 스키마·필수 파라미터를 전부 바꿨고, 공지가 눈에 띄지 않았을 뿐입니다.

이 저장소는 그 이관을 따라잡아 **온비드를 다시 쓸 수 있게** 합니다.

---

## 무엇이 어떻게 바뀌었나

### ① 구 호스트는 죽었습니다

용도코드·주소 조회가 쓰던 `openapi.onbid.co.kr`은 응답하지 않습니다.

```
$ curl -m 20 http://openapi.onbid.co.kr/
curl: (28) Connection timed out after 20001 milliseconds
```

클라우드 IP 차단이 아닙니다 — **한국 가정용 회선에서도 동일**합니다. DNS는 정상 해석되고
온비드 웹사이트(`www.onbid.co.kr`)는 멀쩡합니다. OpenAPI 서버만 죽어 있습니다.

### ② 구 서비스는 폐기, 차세대로 이관

```json
{"errMsg": "NO_OPENAPI_SERVICE_ERROR",
 "returnAuthMsg": "해당 오픈API 서비스가 없거나 폐기됨",
 "returnReasonCode": "12"}
```

`OnbidCltrBidRsltListSrvc` → **`OnbidCltrBidRsltListSrvc2`**. 서비스명 끝에 `2`가 붙은
차세대 버전이 별도로 존재합니다. 베이스는 `https://apis.data.go.kr/B010003`.

### ③ 응답 스키마도 바뀌었습니다

```jsonc
// 구 스키마
{"response": {"header": {...}, "body": {"items": {"item": [...]}}}}

// 차세대 — header/body가 최상위
{"header": {"resultCode": "00"}, "body": {"items": {"item": [...]}, "totalCount": 258}}

// 오류일 때는 또 다른 래퍼
{"result": {"resultCode": "11", "resultMsg": "NO_MANDATORY_REQUEST_PARAMETERS_ERROR"}}
```

---

## 제공 도구 (9종)

| 도구 | 내용 |
|---|---|
| `get_public_auction_items` | 부동산 공매 물건 — 감정가·최저입찰가·개찰일시·유찰여부 |
| `get_onbid_car_items` | 차량 목록 (입찰중·예정) — 제조사·모델·연식·주행거리·연료 |
| `get_onbid_movable_items` | 동산 목록 (입찰중·예정) — 기계·의료장비·집기 등 |
| `get_onbid_car_detail` | 차량 상세 — 감정평가정보·물건사진 |
| `get_onbid_movable_detail` | 동산 상세 — 감정평가법인·보관장소·입찰조건 |
| `get_onbid_announcements` | 공매 공고목록 |
| `get_onbid_bid_conditions` | 공고 입찰조건 — 보증금률·대금납부방식·공동/대리입찰 가능여부 |
| `get_onbid_usage_codes` | 용도 분류코드 (대/중/소분류 계층) |
| `get_onbid_addresses` | 물건 소재지 (시도·시군구·읍면동·상세) |

원본은 11종이었으나 **9종으로 통합**했습니다. 차세대 API가 계층 전체를 한 번에 반환하므로
대/중/소분류 3종과 주소 4종을 각각 하나로 합쳤습니다. `tools/onbid.py`는 677줄 → 296줄이
됐습니다.

---

## 설치

[tae0y/real-estate-mcp](https://github.com/tae0y/real-estate-mcp) 위에 얹는 **오버레이**입니다.
원본을 먼저 설치한 뒤, 파일 3개를 복사하면 온비드 도구가 활성화됩니다.

```bash
git clone https://github.com/tae0y/real-estate-mcp
git clone https://github.com/dongkyucho17/onbid-mcp

cd real-estate-mcp
cp -r ../onbid-mcp/src/real_estate/mcp_server/tools/onbid.py    src/real_estate/mcp_server/tools/
cp -r ../onbid-mcp/src/real_estate/mcp_server/parsers/onbid.py  src/real_estate/mcp_server/parsers/
# _helpers.py는 온비드 URL 상수만 추가하면 됩니다 (아래 참고)
```

`server.py`에 한 줄 추가:

```python
import real_estate.mcp_server.tools.onbid  # noqa: F401 — registers @mcp.tool()
```

`_helpers.py`에는 이 저장소의 [`_onbid_urls.py`](src/real_estate/mcp_server/_onbid_urls.py)
내용을 붙이거나, 동봉된 `_helpers.py`를 참고해 URL 상수 블록만 옮기면 됩니다.

### 환경변수

```bash
export DATA_GO_KR_API_KEY="공공데이터포털에서_발급받은_키"
```

### 필요한 활용신청

공공데이터포털에서 **서비스별로 개별 승인**이 필요합니다.

- 차세대 온비드 공고목록 / 공고상세 입찰정보
- 차세대 온비드 차량 물건목록 / 물건상세
- 차세대 온비드 동산 물건목록 / 물건상세
- 온비드 코드 조회

일일 트래픽은 서비스당 1,000회입니다.

---

## API 함정 6가지

여기가 이 저장소의 핵심입니다. 공식 문서에 있지만 놓치기 쉬운 것들이고,
이것 때문에 원작자도 *"repeated patches"* 라고 표현했을 것입니다.

### 1. 인증키는 URL 문자열에 직접 넣어야 한다

```python
# ❌ 실패 — NO_MANDATORY_REQUEST_PARAMETERS_ERROR
requests.get(url, params={"serviceKey": key, ...})

# ✅ 성공
encoded = urllib.parse.quote(key, safe="")
url = f"{base}?serviceKey={encoded}&{urlencode(params)}"
```

라이브러리가 인코딩하게 두면 **키 오류가 아니라 "필수 파라미터 누락"** 이 돌아옵니다.
오류 메시지가 원인을 전혀 가리키지 않아 진단이 어렵습니다.

### 2. 목록 API의 숨은 필수 항목 — `pvctTrgtYn`

```
prptDivCd (재산유형) + pvctTrgtYn (수의계약가능여부 Y/N)
```

`pvctTrgtYn`이 필수인 줄 모르면 무엇을 넣어도 실패합니다. 코드·날짜 조합을 100가지 넘게
시도했지만 전부 막혔고, 활용가이드를 확인하고서야 풀렸습니다.

### 3. 관리번호가 네 종류이고 서로 대체 불가

| 필드 | 용도 | 예시 |
|---|---|---|
| `cltrMngNo` | **물건**관리번호 — 물건 상세 조회 | `2026-0800-042351` |
| `pbancMngNo` | **공고**관리번호 — 공고 입찰조건 조회 | `202606-20415-00` |
| `onbidPbancNo` | 온비드 공고번호 (숫자) | `894108` |
| `pbctNo` | 공매번호 (숫자) | `10051064` |

엉뚱한 번호를 넣으면 역시 `NO_MANDATORY_REQUEST_PARAMETERS_ERROR`입니다.

### 4. 상세 조회는 진행 중인 건만 나온다

*"현재 입찰 중이거나 입찰 예정인 목록만 조회됩니다"* — 종료된 공매의 물건번호로 상세를
조회하면 `NODATA_ERROR`가 **정상 응답**입니다. 오류가 아닙니다.

### 5. `resultType=json` 필수

`xml`로 요청하면 동일한 파라미터로도 실패합니다.

### 6. 오퍼레이션명에 `2`가 붙는다 (문서와 다름)

문서에는 `getCarDtlInf`로 적혀 있지만 실제 동작하는 것은 **`getCarDtlInf2`** 입니다(v2.0).
서비스 ID(`OnbidCarDtlSrvc`)와 실제 엔드포인트(`OnbidCarDtlSrvc2`)도 다릅니다.

---

## 오류코드 읽는 법

진단할 때 가장 헷갈렸던 부분입니다.

| 응답 | 의미 |
|---|---|
| `NO_OPENAPI_SERVICE_ERROR` (12) | 경로 미해석 — **서비스명 또는 오퍼레이션명이 틀림** |
| `NO_MANDATORY_REQUEST_PARAMETERS_ERROR` (11) | 경로는 정확, **필수 파라미터만 부족** |
| `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` | 미승인 또는 키 오류 |
| `NODATA_ERROR` (03) | 정상 — 조건에 맞는 데이터 없음 |

**코드 12는 "폐기됨"을 뜻하지 않습니다.** 살아 있는 서비스라도 오퍼레이션명을 틀리면 같은
메시지가 나옵니다. 대조 실험으로 확인했습니다:

```
OnbidPbancListSrvc2/getPbancList2     → 코드 11  (정상 경로, 파라미터만 부족)
OnbidPbancListSrvc2/getWrongName2     → 코드 12
OnbidPbancListSrvc2                   → 코드 12  (오퍼레이션 없음)
```

이걸 몰라서 살아 있는 서비스를 "폐기됐다"고 잘못 판단할 뻔했습니다.

---

## 엔드포인트 대응표

베이스: `https://apis.data.go.kr/B010003`

| 도구 | 엔드포인트 | 필수 파라미터 |
|---|---|---|
| `get_public_auction_items` | `OnbidCltrBidRsltListSrvc2/getCltrBidRsltList2` | `prptDivCd`, `pvctTrgtYn` |
| `get_onbid_car_items` | `OnbidCarListSrvc2/getCarCltrList2` | `prptDivCd`, `pvctTrgtYn` |
| `get_onbid_movable_items` | `OnbidMvastListSrvc2/getMvastCltrList2` | `prptDivCd`, `pvctTrgtYn` |
| `get_onbid_car_detail` | `OnbidCarDtlSrvc2/getCarDtlInf2` | `cltrMngNo` |
| `get_onbid_movable_detail` | `OnbidMvastDtlSrvc2/getMvastDtlInf2` | `cltrMngNo` |
| `get_onbid_announcements` | `OnbidPbancListSrvc2/getPbancList2` | `cltrTypeCd`, `prptDivCd`, `bidDivCd`, `dspsMthodCd` + 날짜범위 |
| `get_onbid_bid_conditions` | `OnbidPbancBidDtlSrvc2/getPbancBidInf2` | `pbancMngNo` |
| `get_onbid_usage_codes` | `OnbidCodeSrvc/getOnbidUsgCodeInfo` | 없음 |
| `get_onbid_addresses` | `OnbidCodeSrvc/getOnbidDtlAddrInfo` | 없음 |

오퍼레이션 명명 규칙은 일관되지 않습니다. 문서 확인이 확실합니다.

| 서비스 | 오퍼레이션 | 패턴 |
|---|---|---|
| `OnbidPbancListSrvc2` | `getPbancList2` | 그대로 |
| `OnbidCarListSrvc2` | `getCarCltrList2` | `Cltr` 삽입 |
| `OnbidMvastListSrvc2` | `getMvastCltrList2` | `Cltr` 삽입 |
| `OnbidCarDtlSrvc2` | `getCarDtlInf2` | `Inf` 삽입 |
| `OnbidPbancBidDtlSrvc2` | `getPbancBidInf2` | `Dtl` 빠짐 |
| `OnbidCodeSrvc` | `getOnbidUsgCodeInfo` | `2` 없음 |

---

## 검증

[`docs/verification.md`](docs/verification.md)에 9종 전체의 실호출 결과와 응답 샘플,
진단 과정이 있습니다. 목록 → 상세 연결(`cltrMngNo`·`pbancMngNo` 전달)까지 확인했습니다.

---

## 원본 프로젝트에 대하여

이 저장소는 [tae0y/real-estate-mcp](https://github.com/tae0y/real-estate-mcp)의
온비드 관련 코드에서 파생됐습니다. MIT 라이선스이며, 저작권 표시는 [LICENSE](LICENSE)에
그대로 유지했습니다.

**원작자의 제거 결정을 존중합니다.** 개인 프로젝트로 이 API를 계속 따라가는 건 실제로
부담이 큽니다. 이 저장소는 그 부담을 원본에 지우지 않으면서, 온비드가 필요한 사람이
선택적으로 얹어 쓸 수 있게 하려는 것입니다.

실거래가·전월세·청약 기능은 원본을 그대로 쓰시면 됩니다. 여기엔 온비드만 있습니다.

## 라이선스

MIT
