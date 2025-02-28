from typing import Literal, NewType, Optional, TypedDict

AsiakastietoTimestamp = NewType("AsiakastietoTimestamp", str)
SHA512Hash = NewType("SHA512Hash", str)
BusinessId = NewType("BusinessId", str)  # Without a dash
FinnishPersonalIdentityNumber = NewType("FinnishPersonalIdentityNumber", str)

AsiakastietoTarget = Literal[
    "PAP1", "VAP1", "TAP1"
]  # PAP1 = Production, VAP1 = Test company info, TAP1 = test soletrader info

LanguageCode = Literal["FI", "EN"]
WatchListListCode = Literal[
    "SANCTIONS_AT",
    "SANCTION_LIST",
    "ASSOCIATED_ENTITY",
    "ENFORCEMENT",
    "SOE",
    "ALL",  # (Combination of lists PEP, SANCTION_LIST, ENFORCEMENT, ASSOCIATED_ENTITY and SOE) checked at once.
    "NORDIC_PEP",
    "NORDIC_RCA",
]


# TODO: Come python3.11 convert Optional to typing.NotRequired
class CommonAsiakastietoQueryParams(TypedDict):
    target: Optional[AsiakastietoTarget]
    userid: str
    passwd: str
    enduser: str
    timestamp: AsiakastietoTimestamp  # YYYYMMDDHHMMSSXXTZNNNNNN
    checksum: SHA512Hash
    format: Literal["xml", "json"]
    lang: Optional[LanguageCode]


# Functional definition required due to `listType.listCode` key that contains unallowed characters.
CompanySanctionsParams = TypedDict(
    "CompanySanctionsParams",
    {
        "listType.listCode": list[
            Literal[
                "SANCTIONS_AT",
                "SANCTION_LIST",
                "ASSOCIATED_ENTITY",
                "ENFORCEMENT",
                "SOE",
                "ALL",  # (Combination of lists PEP, SANCTION_LIST, ENFORCEMENT, ASSOCIATED_ENTITY and SOE) checked at once.
                "NORDIC_PEP",
                "NORDIC_RCA",
            ]
        ],
        "qtype": Literal["DG"],
        "businessid": BusinessId,
    },
)


class CompanySanctionsQueryParams(
    CommonAsiakastietoQueryParams, CompanySanctionsParams
):
    version: Literal["5.01"]
    segment: str
    reqmsg: str


# Functional definition required due to `listType.listCode` key that contains unallowed characters.
WatchListParams = TypedDict(
    "WatchListParams",
    {
        "entityType": Literal["I", "O"],
        "listType.listCode": list[WatchListListCode],
    },
)


# flake8: noqa N815
class WatchlistQueryParams(CommonAsiakastietoQueryParams, WatchListParams):
    firstName: Optional[str]
    lastName: Optional[str]
    birthDate: Optional[str]  # dd.mm.yyyy or yyyy
    personId: Optional[FinnishPersonalIdentityNumber]
    # TODO: Consider are these needed, they came in response, and same type could be used for request and response?


class TimeStampField(TypedDict):
    date: str  # YYYY-MM-DD
    time: str  # HH:MM:SS


OK = Literal["0"]
ERROR = Literal["1"]
ResponseStatus = OK | ERROR


class ResponseHeader(TypedDict):
    languageCode: LanguageCode
    timeStamp: TimeStampField
    responseStatus: ResponseStatus
    currencyCode: str  # e.g. "EUR"


class WatchListHit(TypedDict):
    name: str
    role: str  # e.g. "Yritys", "Puheenjohtaja"
    hitCount: str  # e.g. "0"
    hitsRow: list["WatchListHitEntry"]


class PepAndSanctionsData(TypedDict):
    businessId: str
    companyName: str
    searchStatus: str  # "OK"
    watchListHits: list[WatchListHit]


class ErrorMessage(TypedDict):
    errorCode: str  # e.g. "103"
    errorText: str  # e.g. "AUTHENTICATION_FAILED"


class CompanyResponse(TypedDict):
    responseHeader: ResponseHeader
    pepAndSanctionsData: Optional[PepAndSanctionsData]
    errorMessage: Optional[ErrorMessage]


class CompanySanctionsResponse(TypedDict):
    companyResponse: CompanyResponse


class ListType(TypedDict):
    listCode: list[WatchListListCode]


class SearchParametersResponse(TypedDict):
    entityType: str  # "I"
    firstName: str
    lastName: str
    birthDate: str
    personId: str
    businessId: str
    companyName: str
    listType: ListType


class Names(TypedDict):
    name: str
    prefix: str | None
    suffix: str | None
    firstName: str
    lastName: str
    aka: str
    primaryName: str


class Identifiers(TypedDict):
    entityId: str
    directId: str
    passportId: str
    nationalId: str | None
    otherId: str | None
    parentId: str


class AddressSource(TypedDict):
    addressSourceAbbreviation: str | None
    addressSourceName: str | None
    addressSourceCountry: str | None


class Address(TypedDict):
    addressId: str
    addressDetails: str
    city: str
    stateProvince: str | None
    country: str
    postalCode: str
    remarks: str | None
    addressSource: AddressSource


class AddressRow(TypedDict):
    addressRow: list[Address]


class EntitySource(TypedDict):
    ensitySourceAbbreviation: str | None
    entitySourceName: str | None
    entitySourceCountry: str | None
    effectiveDate: str | None
    expirationDate: str | None


class WatchListHitEntry(TypedDict):
    hitId: str
    names: Names
    identifiers: Identifiers
    entityType: str  # e.g. "INDIVIDUAL"
    description: str
    dateOfBirth: str  # e.g. "February 21, 1924"
    dateOfBirth2: str | None
    placeOfBirth: str
    country: str
    touchDate: str  # e.g. "2024-03-04 13:04:00.0"
    addresses: AddressRow
    entitySource: EntitySource


class WatchListHits(TypedDict):
    hitsRow: list[WatchListHitEntry]


class WatchListCategory(TypedDict):
    watchListType: WatchListListCode
    hitCount: str
    watchListHits: WatchListHits


class WatchList(TypedDict):
    category: list[WatchListCategory]


class WatchListResponse(TypedDict):
    responseHeader: ResponseHeader
    searchParameters: SearchParametersResponse
    watchLists: Optional[WatchList]
    errorMessage: Optional[ErrorMessage]


class WatchListSearchResponse(TypedDict):
    watchListResponse: WatchListResponse
