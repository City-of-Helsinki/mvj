def mock_return_company_json_data(business_id):
    return {
        "companyResponse": {
            "responseHeader": {
                "languageCode": "FI",
                "timeStamp": {"date": 1634590800000, "time": 23365000},
                "responseStatus": "0",
                "currencyCode": "EUR",
            },
            "identificationData": None,
            "companyBasics": None,
            "scoringData": [],
            "companyGroupReferences": None,
            "mergerData": None,
            "companyClassification": None,
            "registerData": None,
            "companyPaymentDefaultData": None,
            "personInCharge": None,
            "decisionMakers": None,
            "personInChargeSummary": [],
            "shareholderData": None,
            "paymentHistory": None,
            "errorMessage": None,
            "confirmationMessage": None,
            "authorisedSignaturesText": None,
            "authorisedSignaturesData": None,
            "mortgageData": None,
            "additionalNamesData": None,
            "newsRow": [],
            "paymentDefaultRefData": None,
            "additionalInformationRow": [],
            "companyHistoryRow": [],
            "lineOfBusinessLongRow": [],
            "listOfCompaniesRow": [],
            "decisionProposalData": {
                "usecode": "1",
                "model": {"code": "HEASYR", "name": "Yritysluottopäätökset"},
                "customerData": {
                    "customerDataRow": [],
                    "customerProductDataRow": [],
                    "name": "Solid Corporation Oy",
                    "businessId": business_id,
                    "personId": None,
                    "insertedInMonitoringText": None,
                    "customerKey": None,
                },
                "decisionProposal": {
                    "handler": None,
                    "inputRow": [],
                    "prosessingDate": 1634590800000,
                    "proposal": {
                        "code": "1",
                        "text": "Luottopäätös edellyttää lisäselvityksiä.",
                        "proposalCode": None,
                        "proposalText": None,
                        "factorRow": [
                            {
                                "code": "004",
                                "text": "Yritystä ei ole merkitty ennakkoperintärekisteriin.",
                            },
                            {
                                "code": "090",
                                "text": "Yritys on vanhempi kuin -1 kuukautta ja tilinpäätös puuttuu.",
                            },
                        ],
                    },
                },
            },
            "companyData": {
                "identificationData": {
                    "businessId": "30101929",
                    "name": "Solid Corporation Oy",
                    "domicileCode": None,
                    "domicile": None,
                    "companyLanguageCode": None,
                    "companyLanguageText": None,
                    "postalAddress": None,
                    "address": {
                        "street": "Kruunuvuorenkatu 3 E",
                        "zip": "00160",
                        "town": "Helsinki",
                    },
                    "contactInformation": {
                        "phone": "+358 44 7200965",
                        "fax": None,
                        "www": None,
                        "email": None,
                    },
                    "companyForm": "OY",
                    "companyFormText": "Osakeyhtiö",
                    "lineOfBusiness": {
                        "lineOfBusinessCode": "62010",
                        "lineOfBusinessText": "Ohjelmistojen suunnittelu ja valmistus",
                    },
                    "naceCode": None,
                    "naceText": None,
                },
                "startDate": None,
            },
            "populationInformation": None,
            "companyPaymentsAnalysis": None,
            "ratios": None,
            "tradeRegisterExtracts": None,
            "articlesOfAssociation": None,
            "authorizedSignature": None,
            "companysDomainNames": None,
            "queryHistoryInformation": None,
            "debtCollectionData": None,
            "bankruptcyIndicator": None,
            "beneficialOwner": None,
            "trustedCompanyData": None,
            "esgData": None,
            "valueReportData": None,
            "digitalActivityData": None,
            "growthIndicator": None,
            "officialRegisterBeneficialOwner": None,
            "authorisedSignaturesAbstract": None,
            "companyInGroup": [],
            "companyRadar": None,
            "leiData": None,
            "companyLoan": None,
            "shareholder2021Data": None,
            "authorizedSignature2021": None,
            "extract": None,
            "einvoiceData": None,
        },
        "groupResponse": None,
    }


