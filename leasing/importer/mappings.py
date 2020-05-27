from leasing.enums import (
    AreaUnit,
    ContactType,
    InvoiceState,
    InvoiceType,
    LeaseAreaType,
    LeaseState,
    RentAdjustmentType,
    RentCycle,
    RentType,
)

VUOKRALAJI_MAP = {
    # TODO: Is MANUAL the correct default
    None: RentType.MANUAL,
    "1": RentType.FIXED,
    "2": RentType.INDEX,
    "3": RentType.ONE_TIME,
    "4": RentType.FREE,
    "5": RentType.MANUAL,
}

TILA_MAP = {
    "V": LeaseState.LEASE,
    "H": LeaseState.APPLICATION,
    "L": LeaseState.PERMISSION,
    "R": LeaseState.RESERVATION,
    "S": LeaseState.LEASE,
    "T": LeaseState.LEASE,
}

VUOKRAKAUSI_MAP = {
    None: None,
    "1": RentCycle.JANUARY_TO_DECEMBER,
    "2": RentCycle.APRIL_TO_MARCH,
}

ALENNUS_KOROTUS_MAP = {
    "A": RentAdjustmentType.DISCOUNT,
    "K": RentAdjustmentType.INCREASE,
}

# Values from receivable_type.json fixture
SAAMISLAJI_MAP = {"VU": 1, "KO": 2, "VT": 3}

LASKUN_TILA_MAP = {
    "H": InvoiceState.REFUNDED,
    "A": InvoiceState.OPEN,
    "S": InvoiceState.PAID,
}

LASKUTYYPPI_MAP = {"V": InvoiceType.CHARGE, "H": InvoiceType.CREDIT_NOTE}

ASIAKASTYYPPI_MAP = {
    None: ContactType.OTHER,
    "0": ContactType.PERSON,
    "1": ContactType.BUSINESS,
    "2": ContactType.UNIT,
    "3": ContactType.ASSOCIATION,
    "4": ContactType.OTHER,
}

MAA_MAP = {
    None: None,
    "FI": "FI",
    "LI": "LI",
    "NL": "NL",
    "NC": "NZ",
    "S": "SE",
    "EG": "EG",
    "U": "US",
}

IRTISANOMISAIKA_MAP = {
    "01": 3,  # 2 viikon irtisanomisaika
    "02": 7,  # 1 kk:n irtisanomisaika
    "03": 8,  # 2 kk:n irtisanomisaika
    "04": 9,  # 3 kk:n irtisanomisaika
    "10": 16,  # muu irtisanomisaika
    "05": 10,  # 6 kk:n irtisanomisaika
    "06": 13,  # 1 vuoden irtisanomisaika
    "07": 14,  # 2 vuoden irtisanomisaika
    "08": 12,  # 15 kkn irtisanomisaika
    "09": 15,  # 3 vuoden irtisanomisaika
    "11": 2,  # 1 viikon irtisanomisaika
    "12": 4,  # 3 viikon irtisanomisaika
    "13": 1,  # Ei irtisanomisaikaa (mm.rasite
    "14": 6,  # 30 päivän irtisanomisaika
    "15": 11,  # 9 kk:n irtisanomisaika
    "16": 5,  # 14 vuorok. irtisanomisaika
}

HITAS_MAP = {
    "0": 2,  # Ei hitasta
    "1": 3,  # Hitas I
    "2": 4,  # Hitas II
    "3": 5,  # Laatusääntely
    "4": 6,  # Ei laatusääntelyä
    "5": 7,  # Hitas I tai laatusä.
    "6": 8,  # Ei tietoa
    "7": 9,  # Hitas II (Loikkari)
    "8": 10,  # Hitas (vapautettu)
    "9": 11,  # Hintakontrolloitu
    "A": 1,  # Puolihitas
}

