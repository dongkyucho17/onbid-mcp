"""MCP tools for Onbid (공매) — 차세대 온비드 API (2026~).

2026-08-13 전면 개편. 구 버전은 두 가지 이유로 전부 실패하고 있었다:
  1. `openapi.onbid.co.kr` 호스트 무응답 (한국 IP에서도 불통) — 코드·주소 7종
  2. `apis.data.go.kr/.../…Srvc` 폐기 → `…Srvc2`로 이관 — 물건 2종

엔드포인트·필수 파라미터는 전부 실호출로 검증했다(공공데이터포털 활용가이드 대조).
  목록계: prptDivCd + pvctTrgtYn 이 필수 (이게 빠지면 NO_MANDATORY)
  상세계: cltrMngNo(물건) 또는 pbancMngNo(공고)가 필수
  인증키: URL-Encode 후 URL에 직접 삽입 (라이브러리 자동 인코딩은 실패)
"""

from __future__ import annotations

from typing import Any

from real_estate.mcp_server import mcp
from real_estate.mcp_server._helpers import (
    _ONBID_BID_RESULT_LIST_URL,
    _ONBID_CAR_DTL_URL,
    _ONBID_CAR_LIST_URL,
    _ONBID_DTL_ADDR_URL,
    _ONBID_MVAST_DTL_URL,
    _ONBID_MVAST_LIST_URL,
    _ONBID_PBANC_BID_DTL_URL,
    _ONBID_PBANC_LIST_URL,
    _ONBID_USG_CODE_URL,
    _build_url_with_service_key,
    _check_onbid_api_key,
    _fetch_json,
    _get_data_go_kr_key_for_onbid,
)
from real_estate.mcp_server.error_types import (
    make_api_error,
    make_invalid_input_error,
    make_parse_error,
)
from real_estate.mcp_server.parsers.onbid import _onbid_extract_items

_OK = {"00", "000"}


async def _call(url_base: str, params: dict[str, Any], page_no: int, num_of_rows: int):
    """공통 호출·파싱. 성공 시 {total_count, items, page_no, num_of_rows}."""
    if page_no < 1:
        return make_invalid_input_error(field="page_no", reason="must be >= 1", example="1")
    if num_of_rows < 1:
        return make_invalid_input_error(field="num_of_rows", reason="must be >= 1", example="20")

    err = _check_onbid_api_key()
    if err:
        return err

    base_params: dict[str, Any] = {
        "pageNo": page_no,
        "numOfRows": num_of_rows,
        "resultType": "json",
    }
    base_params.update({k: v for k, v in params.items() if v not in (None, "")})

    url = _build_url_with_service_key(
        url_base, _get_data_go_kr_key_for_onbid(), base_params
    )
    payload, fetch_err = await _fetch_json(url)
    if fetch_err:
        return fetch_err
    if not isinstance(payload, dict):
        return make_parse_error("JSON", "Unexpected response type")

    result_code, body, items = _onbid_extract_items(payload)
    if result_code and result_code not in _OK:
        msg = str(body.get("resultMsg") or payload.get("resultMsg") or "").strip()
        if result_code == "03" or "NODATA" in msg:
            return {"total_count": 0, "items": [], "page_no": page_no,
                    "num_of_rows": num_of_rows,
                    "note": "조건에 맞는 물건이 없습니다 (상세 조회는 현재 입찰중·예정 건만 대상)"}
        if "NO_MANDATORY" in msg:
            return make_api_error(
                code=result_code,
                message=("필수 파라미터 누락. 목록은 prpt_div_cd와 pvct_trgt_yn이, "
                         "상세는 물건/공고 관리번호가 반드시 필요합니다."),
            )
        return make_api_error(code=result_code, message=msg or "Onbid API error")

    try:
        total_count = int(body.get("totalCount") or 0)
    except (TypeError, ValueError):
        total_count = 0
    return {
        "total_count": total_count,
        "items": items,
        "page_no": int(body.get("pageNo") or page_no),
        "num_of_rows": int(body.get("numOfRows") or num_of_rows),
    }


# ─── 물건 목록 ──────────────────────────────────────────────────────────────

