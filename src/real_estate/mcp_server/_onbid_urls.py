"""차세대 온비드 API 엔드포인트 상수.

`_helpers.py`에 이 내용을 붙여넣거나, 거기서 import 해서 쓰면 된다.

배경: 캠코가 온비드 OpenAPI를 '차세대'로 이관하면서
  - 구 호스트 `openapi.onbid.co.kr` 는 응답하지 않는다(한국 IP에서도 타임아웃)
  - 구 서비스 `apis.data.go.kr/B010003/…Srvc` 는 폐기 → 끝에 `2`가 붙은 서비스로 이관
전부 2026-08-13 실호출로 확인했다.

⚠️ 인증키는 URL-Encode 후 **URL 문자열에 직접 삽입**해야 한다.
   requests의 params= 로 넘기면 NO_MANDATORY_REQUEST_PARAMETERS_ERROR가 난다.
"""

_ONBID_BASE = "https://apis.data.go.kr/B010003"

# ── 물건·공고 ────────────────────────────────────────────────
# 필수: prptDivCd(재산유형) + pvctTrgtYn(수의계약가능여부 Y/N)
_ONBID_BID_RESULT_LIST_URL = f"{_ONBID_BASE}/OnbidCltrBidRsltListSrvc2/getCltrBidRsltList2"
_ONBID_CAR_LIST_URL = f"{_ONBID_BASE}/OnbidCarListSrvc2/getCarCltrList2"
_ONBID_MVAST_LIST_URL = f"{_ONBID_BASE}/OnbidMvastListSrvc2/getMvastCltrList2"

# 필수: cltrMngNo(물건관리번호). 현재 입찰중·입찰예정 건만 조회된다.
_ONBID_CAR_DTL_URL = f"{_ONBID_BASE}/OnbidCarDtlSrvc2/getCarDtlInf2"
_ONBID_MVAST_DTL_URL = f"{_ONBID_BASE}/OnbidMvastDtlSrvc2/getMvastDtlInf2"

# 공고목록 필수: cltrTypeCd + prptDivCd + bidDivCd + dspsMthodCd + 날짜범위
_ONBID_PBANC_LIST_URL = f"{_ONBID_BASE}/OnbidPbancListSrvc2/getPbancList2"
# 공고 입찰상세 필수: pbancMngNo(공고관리번호) — 물건관리번호와 다르다
_ONBID_PBANC_BID_DTL_URL = f"{_ONBID_BASE}/OnbidPbancBidDtlSrvc2/getPbancBidInf2"

# ── 코드·주소 (필수 파라미터 없음) ──────────────────────────
# 차세대는 계층 전체를 한 번에 반환한다. 구 버전의 대/중/소분류 3종,
# addr1~3 + 상세주소 4종이 각각 아래 하나로 대체된다.
_ONBID_USG_CODE_URL = f"{_ONBID_BASE}/OnbidCodeSrvc/getOnbidUsgCodeInfo"
_ONBID_DTL_ADDR_URL = f"{_ONBID_BASE}/OnbidCodeSrvc/getOnbidDtlAddrInfo"

# ── 구 상수명 별칭 (기존 코드 호환) ─────────────────────────
_ONBID_CODE_TOP_URL = _ONBID_USG_CODE_URL
_ONBID_CODE_MIDDLE_URL = _ONBID_USG_CODE_URL
_ONBID_CODE_BOTTOM_URL = _ONBID_USG_CODE_URL
_ONBID_ADDR1_URL = _ONBID_DTL_ADDR_URL
_ONBID_ADDR2_URL = _ONBID_DTL_ADDR_URL
_ONBID_ADDR3_URL = _ONBID_DTL_ADDR_URL
_ONBID_BID_RESULT_DETAIL_URL = _ONBID_PBANC_BID_DTL_URL
_ONBID_THING_INFO_LIST_URL = _ONBID_MVAST_LIST_URL
_ONBID_CODE_INFO_BASE_URL = f"{_ONBID_BASE}/OnbidCodeSrvc"