FINANCING_MAP = {
    "0": 5,  # Ei tietoa
    "1": 6,  # Aravalainoitettu
    "2": 7,  # Vapaarahoitteinen
    "3": 8,  # Peruskorjauslaina
    "4": 9,  # Korkotuki
    "5": 10,  # Arava tai korkotuki
    "6": 11,  # Vapaarah. tai arava
    "7": 12,  # Vap.rah. tai korkot.
    "8": 13,  # Korkot./arava/vap.ra
    "9": 14,  # Muu kuin AV ja p. KT
    "A": 1,  # Korkotuki yht. pitkä
    "B": 2,  # Korkotuki yht. lyhyt
    "C": 3,  # Korkotuki osakk. om.
    "D": 4,  # Muu
}

MANAGEMENT_MAP = {
    "0": 6,  # Ei tieoa
    "1": 7,  # Omistus
    "2": 8,  # Vuokra
    "3": 9,  # Asumisoikeus
    "4": 10,  # Sekatalo
    "5": 11,  # Vuokra tai asumisoik
    "6": 12,  # Omistus tai vuokra
    "7": 13,  # Omist./vuokra/as.oik
    "8": 14,  # Osaomistus
    "9": 15,  # Asumisoik./osaomist.
    "A": 1,  # koe
    "B": 2,  # koe 2
    "C": 3,  # Asumisoikeus/omistus
    "D": 4,  # Asumisoikeus/vuokra
    "E": 5,  # Omistus ja vuokra
}

LEASE_AREA_TYPE_MAP = {
    None: LeaseAreaType.OTHER,  # Unknown
    "1": LeaseAreaType.PLAN_UNIT,  # Kaavatontti
    "2": LeaseAreaType.REAL_PROPERTY,  # Kiinteistö
    "3": LeaseAreaType.OTHER,  # Siirtolapuutarhapalsta
}

BASIS_OF_RENT_PLOT_TYPE_MAP = {
    None: 1,
    "01": 1,
    "02": 2,
    "03": 3,
    "04": 4,
    "05": 5,
    "06": 6,
    "07": 7,
    "08": 8,
    "10": 9,
    "11": 10,
    "12": 11,
    "13": 12,
    "14": 13,
    "20": 14,
    "21": 15,
    "30": 16,
}

BASIS_OF_RENT_BUILD_PERMISSION_MAP = {
    # key: RAKENNUSOIKEUSTYYPPI, ERITTELY
    ("1", "1"): 1,
    ("1", "2"): 2,
    ("1", "3"): 3,
    ("8", "1"): 4,
    ("2", "1"): 5,
    ("02", "2"): 6,
    ("7", "1"): 7,
    ("07", "2"): 7,
    ("9", "1"): 8,
    ("9", "2"): 9,
    ("10", "1"): 10,
    ("10", "2"): 10,
    ("5", "1"): 11,
    ("4", "1"): 12,
    ("3", "1"): 13,
    ("11", "2"): 14,
    ("6", "1"): 15,
}

BASIS_OF_RENT_RATE_AREA_UNIT_MAP = {
    None: None,
    "m2": AreaUnit.SQUARE_METRE,
    "hm2": AreaUnit.APARTMENT_SQUARE_METRE,
    "km2": AreaUnit.FLOOR_SQUARE_METRE,
    "kem2": AreaUnit.FLOOR_SQUARE_METRE,
    "k-m2": AreaUnit.FLOOR_SQUARE_METRE,
}