@mcp.tool()
async def get_public_auction_items(
    prpt_div_cd: str = "0007,0005",
    pvct_trgt_yn: str = "N",
    cltr_type_cd: str | None = "0001",
    bid_div_cd: str | None = "0001",
    dsps_mthod_cd: str | None = "0001",
    opbd_dt_start: str | None = None,
    opbd_dt_end: str | None = None,
    lctn_sdnm: str | None = None,
    lctn_sggnm: str | None = None,
    page_no: int = 1,
    num_of_rows: int = 20,
) -> dict[str, Any]:
    """온비드 공매 물건(부동산 중심) 낙찰결과 목록.

    감정가·최저입찰가·개찰일시·유찰여부·소재지를 제공한다. 종료된 회차 기준이라
    시세 파악과 낙찰가율 분석에 쓴다. 진행 중 물건은 차량/동산 목록 도구를 쓸 것.

    Args:
        prpt_div_cd: 재산유형(필수). 0007 압류재산, 0005 기타일반, 0010 국유재산,
            0002 공유재산, 0006 유입재산, 0008 수탁재산, 0013 파산자산. 복수는 쉼표.
        pvct_trgt_yn: 수의계약 가능여부(필수) Y/N.
        cltr_type_cd: 물건유형 0001 부동산 / 0002 자동차 / 0003 동산.
        bid_div_cd: 0001 인터넷, 0002 현장.
        dsps_mthod_cd: 0001 매각, 0002 임대.
        opbd_dt_start/end: 개찰일 범위 (YYYYMMDD).
        lctn_sdnm/lctn_sggnm: 소재지 시도/시군구.
    """
    return await _call(_ONBID_BID_RESULT_LIST_URL, {
        "prptDivCd": prpt_div_cd, "pvctTrgtYn": pvct_trgt_yn,
        "cltrTypeCd": cltr_type_cd, "bidDivCd": bid_div_cd,
        "dspsMthodCd": dsps_mthod_cd,
        "opbdDtStart": opbd_dt_start, "opbdDtEnd": opbd_dt_end,
        "lctnSdnm": lctn_sdnm, "lctnSggnm": lctn_sggnm,
    }, page_no, num_of_rows)


@mcp.tool()
async def get_onbid_car_items(
    prpt_div_cd: str = "0007,0005",
    pvct_trgt_yn: str = "N",
    bid_div_cd: str | None = None,
    dsps_mthod_cd: str | None = None,
    page_no: int = 1,
    num_of_rows: int = 20,
) -> dict[str, Any]:
    """온비드 공매 **차량** 물건목록 (현재 입찰중·입찰예정).

    제조사·모델·연식·주행거리·배기량·연료·변속기와 감정가/최저입찰가, 입찰기간을
    제공한다. 응답의 cltr_mng_no로 get_onbid_car_detail을 호출하면 상세를 볼 수 있다.

    Args:
        prpt_div_cd: 재산유형(필수, 복수는 쉼표). 0007 압류재산, 0005 기타일반 등.
        pvct_trgt_yn: 수의계약 가능여부(필수) Y/N.
    """
    return await _call(_ONBID_CAR_LIST_URL, {
        "prptDivCd": prpt_div_cd, "pvctTrgtYn": pvct_trgt_yn,
        "bidDivCd": bid_div_cd, "dspsMthodCd": dsps_mthod_cd,
    }, page_no, num_of_rows)


@mcp.tool()
async def get_onbid_movable_items(
    prpt_div_cd: str = "0007,0005",
    pvct_trgt_yn: str = "N",
    bid_div_cd: str | None = None,
    dsps_mthod_cd: str | None = None,
    page_no: int = 1,
    num_of_rows: int = 20,
) -> dict[str, Any]:
    """온비드 공매 **동산**(차량 제외) 물건목록 (현재 입찰중·입찰예정).

    기계·의료장비·가전·집기 등. 용도 대/중/소분류, 감정가·최저입찰가, 보관장소,
    제조연도, 입찰기간을 제공한다. cltr_mng_no로 get_onbid_movable_detail 호출.

    Args:
        prpt_div_cd: 재산유형(필수, 복수는 쉼표).
        pvct_trgt_yn: 수의계약 가능여부(필수) Y/N.
    """
    return await _call(_ONBID_MVAST_LIST_URL, {
        "prptDivCd": prpt_div_cd, "pvctTrgtYn": pvct_trgt_yn,
        "bidDivCd": bid_div_cd, "dspsMthodCd": dsps_mthod_cd,
    }, page_no, num_of_rows)


# ─── 상세 ───────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_onbid_car_detail(
    cltr_mng_no: str,
    pbct_cdtn_no: int | None = None,
) -> dict[str, Any]:
    """차량 공매 물건 상세 — 감정평가정보·물건사진·입찰조건.

    현재 입찰중이거나 입찰예정인 차량만 조회된다(종료 건은 결과 없음).

    Args:
        cltr_mng_no: 물건관리번호(필수). 예 "2026-0800-042351" — 목록 응답의 cltrMngNo.
        pbct_cdtn_no: 공매조건번호(선택). 목록 응답의 pbctCdtnNo.
    """
    return await _call(_ONBID_CAR_DTL_URL, {
        "cltrMngNo": cltr_mng_no, "pbctCdtnNo": pbct_cdtn_no,
    }, 1, 1)