def mock_return_consumer_json_data(identity_number):
    return {
        "consumerResponse": {
            "responseHeader": {
                "languageCode": "FI",
                "timeStamp": {"date": 1634590800000, "time": 40333000},
                "responseStatus": "0",
                "currencyCode": "EUR",
            },
            "personInformation": None,
            "profileData": None,
            "scoringBackgroundData": None,
            "scoringData": [],
            "decisionProposalData": {
                "usecode": "1",
                "model": {"code": "HEASKU", "name": "Kuluttajaluottopäätökset"},
                "customerData": {
                    "customerDataRow": [],
                    "customerProductDataRow": [],
                    "name": None,
                    "businessId": None,
                    "personId": identity_number,
                    "insertedInMonitoringText": None,
                    "customerKey": None,
                },
                "decisionProposal": {
                    "handler": None,
                    "inputRow": [],
                    "prosessingDate": 1634590800000,
                    "proposal": {
                        "code": "0",
                        "text": "Ehdotetaan hylättäväksi.",
                        "proposalCode": None,
                        "proposalText": None,
                        "factorRow": [
                            {
                                "code": "041",
                                "text": "Henkilöllä on maksuhäiriöitä 1, joka on vähintään 1 kpl.",
                            }
                        ],
                    },
                },
            },
            "populationInformation": None,
            "personIdentification": None,
            "soletrader": None,
            "paymentDefaultData": None,
            "creditInformationData": None,
            "noRegisteredMessage": None,
            "personInChargeSummary": None,
            "creditSummary": None,
            "assets": None,
            "taxInformation": None,
            "otherInformation": None,
            "errorMessage": None,
            "personInAssociationSummary": None,
            "officialRegisterBeneficialOwner": None,
        }
    }


def mock_return_company_sanctions_json_data():
    return {
        "companyResponse": {
            "responseHeader": {
                "languageCode": "FI",
                "timeStamp": {"date": "2025-03-03", "time": "14:17:35"},
                "responseStatus": "0",
                "currencyCode": "EUR",
            },
            "pepAndSanctionsData": {
                "businessId": "12345678",
                "companyName": "Sanctioned Company Oy",
                "searchStatus": "OK",
                "watchListHits": [
                    {
                        "jotain": "toista",
                        "name": "Southeast Trading Oy",
                        "role": "Yritys",
                        "hitCount": "1",
                        "hitsRow": [
                            {
                                "watchListType": "SANCTION_LIST",
                                "hitId": "1",
                                "names": {"name": "SANCTIONED COMPANY OY"},
                                "description": "Added to OFAC's SDN List.",
                                "entitySource": {
                                    "entitySourceAbbreviation": "OFAC",
                                    "entitySourceCountry": "United States",
                                },
                            }
                        ],
                    },
                    {
                        "jotain": "muuta",
                        "name": "Doe, John",
                        "role": "Varsinainen j\u00e4sen",
                        "hitCount": "0",
                    },
                ],
            },
        }
    }