DECISION_MAKER_MAP = {
    None: None,
    "AK TOI": 1,  # Alueidenkäyttö toimistopäällik
    "AKPÄÄL": 2,  # Alueidenkäyttöpäällikkö
    "AKTPLK": 3,  # Alueiden käyttö tiimipäällikkö
    "AKYKSP": 4,  # Alueiden käyttö, yksikon pääll
    "APKIRJ": 5,  # Asuntopalvelut kirje
    "APYKSP": 6,  # Asuntopalvelut yksikön pääll.
    "AS": 7,  # Asuntoasiainosasto
    "AS PTL": 8,  # Asunto-os. tstopääll. ptl .
    "ASKIRJ": 9,  # Asuntoasiainosaston kirje
    "ASLK": 10,  # Asuntolautakunta
    "ASOPTL": 11,  # Asunto-os. osastopääll. ptl
    "AT PTK": 12,  # Asuntotontti tstopääll. ptk
    "AT SÄP": 13,  # Asuntotontti tstopääl. sähköp.
    "ATPSÄP": 14,  # Asuntotonttitiimin pääl. s-pos
    "ATT TJ": 15,  # Asuntotuotantotston tj ptl
    "ATTP": 16,  # Asuntotonttitoimiston toimistopäällikkö
    "ATTPLK": 17,  # Asuntotontit tiimipäällikkö
    "ATTTK": 18,  # Asuntotuotantotoimikunta
    "E-S AV": 19,  # Etelä-Suomen Aluevalv.vsto
    "E-S MM": 20,  # Etelä-Suomen maanmittauststo
    "ED OIK": 21,  # Eduskunnan oikeusasiamies
    "EKVSTO": 22,  # Espoon kaupunginvaltuusto
    "ELPTL1": 23,  # Elinkeinot. tstop.(luvat)
    "ELPTL2": 24,  # Elinkeinot. tstop.(tilap.vuok)
    "ELPTL3": 25,  # Elinkeinot. tstop. (siirrot)
    "ELPTL4": 26,  # Elinkeinot.tstop. (toimit.ton)
    "ELPTL5": 27,  # Piirustusten tutkiminen
    "ELPTL6": 28,  # Elinkeinot. tstop. (teoll.ton)
    "ELPTL7": 29,  # Hankinnat
    "ELTSTO": 30,  # Elinkeinotoimisto
    "ETUKES": 31,  # Elintarviketukkukaupan keskus
    "ETULK": 32,  # Elintarviketukkulautakunta
    "GEODEE": 33,  # Kaupungingeodeetti
    "H-O KV": 34,  # -> HAL
    "HAL": 34,  # Kiinteistövirasto hallinto-osasto
    "HE H-O": 35,  # Helsingin hallinto-oikeus
    "HE HAO": 36,  # Helsingin hallinto-oikeus
    "HHO": 37,  # Helsingin hovioikeus
    "HKL": 38,  # Liikennelaitos
    "HKLJK": 39,  # Hgin kgin liikennel. johtokunt
    "HKR": 40,  # Rakennusvirasto
    "HKR KP": 41,  # Rakennusvirasto Katupäällikkö
    "HKRAPÄ": 42,  # Rv:n ka- ja pu. al.käyt.pääl.
    "HKRPAL": 43,  # "HKR, palveluos. tstopäällikkö"
    "HKRPTL": 44,  # rak.viraston toim.johtajan ptl
    "HTR": 45,  # Hitas-työryhmä
    "KA": 46,  # Kansliaosasto
    "KA PTL": 47,  # Kansliaosaston pääll. ptl
    "KAJ": 48,  # Apulaiskaupunginjohtaja
    "KAKIRJ": 49,  # Kansliaosaston kirje
    "KAULA": 50,  # Kaupungin lakimies
    "KEI.SE": 51,  # Keisarillinen senaatti
    "KEISAR": 52,  # Keisarillinen määräys
    "KH YLJ": 57,  # -> KHSYLJ
    "KHO": 53,  # Korkein Hallinto-Oikeus
    "KHS": 54,  # Kaupunginhallitus
    "KHS SJ": 55,  # -> KHS/SJ
    "KHS/SJ": 55,  # kginhallituksen suunnit.jaosto
    "KHSEJA": 56,  # KHS:n elinkeinojaosto
    "KHSYLJ": 57,  # Kaupunginhallituksen yleisjaos
    "KI PTL": 58,  # KI PTL
    "KI/JTU": 59,  # Kirje/Juhani Tuuttila
    "KIRJ": 60,  # KIRJE
    "KJ": 61,  # KJ
    "KK": 62,  # KK
    "KKO": 63,  # KORKEIN OIKEUS
    "KL TJ": 64,  # KL TJ
    "KLH": 65,  # KLH
    "KLK": 66,  # Kiinteistölautakunta
    "KLK/TA": 67,  # Kiinteistölaut. talo-jaos
    "KLKS": 68,  # KLKS
    "KMO": 69,  # Kaupunginmittausosasto
    "KO": 46,  # -> KA
    "KO PL": 70,  # KO PL
    "KO PTL": 71,  # KO PTL
    "KOKIRJ": 49,  # -> KAKIRJ
    "KP PTL": 72,  # KP PTL
    "KSLK": 73,  # Kaupunkisuunnittelulautakunta
    "KSV": 74,  # Kaupunkisuunnitteluvirasto
    "KSV VP": 75,  # Ksv virastopäällikkö
    "KV": 76,  # Kiinteistövirasto
    "KV H-O": 77,  # Kv hallinto-osasto
    "KV HAL": 77,  # -> KV H-O
    "KV KIR": 78,  # Kiinteistövirasto kirje
    "KV/KIR": 78,  # -> KV KIR
    "KVSTO": 79,  # Kaupunginvaltuusto
    "KYLK": 80,  # Kaupunkiympäristölautakunta
    "KYLKJA": 81,  # -> KYLKYL
    "KYLKYL": 81,  # KYLK ympäristö- ja lupajaosto
    "KYMPTJ": 82,  # Kaupunkiympäristön toimialajoh
    "KÄROIK": 83,  # Käräjäoikeus
    "L-S VO": 84,  # L-S VO
    "L-S YM": 85,  # Länsi-Suomen ympäristölupavira
    "LILK": 86,  # Liikuntalautakunta
    "LIV": 87,  # Liikuntavirasto osastopääll.
    "LIVPTL": 88,  # Liikuntavirasto
    "LKL": 66,  # -> KLK
    "MA PTL": 89,  # Maanluovut. tstop. päät (vuok)
    "MAOSOP": 90,  # Maaomaisuus, sopimukset
    "MAPTL1": 91,  # Maanluovut. tstop. päät (piir)
    "MAPTL2": 92,  # Maanluovt. tstop. päät. (hank)
    "MATSTO": 93,  # Maanluovutustoimisto
    "MH": 94,  # Maanhank. tstopääll. lausunto
    "MH PTK": 95,  # Maanhankintat. tstopääll. päät
    "MH PTL": 95,  # -> MH PTK
    "MHTPLK": 96,  # Maanhankinta tiimipäällikkö
    "MIN": 97,  # Sisäasiainministeriö
    "MKJOHT": 98,  # Maankäyttöjohtaja
    "MML": 99,  # Maanmittauslaitos/-toimisto
    "MOTPLK": 100,  # Maaomaisuuden hall. tiimipääl.
    "MOYKSP": 101,  # Maaomaisuus yksikön päällikkö
    "OP PL": 102,  # OP PL
    "OP PTL": 103,  # OP PTL
    "OPPL": 104,  # OPPL
    "PELLK": 105,  # Pelastuslautakunta
    "PT PTK": 106,  # Palvelutsto. tstopääll.
    "RAKLK": 107,  # Rakennuslautakunta
    "RAKVV": 108,  # Rakennusvalvontavirasto
    "RLK ES": 109,  # Rakennuslautakunta Espoo
    "RTKRI": 110,  # Rahatoimikamari
    "SA JK": 111,  # Helsingin sataman johtokunta
    "SA PTL": 112,  # Satamajohtajan päätösluettelo
    "SALK": 113,  # Satamalautakunta
    "SOPTII": 114,  # Vuokrasopimustiimi
    "SOSLK": 115,  # Sosiaalilautakunta
    "TA PTL": 116,  # Talo-os. tstopäällikön ptl
    "TAIPTL": 117,  # Taidemuseon johtajan päätöslue
    "TESTAM": 118,  # Testamentti
    "TI PTL": 119,  # KV TILAKESKUKSEN PÄÄLLIKKÖ
    "TILA": 121,  # Kiinteistöviraston tilakeskus
    "TJ": 122,  # TJ
    "TO": 123,  # Tonttiosasto
    "TO AOP": 124,  # Tonttiosaston ap.os.pääll.ptl
    "TO KIR": 132,  # -> TOKIRJ
    "TO OP": 125,  # Tonttios.pääll.päät.
    "TO PAL": 126,  # Tonttiosasto Palvelutoimisto
    "TO PLK": 127,  # Tonttipäällikkö (Make)
    "TO PTL": 128,  # Tonttios. pääll.
    "TO.KIR": 132,  # -> TOKIRJ
    "TOAPT1": 129,  # To.os. ap.os.pääll.ptl piir.
    "TOAPTL": 130,  # To.os.ap.os.pääll.ptl
    "TOJ": 131,  # Tonttijaosto
    "TOKIRJ": 132,  # Tonttiosaston kirje
    "TOOPKI": 133,  # Tonttiosaston op kirje
    "TOPPT": 134,  # Tonttiosaston pal.tstopääl.ptl
    "TOPTL4": 135,  # Tonttios.pääll.päät.(lyh.vuok)
    "TOPTL7": 136,  # Tonttios.pääll.päät.(piirust.)
    "TOPTL8": 137,  # Tonttios.pääll.pä(rak.l.korv.)
    "TOPTL9": 138,  # Tonttios.pääll.(kiint.om.päät)
    "TOYKSP": 139,  # Tontit-yksikön päällikkö
    "TP PLK": 140,  # Tilapalvelupäällikkö, rya
    "TRO TL": 141,  # TRO TL
    "TYKIRJ": 142,  # Tontit-yksikön kirje
    "TYPSÄP": 143,  # Tontit-yksikön pääl. s-posti
    "UUD.VE": 144,  # Uuudenmaan verovirasto
    "UUDELY": 145,  # Uudenmaan elykeskus
    "UUDLÄH": 146,  # Uuudenmaan lääninhallitus
    "UUDYMK": 147,  # Uudenmaan ympäristökeskus
    "VIRKIR": 148,  # Viraston kirje
    "VO PTL": 150,  # -> VP PTL
    "VP": 149,  # Virastopäällikkö
    "VP PTL": 150,  # Virastopäällikön päät.
    "VÄLK": 151,  # Väestönsuojalautakunta
    "XXX": 152,  # Muu päättäjä
    "YLJ": 153,  # Kaupunginhallituksen yleisjaos
    "YM": 159,  # -> YMPMIN
    "YMK": 156,  # -> YMKHKI
    "YMK/YS": 154,  # Ympäristök. ymp.suojeluosasto
    "YMK/YV": 155,  # Ympäristök, ymp.valvontayksikk
    "YMKHKI": 156,  # Ympäristökeskus
    "YMP.TE": 157,  # Ymp.valv.yksikkö/teoll.valvont
    "YMPLK": 158,  # Ympäristölautakunta
    "YMPMIN": 159,  # Ympäristöministeriö
    "YT PTK": 160,  # Yritystontti tstopääll. ptk
    "YTLK": 161,  # Yleisten töiden lautakunta
    "YTPSÄP": 162,  # Yritystonttitiimi pääl. s-post
    "YTTPLK": 163,  # Yritystontit tiimipäällikkö
    "YTTSTO": 164,  # Yritystonttitoimisto
    "YVPPTL": 165,  # Ympäristövalvontapäällikkö
}

MANUAL_RATIOS = {
    "T3154-14": (19.5, 19.29),
    "T3154-13": (19.5, 19.29),
    "T3154-12": (19.5, 19.29),
    "T3154-11": (19.5, 19.29),
    "T3154-10": (19.5, 19.29),
    "T3154-4": (19.5, 19.29),
    "T3154-2": (19.5, 19.29),
    "T3154-1": (19.5, 19.29),
    "T1155-2": (1.35,),
    "T1155-1": (1.35,),
    "S0108-100": (1.4,),
    "A2131-3": (1.21,),
    "S0149-234": (1.05,),
    "S0147-229": (1.05,),
    "H2138-7": (1.02,),
    "H2110-11": (1.37,),
}