@mcp.tool()
async def get_onbid_movable_detail(
    cltr_mng_no: str,
    pbct_cdtn_no: int | None = None,
) -> dict[str, Any]:
    """동산 공매 물건 상세 — 감정평가법인·물건사진·보관장소·입찰조건(93개 필드).

    현재 입찰중이거나 입찰예정인 동산만 조회된다.

    Args:
        cltr_mng_no: 물건관리번호(필수). 예 "2026-0400-007680".
        pbct_cdtn_no: 공매조건번호(선택).
    """
    return await _call(_ONBID_MVAST_DTL_URL, {
        "cltrMngNo": cltr_mng_no, "pbctCdtnNo": pbct_cdtn_no,
    }, 1, 1)


# ─── 공고 ───────────────────────────────────────────────────────────────────

@mcp.tool()
async def get_onbid_announcements(
    cltr_type_cd: str = "0001",
    prpt_div_cd: str = "0007",
    bid_div_cd: str = "0001",
    dsps_mthod_cd: str = "0001",
    pbanc_ymd_start: str | None = None,
    pbanc_ymd_end: str | None = None,
    onbid_pbanc_nm: str | None = None,
    org_nm: str | None = None,
    page_no: int = 1,
    num_of_rows: int = 20,
) -> dict[str, Any]:
    """온비드 공매 **공고목록** — 공고관리번호·공고명·공고기관·공고일자.

    응답의 pbanc_mng_no로 get_onbid_bid_conditions를 호출하면 입찰 조건을 볼 수 있다.

    Args:
        cltr_type_cd: 0001 부동산 / 0002 자동차 / 0003 동산.
        prpt_div_cd: 재산유형(복수는 쉼표).
        pbanc_ymd_start/end: 공고일 범위 (YYYYMMDD).
        onbid_pbanc_nm: 공고명 검색어.
        org_nm: 공고기관명.
    """
    return await _call(_ONBID_PBANC_LIST_URL, {
        "cltrTypeCd": cltr_type_cd, "prptDivCd": prpt_div_cd,
        "bidDivCd": bid_div_cd, "dspsMthodCd": dsps_mthod_cd,
        "pbancYmdStart": pbanc_ymd_start, "pbancYmdEnd": pbanc_ymd_end,
        "onbidPbancNm": onbid_pbanc_nm, "orgNm": org_nm,
    }, page_no, num_of_rows)


@mcp.tool()
async def get_onbid_bid_conditions(pbanc_mng_no: str) -> dict[str, Any]:
    """공고 **입찰 상세조건** — 보증금률·대금납부방식·공동/대리입찰 가능여부 등.

    실제 입찰 참여 판단에 필요한 실무 정보다. 목록 API에는 없다.

    Args:
        pbanc_mng_no: 공고관리번호(필수). 예 "202606-20415-00"
            — get_onbid_announcements 응답의 pbancMngNo.
            물건관리번호(cltrMngNo)와 다르니 혼동하지 말 것.
    """
    return await _call(_ONBID_PBANC_BID_DTL_URL, {"pbancMngNo": pbanc_mng_no}, 1, 1)


# ─── 코드·주소 (구 7개 도구를 2개로 통합) ──────────────────────────────────

@mcp.tool()
async def get_onbid_usage_codes(
    page_no: int = 1,
    num_of_rows: int = 500,
) -> dict[str, Any]:
    """온비드 용도 분류코드 전체(약 420건) — 대/중/소분류가 계층으로 반환된다.

    각 항목의 up_ctgr_id가 상위 분류를 가리킨다. 예: 부동산(10000) > 토지(10100)
    > 대지(10101). 물건 응답의 cltrUsgLclsCtgrId 등이 이 체계를 쓴다.
    구 버전의 대/중/소분류 3개 도구를 하나로 합친 것이다.
    """
    return await _call(_ONBID_USG_CODE_URL, {}, page_no, num_of_rows)


@mcp.tool()
async def get_onbid_addresses(
    page_no: int = 1,
    num_of_rows: int = 100,
) -> dict[str, Any]:
    """온비드 물건 소재지 목록 — 시도·시군구·읍면동·상세주소를 한 번에 반환.

    구 버전의 addr1/addr2/addr3/상세주소 4개 도구를 하나로 합친 것이다.
    """
    return await _call(_ONBID_DTL_ADDR_URL, {}, page_no, num_of_rows)
