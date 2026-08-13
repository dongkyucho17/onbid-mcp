# onbid-mcp

🇰🇷 [한국어 README](README.md)

**Onbid (public auction) MCP server — patched for the next-generation API.**

Onbid support was dropped from the upstream project as *"unmaintainable."* This repo brings it
back on the migrated endpoints. All 9 tools verified against live calls.

```
Car listings         258      Movable-asset listings   2,650    Announcement listings   590
Usage codes           420      Item locations          17,744    Items (auction results) 53,804
Car detail          85 fields  Movable-asset detail     93 fields Bid conditions          17 fields
```

---

## Why this repo exists

[tae0y/real-estate-mcp](https://github.com/tae0y/real-estate-mcp) is a solid project that exposes
Korean real-estate data (transaction prices, jeonse/wolse, etc.) as MCP tools. It used to include
11 Onbid (public auction) tools, but they were **removed** in July 2026:

> **[BREAKING CHANGES] Remove Onbid (공매) tools (#31)**
> Onbid's API required repeated patches, making it unsustainable to maintain as a
> personal project (announced deprecation, effective 2026-06-01).

The Onbid API genuinely had changed, and the old endpoints **still don't respond today.**

But on inspection, this wasn't a shutdown — it was a **migration.** KAMCO (Korea Asset Management
Corporation) moved Onbid to a *next-generation* platform, changing the service hosts, response
schema, and required parameters all at once. The announcement was easy to miss.

This repo undoes that migration and makes Onbid usable again.

---

## What actually changed

### 1. The old host is dead

Usage-code and address lookups used to call `openapi.onbid.co.kr`. It no longer responds:

```
$ curl -m 20 http://openapi.onbid.co.kr/
curl: (28) Connection timed out after 20001 milliseconds
```

This isn't a cloud-IP block — **the same timeout happens from a residential connection inside
Korea.** DNS resolves fine, and the Onbid website (`www.onbid.co.kr`) is up. Only the OpenAPI
server is dead.

### 2. The old service is deprecated in favor of a v2

```json
{"errMsg": "NO_OPENAPI_SERVICE_ERROR",
 "returnAuthMsg": "해당 오픈API 서비스가 없거나 폐기됨",
 "returnReasonCode": "12"}
```

`OnbidCltrBidRsltListSrvc` → **`OnbidCltrBidRsltListSrvc2`**. A next-generation version exists
under a separate service name with a trailing `2`, at base `https://apis.data.go.kr/B010003`.

### 3. The response schema changed too

```jsonc
// Old schema
{"response": {"header": {...}, "body": {"items": {"item": [...]}}}}

// Next-gen — header/body promoted to the top level
{"header": {"resultCode": "00"}, "body": {"items": {"item": [...]}, "totalCount": 258}}

// Errors use yet another wrapper
{"result": {"resultCode": "11", "resultMsg": "NO_MANDATORY_REQUEST_PARAMETERS_ERROR"}}
```

---

## Tools (9)

| Tool | What it returns |
|---|---|
| `get_public_auction_items` | Public-auction real-estate listings — appraised value, minimum bid, opening date/time, whether it was passed over |
| `get_onbid_car_items` | Vehicle listings (open or upcoming bids) — make, model, year, mileage, fuel type |
| `get_onbid_movable_items` | Movable-asset listings (open or upcoming bids) — machinery, medical equipment, fixtures, etc. |
| `get_onbid_car_detail` | Vehicle detail — appraisal info, photos |
| `get_onbid_movable_detail` | Movable-asset detail — appraiser, storage location, bid conditions |
| `get_onbid_announcements` | Auction announcement listings |
| `get_onbid_bid_conditions` | Announcement bid conditions — deposit rate, payment method, joint/proxy bidding eligibility |
| `get_onbid_usage_codes` | Usage classification codes (large/medium/small category hierarchy) |
| `get_onbid_addresses` | Item locations (province/city/district/dong, detail) |

The original had 11 tools; this repo **consolidates them into 9.** The next-gen API returns the
whole category hierarchy in one call, so the three category-tier tools and four address tools
each collapsed into one. `tools/onbid.py` went from 677 lines to 296.

---

## Install

This is an **overlay** on top of [tae0y/real-estate-mcp](https://github.com/tae0y/real-estate-mcp).
Install the upstream project first, then copy in 3 files to activate the Onbid tools.

```bash
git clone https://github.com/tae0y/real-estate-mcp
git clone https://github.com/dongkyucho17/onbid-mcp

cd real-estate-mcp
cp -r ../onbid-mcp/src/real_estate/mcp_server/tools/onbid.py    src/real_estate/mcp_server/tools/
cp -r ../onbid-mcp/src/real_estate/mcp_server/parsers/onbid.py  src/real_estate/mcp_server/parsers/
# _helpers.py just needs the Onbid URL constants added (see below)
```

Add one line to `server.py`:

```python
import real_estate.mcp_server.tools.onbid  # noqa: F401 — registers @mcp.tool()
```

For `_helpers.py`, paste in the contents of this repo's
[`_onbid_urls.py`](src/real_estate/mcp_server/_onbid_urls.py), or use the bundled `_helpers.py`
as a reference and move over just the URL-constants block.

### Environment variable

```bash
export DATA_GO_KR_API_KEY="your-key-from-data.go.kr"
```

### Required approvals

data.go.kr requires **separate approval per service.** You'll need:

- Next-gen Onbid announcement listing / announcement detail (bid info)
- Next-gen Onbid vehicle listing / vehicle detail
- Next-gen Onbid movable-asset listing / movable-asset detail
- Onbid code lookup

Daily quota is 1,000 calls per service.

---

## Six API traps

This is the real value of this repo. All of these are technically documented, but easy to miss —
and are almost certainly what the upstream maintainer meant by *"repeated patches."*

### 1. The service key must be spliced into the URL string directly

```python
# Fails — NO_MANDATORY_REQUEST_PARAMETERS_ERROR
requests.get(url, params={"serviceKey": key, ...})

# Works
encoded = urllib.parse.quote(key, safe="")
url = f"{base}?serviceKey={encoded}&{urlencode(params)}"
```

Let a library auto-encode it and you get **"missing required parameter," not "bad key."** The
error message points nowhere near the actual cause, which makes this brutal to diagnose blind.

### 2. A hidden required field on every list endpoint — `pvctTrgtYn`

```
prptDivCd (property type) + pvctTrgtYn (private-contract eligible Y/N)
```

Not knowing `pvctTrgtYn` is required means *nothing* works, no matter what else you pass. Over a
hundred code/date combinations were tried and rejected before checking the usage guide surfaced
this.

### 3. Four different ID fields, none interchangeable

| Field | Used for | Example |
|---|---|---|
| `cltrMngNo` | **Item** management number — item detail lookup | `2026-0800-042351` |
| `pbancMngNo` | **Announcement** management number — bid-condition lookup | `202606-20415-00` |
| `onbidPbancNo` | Onbid announcement number (numeric) | `894108` |
| `pbctNo` | Auction number (numeric) | `10051064` |

Pass the wrong one and you get the same `NO_MANDATORY_REQUEST_PARAMETERS_ERROR` again.

### 4. Detail lookups only work for items still open

*"Only currently-bidding or upcoming items can be looked up"* — querying detail for an item
number from a **closed** auction returns `NODATA_ERROR` as the **correct, expected** response,
not an error condition to work around.

### 5. `resultType=json` is mandatory

Requesting `xml` fails with the exact same parameters otherwise valid for `json`.

### 6. Operation names carry a trailing `2` the docs don't mention

The documentation says `getCarDtlInf`; the operation that actually works is
**`getCarDtlInf2`** (v2.0). The service ID (`OnbidCarDtlSrvc`) and the real endpoint
(`OnbidCarDtlSrvc2`) differ too.

---

## Reading the error codes

This was the most confusing part of the whole diagnosis.

| Response | Meaning |
|---|---|
| `NO_OPENAPI_SERVICE_ERROR` (12) | Route unresolved — **wrong service name or operation name** |
| `NO_MANDATORY_REQUEST_PARAMETERS_ERROR` (11) | Route is correct, **just missing required params** |
| `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` | Not approved yet, or key is wrong |
| `NODATA_ERROR` (03) | Normal — no data matches the given conditions |

**Code 12 does not mean "deprecated."** A perfectly live service returns the exact same message
if you get the operation name wrong. Confirmed with a controlled comparison:

```
OnbidPbancListSrvc2/getPbancList2     → code 11  (correct route, just missing params)
OnbidPbancListSrvc2/getWrongName2     → code 12
OnbidPbancListSrvc2                   → code 12  (no operation given)
```

Missing this distinction would have led to wrongly declaring a live service "dead."

---

## Endpoint reference

Base: `https://apis.data.go.kr/B010003`

| Tool | Endpoint | Required params |
|---|---|---|
| `get_public_auction_items` | `OnbidCltrBidRsltListSrvc2/getCltrBidRsltList2` | `prptDivCd`, `pvctTrgtYn` |
| `get_onbid_car_items` | `OnbidCarListSrvc2/getCarCltrList2` | `prptDivCd`, `pvctTrgtYn` |
| `get_onbid_movable_items` | `OnbidMvastListSrvc2/getMvastCltrList2` | `prptDivCd`, `pvctTrgtYn` |
| `get_onbid_car_detail` | `OnbidCarDtlSrvc2/getCarDtlInf2` | `cltrMngNo` |
| `get_onbid_movable_detail` | `OnbidMvastDtlSrvc2/getMvastDtlInf2` | `cltrMngNo` |
| `get_onbid_announcements` | `OnbidPbancListSrvc2/getPbancList2` | `cltrTypeCd`, `prptDivCd`, `bidDivCd`, `dspsMthodCd` + date range |
| `get_onbid_bid_conditions` | `OnbidPbancBidDtlSrvc2/getPbancBidInf2` | `pbancMngNo` |
| `get_onbid_usage_codes` | `OnbidCodeSrvc/getOnbidUsgCodeInfo` | none |
| `get_onbid_addresses` | `OnbidCodeSrvc/getOnbidDtlAddrInfo` | none |

Operation-naming isn't consistent across services. Check the docs, don't guess.

| Service | Operation | Pattern |
|---|---|---|
| `OnbidPbancListSrvc2` | `getPbancList2` | as-is |
| `OnbidCarListSrvc2` | `getCarCltrList2` | `Cltr` inserted |
| `OnbidMvastListSrvc2` | `getMvastCltrList2` | `Cltr` inserted |
| `OnbidCarDtlSrvc2` | `getCarDtlInf2` | `Inf` inserted |
| `OnbidPbancBidDtlSrvc2` | `getPbancBidInf2` | `Dtl` dropped |
| `OnbidCodeSrvc` | `getOnbidUsgCodeInfo` | no trailing `2` |

---

## Verification

[`docs/verification.md`](docs/verification.md) has live-call results and sample responses for
all 9 tools, plus the diagnostic trail. Includes the list-to-detail handoff (passing `cltrMngNo`
and `pbancMngNo` through correctly).

---

## About the upstream project

This repo is derived from the Onbid-related code in
[tae0y/real-estate-mcp](https://github.com/tae0y/real-estate-mcp). MIT licensed; the original
copyright notice is preserved as-is in [LICENSE](LICENSE).

**The upstream maintainer's removal decision is respected here.** Chasing this particular API as
a solo maintainer is genuinely burdensome. This repo exists so that burden doesn't fall back on
the upstream project, while still letting anyone who needs Onbid opt in.

For transaction prices, jeonse/wolse, and housing-subscription features, use the upstream project
as-is. This repo is Onbid only.

## License

MIT