def mock_return_consumer_sanctions_json_data():
    return {
        "watchListResponse": {
            "responseHeader": {
                "languageCode": None,
                "timeStamp": {"date": "2025-02-27", "time": "17:01:35"},
                "responseStatus": "0",
                "currencyCode": "",
            },
            "searchParameters": {
                "entityType": "I",
                "firstName": None,
                "lastName": "Lastname",
                "birthDate": None,
                "personId": None,
                "businessId": None,
                "companyName": None,
                "listType": {"listCode": ["SANCTION_LIST"]},
            },
            "watchLists": {
                "category": [
                    {
                        "watchListType": "SANCTION_LIST",
                        "hitCount": "10",
                        "watchListHits": {
                            "hitsRow": [
                                {
                                    "hitId": "1",
                                    "names": {
                                        "name": "Doe, John Michael",
                                        "prefix": None,
                                        "firstName": "John Michael",
                                        "lastName": "Doe",
                                        "suffix": None,
                                        "aka": "Mad Doe,Hurricane Doe",
                                        "primaryName": None,
                                    },
                                    "identifiers": {
                                        "entityId": "1261261",
                                        "directId": "3f8c9b2e-5d4b-4e1b-9b2e-5d4b4e1b9b2e",
                                        "passportId": "AB004321;AB004320",
                                        "nationalId": None,
                                        "otherId": None,
                                        "parentId": "0",
                                    },
                                    "entityType": "INDIVIDUAL",
                                    "description": "Sanctioned Entity. Former President Doeland (Novemer 1, 1993 - November 2, 1993). Suspected of corruption - November 1993. Deceased November 3, 1993.",  # noqa: E501
                                    "dateOfBirth": "January 1, 1950",
                                    "dateOfBirth2": None,
                                    "placeOfBirth": "Palembang, Indonesia",
                                    "country": "Indonesia",
                                    "touchDate": "2024-01-01 12:00:00.0",
                                    "addresses": {
                                        "addressRow": [
                                            {
                                                "addressId": "13456789",
                                                "addressDetails": "Corner of 1st Street and 2nd Avenue",
                                                "city": "Doha",
                                                "stateProvince": None,
                                                "country": "Qatar",
                                                "postalCode": None,
                                                "remarks": None,
                                                "addressSource": {
                                                    "addressSourceAbbreviation": None,
                                                    "addressSourceName": None,
                                                    "addressSourceCountry": None,
                                                },
                                            },
                                            {
                                                "addressId": "23456789",
                                                "addressDetails": "Street of 3rd Avenue",
                                                "city": "Addis Ababa",
                                                "stateProvince": None,
                                                "country": "Ethiopia",
                                                "postalCode": None,
                                                "remarks": None,
                                                "addressSource": {
                                                    "addressSourceAbbreviation": None,
                                                    "addressSourceName": None,
                                                    "addressSourceCountry": None,
                                                },
                                            },
                                        ]
                                    },
                                    "entitySource": {
                                        "entitySourceAbbreviation": "Sanctions",
                                        "entitySourceName": "Consolidated Sanctions List",
                                        "entitySourceCountry": "International",
                                        "effectiveDate": None,
                                        "expirationDate": None,
                                    },
                                },
                                {
                                    "hitId": "2",
                                    "names": {
                                        "name": "Doe, John 2nd",
                                        "prefix": None,
                                        "firstName": "John",
                                        "lastName": "Doe",
                                        "suffix": None,
                                        "aka": "Tornado Doe",
                                        "primaryName": None,
                                    },
                                    "identifiers": {
                                        "entityId": "3434340",
                                        "directId": "63d97caa-36f5-4ad1-b368-00737c480a6a",
                                        "passportId": "A1234569",
                                        "nationalId": None,
                                        "otherId": None,
                                        "parentId": "0",
                                    },
                                    "entityType": "INDIVIDUAL",
                                    "description": "Sanctioned Entity. Son of John Michael Doe, Former President Doeland.",  # noqa: E501
                                    "dateOfBirth": "June 2, 1994",
                                    "dateOfBirth2": None,
                                    "placeOfBirth": "Doecity, Doeland",
                                    "country": "Doeland",
                                    "touchDate": "2025-01-01 10:00:00.0",
                                    "addresses": {"addressRow": []},
                                    "entitySource": {
                                        "entitySourceAbbreviation": "Sanctions",
                                        "entitySourceName": "Consolidated Sanctions List",
                                        "entitySourceCountry": "International",
                                        "effectiveDate": None,
                                        "expirationDate": None,
                                    },
                                },
                            ]
                        },
                    }
                ]
            },
            "errorMessage": None,
        }
    }
