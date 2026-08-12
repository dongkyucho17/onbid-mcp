# 검증 기록

수정된 온비드 도구 9종 전체를 실제 API 호출로 검증한 결과입니다.

- 검증일: 2026-08-13
- 환경: Python 3.12, `uv run`, 공공데이터포털 개발계정 (활용기간 2026-08-03 ~ 2028-08-03)

## 결과

```
차량 목록            ✅ 총 258건 · 수신 2
동산 목록            ✅ 총 2650건 · 수신 2
용도 코드            ✅ 총 420건 · 수신 3
물건 주소            ✅ 총 17744건 · 수신 2
공고 목록            ✅ 총 590건 · 수신 2
물건(낙찰결과)        ✅ 총 53804건 · 수신 2
차량 상세            ✅ (필드 85개) — 기아 중형 특수 D4DA 2012 3907cc
동산 상세            ✅ (필드 93개) — 수술대 1대
입찰 조건            ✅ (필드 17개)
```

목록 → 상세 연결도 함께 확인했습니다. 목록 응답의 `cltrMngNo`·`pbctCdtnNo`를 상세 API에
그대로 전달해 데이터를 받았고, 공고목록의 `pbancMngNo`로 입찰조건까지 이어집니다.

## 엔드포인트 대응표

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

베이스: `https://apis.data.go.kr/B010003`

## 응답 샘플

### 차량 목록 (`getCarCltrList2`)

```
onbidCltrNm            기아 중형 특수 D4DA 2012 3907cc
cltrMngNo              2026-0800-042351
pbctCdtnNo             6125406
용도                    자동차 > 자동차 > 특수자동차 (12000/12100/12107)
cltrMkrNm              기아
carMdlNm               D4DA 2012
yrmdl                  2012
vhrnoCont              98오7657
drvDstc                4238
dsvlm                  3907
fuelCont               디젤
pnsNm                  오토
apslEvlAmt             1500000
lowstBidPrcIndctCont   1500000
cltrBidBgngDt          202608051000
cltrBidEndDt           202608121000
소재지                  전남광주통합특별시 무안군 삼향읍
orgNm                  전라남도경찰청
prptDivNm              기타일반재산
pbctStatNm             입찰마감
```

### 동산 상세 (`getMvastDtlInf2`)

```
onbidCltrNm            수술대 1대
용도                    측정/실험/의료 > 측정/실험및의료장비 > 의료장비및용품
apslEvlAmt             7008500
lowstBidPrcIndctCont   3504250        (감정가 대비 50%)
cltrBidBgngDt          202608061400
cltrBidEndDt           202608121600
cltrCstdPlcNm          강원특별자치도 홍천군 홍천읍 … 아름다운병원
orgNm                  강원도 홍천군 보건소
mnftYr                 2022
cltrEtcCont            취득일자: 2023. 01. 26. / 실 사용기간: 9개월 이하
apslEvlClgList         [{'apslEvlOrgNm': '(주)경일감정평가법인', …}]
potoUrlList            [{'urlAdr': 'https://www.onbid.co.kr/…'}]
```

감정평가법인·물건사진·보관장소·입찰조건 전문까지 포함해 93개 필드입니다.

### 공고 입찰조건 (`getPbancBidInf2`)

```
onbidPbancNm           (충북지역본부) 2026년 제025차 압류재산 공매공고
pbancMngNo             202606-20415-00
collbBidPsblYn         Y     공동입찰 가능
subtBidPsblYn          Y     대리입찰 가능
nrnkAplyPsblYn         Y     차순위 신청 가능
twtmGthrBidPsblYn      Y     2회 동시입찰 가능
bidVldCrtrCont         1인 이상의 유효한 입찰
pbctTdpsCont           입찰가격*10%      (보증금)
pcmtPayMtdCont         일시불            (대금납부방식)
pcmtPayTermCont        30일              (납부기한)
cseqBidInfClgList      [차수별 입찰정보 배열]
```

목록 API에는 없는 **입찰 실무 정보**입니다. 실제 참여 판단에 직결됩니다.

## 진단 과정 기록

수정 전 원인 규명에 쓴 확인들입니다. 같은 증상을 겪는 분께 참고가 되길 바랍니다.

### 호스트 도달성

| 출발지 | 대상 | 결과 |
|---|---|---|
| 해외 클라우드(VPS) | `openapi.onbid.co.kr` | 타임아웃 |
| **한국 가정용 회선** | `openapi.onbid.co.kr` | **타임아웃** |
| 한국 가정용 회선 | `www.onbid.co.kr` | HTTP 200 |

한국 IP에서도 막히므로 **클라우드 IP 차단이 아닙니다.** OpenAPI 서버 자체 문제입니다.

### 오류 메시지 구분법

| 응답 | 의미 |
|---|---|
| `NO_OPENAPI_SERVICE_ERROR` (코드 12) | 경로가 해석되지 않음 — **서비스명 또는 오퍼레이션명이 틀림** |
| `NO_MANDATORY_REQUEST_PARAMETERS_ERROR` (코드 11) | 경로는 맞고 **필수 파라미터만 부족** |
| `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` | 미승인 또는 키 오류 |
| `NODATA_ERROR` (코드 03) | 정상 — 조건에 맞는 데이터가 없음 |

**코드 12는 "폐기됨"이 아닙니다.** 동작하는 서비스라도 오퍼레이션명을 틀리면 같은 메시지가
나옵니다. 대조 실험으로 확인했습니다:

```
OnbidPbancListSrvc2/getPbancList2     → 코드 11 (정상 경로)
OnbidPbancListSrvc2/getWrongName2     → 코드 12
OnbidPbancListSrvc2                   → 코드 12  (오퍼레이션 없음)
```

### 오퍼레이션 명명 규칙

일관되지 않아 추측이 어렵습니다. 문서 확인이 확실합니다.

| 서비스 | 오퍼레이션 |
|---|---|
| `OnbidPbancListSrvc2` | `getPbancList2` |
| `OnbidCltrBidRsltListSrvc2` | `getCltrBidRsltList2` |
| `OnbidCarListSrvc2` | `getCarCltrList2` (Cltr 삽입) |
| `OnbidMvastListSrvc2` | `getMvastCltrList2` (Cltr 삽입) |
| `OnbidCarDtlSrvc2` | `getCarDtlInf2` (Inf 삽입) |
| `OnbidMvastDtlSrvc2` | `getMvastDtlInf2` |
| `OnbidPbancBidDtlSrvc2` | `getPbancBidInf2` (Dtl 없음) |
| `OnbidCodeSrvc` | `getOnbidUsgCodeInfo`, `getOnbidDtlAddrInfo` (`2` 없음) |
