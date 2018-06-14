from leasing.enums import (
    AreaUnit, ContactType, InvoiceState, InvoiceType, LeaseAreaType, LeaseState, RentAdjustmentType, RentCycle,
    RentType)

VUOKRALAJI_MAP = {
    # TODO: Is MANUAL the correct default
    None: RentType.MANUAL,
    '1': RentType.FIXED,
    '2': RentType.INDEX,
    '3': RentType.ONE_TIME,
    '4': RentType.FREE,
    '5': RentType.MANUAL,
}

TILA_MAP = {
    'V': LeaseState.LEASE,
    'H': LeaseState.APPLICATION,
    'L': LeaseState.PERMISSION,
    'R': LeaseState.RESERVATION,
    'S': LeaseState.TRANSFERRED,
    'T': LeaseState.FREE,
}

VUOKRAKAUSI_MAP = {
    None: None,
    '1': RentCycle.JANUARY_TO_DECEMBER,
    '2': RentCycle.APRIL_TO_MARCH,
}

ALENNUS_KOROTUS_MAP = {
    'A': RentAdjustmentType.DISCOUNT,
    'K': RentAdjustmentType.INCREASE,
}

# Values from receivable_type.json fixture
SAAMISLAJI_MAP = {
    'VU': 1,
    'KO': 2,
}

LASKUN_TILA_MAP = {
    'H': InvoiceState.REFUNDED,
    'A': InvoiceState.OPEN,
    'S': InvoiceState.PAID,
}

LASKUTYYPPI_MAP = {
    'V': InvoiceType.CHARGE,
    'H': InvoiceType.CREDIT_NOTE,
}

ASIAKASTYYPPI_MAP = {
    None: ContactType.OTHER,
    '0': ContactType.PERSON,
    '1': ContactType.BUSINESS,
    '2': ContactType.UNIT,
    '3': ContactType.ASSOCIATION,
    '4': ContactType.OTHER,
}

IRTISANOMISAIKA_MAP = {
    '01': 3,  # 2 viikon irtisanomisaika
    '02': 7,  # 1 kk:n irtisanomisaika
    '03': 8,  # 2 kk:n irtisanomisaika
    '04': 9,  # 3 kk:n irtisanomisaika
    '10': 16,  # muu irtisanomisaika
    '05': 10,  # 6 kk:n irtisanomisaika
    '06': 13,  # 1 vuoden irtisanomisaika
    '07': 14,  # 2 vuoden irtisanomisaika
    '08': 12,  # 15 kkn irtisanomisaika
    '09': 15,  # 3 vuoden irtisanomisaika
    '11': 2,  # 1 viikon irtisanomisaika
    '12': 4,  # 3 viikon irtisanomisaika
    '13': 1,  # Ei irtisanomisaikaa (mm.rasite
    '14': 6,  # 30 päivän irtisanomisaika
    '15': 11,  # 9 kk:n irtisanomisaika
    '16': 5,  # 14 vuorok. irtisanomisaika
}

HITAS_MAP = {
    '0': 2,  # Ei hitasta
    '1': 3,  # Hitas I
    '2': 4,  # Hitas II
    '3': 5,  # Laatusääntely
    '4': 6,  # Ei laatusääntelyä
    '6': 8,  # Ei tietoa
    '7': 9,  # Hitas II (Loikkari)
    '8': 10,  # Hitas (vapautettu)
    '9': 11,  # Hintakontrolloitu
    'A': 1,  # Puolihitas
}

FINANCING_MAP = {
    '0': 5,  # Ei tietoa
    '1': 6,  # Aravalainoitettu
    '2': 7,  # Vapaarahoitteinen
    '3': 8,  # Peruskorjauslaina
    '4': 9,  # Korkotuki
    '5': 10,  # Arava tai korkotuki
    '6': 11,  # Vapaarah. tai arava
    '7': 12,  # Vap.rah. tai korkot.
    '8': 13,  # Korkot./arava/vap.ra
    '9': 14,  # Muu kuin AV ja p. KT
    'A': 1,  # Korkotuki yht. pitkä
    'B': 2,  # Korkotuki yht. lyhyt
    'C': 3,  # Korkotuki osakk. om.
    'D': 4,  # Muu
}

MANAGEMENT_MAP = {
    '0': 6,  # Ei tieoa
    '1': 7,  # Omistus
    '2': 8,  # Vuokra
    '3': 9,  # Asumisoikeus
    '4': 10,  # Sekatalo
    '5': 11,  # Vuokra tai asumisoik
    '6': 12,  # Omistus tai vuokra
    '7': 13,  # Omist./vuokra/as.oik
    '8': 14,  # Osaomistus
    '9': 15,  # Asumisoik./osaomist.
    'A': 1,  # koe
    'B': 2,  # koe 2
    'C': 3,  # Asumisoikeus/omistus
    'D': 4,  # Asumisoikeus/vuokra
    'E': 5,  # Omistus ja vuokra
}

LEASE_AREA_TYPE_MAP = {
    None: LeaseAreaType.OTHER,  # Unknown
    '1': LeaseAreaType.PLAN_UNIT,  # Kaavatontti
    '2': LeaseAreaType.REAL_PROPERTY,  # Kiinteistö
    '3': LeaseAreaType.OTHER,  # Siirtolapuutarhapalsta
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
    ('1', '1'): 1,
    ('1', '2'): 2,
    ('1', '3'): 3,
    ('8', '1'): 4,
    ('2', '1'): 5,
    ('02', '2'): 6,
    ('7', '1'): 7,
    ('07', '2'): 7,
    ('9', '1'): 8,
    ('9', '2'): 9,
    ('10', '1'): 10,
    ('10', '2'): 10,
    ('5', '1'): 11,
    ('4', '1'): 12,
    ('3', '1'): 13,
    ('11', '2'): 14,
    ('6', '1'): 15,
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
    'KLK': 54,  # Kiinteistölautakunta
    'KSLK': 58,  # Kaupunkisuunnittelulautakunta
    'MIN': 79,  # Sisäasiainministeriö
    'KHS': 47,  # Kaupunginhallitus
    'TO OP': 102,  # Tonttios.pääll.päät.
    'RTKRI': 88,  # Rahatoimikamari
    'KVSTO': 64,  # Kaupunginvaltuusto
    'KA PTL': 40,  # Kansliaosaston pääll. ptl
    'KONVER': 57,  # Konversio-ohjelmisto
    'ASLK': 7,  # Asuntolautakunta
    'AS PTL': 5,  # Asunto-os. tstopääll. ptl .
    'SALK': 91,  # Satamalautakunta
    'TOJ': 108,  # Tonttijaosto
    'VP PTL': 123,  # Virastopäällikön päät.
    'YTLK': 133,  # Yleisten töiden lautakunta
    'HTR': 38,  # Hitas-työryhmä
    'KAJ': 41,  # Apulaiskaupunginjohtaja
    'KHSYLJ': 50,  # Kaupunginhallituksen yleisjaos
    'KLK/TA': 55,  # Kiinteistölaut. talo-jaos
    'KHS/SJ': 49,  # kginhallituksen suunnit.jaosto
    'HKRPTL': 37,  # rak.viraston toim.johtajan ptl
    'ASOPTL': 8,  # Asunto-os. osastopääll. ptl
    'KA': 39,  # Kansliaosasto
    'XXX': 125,  # Muu päättäjä
    'ELPTL1': 17,  # Elinkeinot. tstop.(luvat)
    'ELPTL2': 18,  # Elinkeinot. tstop.(tilap.vuok)
    'HKL': 32,  # Liikennelaitos
    'TO': 100,  # Tonttiosasto
    'YMPMIN': 130,  # Ympäristöministeriö
    'HKR': 34,  # Rakennusvirasto
    'VP': 122,  # Virastopäällikkö
    'RAKVV': 86,  # Rakennusvalvontavirasto
    'TOKIRJ': 109,  # Tonttiosaston kirje
    'KAKIRJ': 42,  # Kansliaosaston kirje
    'RAKLK': 85,  # Rakennuslautakunta
    'VIRKIR': 121,  # Viraston kirje
    'GEODEE': 29,  # Kaupungingeodeetti
    'KHO': 46,  # Korkein Hallinto-Oikeus
    'UUDYMK': 120,  # Uudenmaan ympäristökeskus
    'ELPTL3': 19,  # Elinkeinot. tstop. (siirrot)
    'KEISAR': 44,  # KEISARILLINEN MÄÄRÄYS
    'KKO': 53,  # KORKEIN OIKEUS
    'KI/JTU': 51,  # Kirje/Juhani Tuuttila
    'ASKIRJ': 6,  # Asuntoasiainosaston kirje
    'UUD.VE': 119,  # Uuudenmaan verovirasto
    'YMPLK': 129,  # Ympäristölautakunta
    'LILK': 70,  # Liikuntalautakunta
    'YMKHKI': 126,  # Ympäristökeskus
    'ED OIK': 15,  # Eduskunnan oikeusasiamies
    'TA PTL': 94,  # Talo-os. tstopäällikön ptl
    'AS': 4,  # Asuntoasiainosasto
    'LIV': 71,  # Liikuntavirasto osastopääll.
    'ELPTL4': 20,  # Elinkeinot.tstop. (toimit.ton)
    'ATTTK': 14,  # Asuntotuotantotoimikunta
    'YLJ': 50,  # Kaupunginhallituksen yleisjaos
    'ELPTL5': 21,  # Piirustusten tutkiminen
    'HE H-O': 30,  # Helsingin hallinto-oikeus
    'ELPTL6': 22,  # Elinkeinot. tstop. (teoll.ton)
    'KIRJ': 52,  # KIRJE
    'ETULK': 28,  # ELINTARVIKETUKKULAUTAKUNTA
    'KEI.SE': 45,  # Keisarillinen senaatti
    'HHO': 31,  # Helsingin hovioikeus
    'EKVSTO': 16,  # Espoon kaupunginvaltuusto
    'KAULA': 43,  # Kaupungin lakimies
    'HE HAO': 30,  # Helsingin hallinto-oikeus
    'KMO': 56,  # Kaupunginmittausosasto
    'TOAPT1': 107,  # To.os. ap.os.pääll.ptl piir.
    'MML': 80,  # Maanmittauslaitos/-toimisto
    'E-S MM': 26,  # Etelä-Suomen maanmittauststo
    'KV': 61,  # Kiinteistövirasto
    'ELPTL7': 23,  # Hankinnat
    'PELLK': 83,  # Pelastuslautakunta
    'ELTSTO': 24,  # Elinkeinotoimisto
    'MATSTO': 76,  # Maanluovutustoimisto
    'TILA': 99,  # Kiinteistöviraston tilakeskus
    'ATT TJ': 12,  # Asuntotuotantotston tj ptl
    # 'KV H-O': 63,  # Kv hallinto-osasto
    'SOSLK': 93,  # Sosiaalilautakunta
    'VÄLK': 124,  # Väestönsuojalautakunta
    'ETUKES': 27,  # Elintarviketukkukaupan keskus
    'KV H-O': 62,  # KV:n Hallinto-osasto
    'E-S AV': 25,  # Etelä-Suomen Aluevalv.vsto
    'UUDELY': 117,  # Uudenmaan elykeskus
    # 'TI PTL': 98,  # KV TILAKESKUKSEN PÄÄLLIKKÖ
    'TOAPTL': 106,  # To.os.ap.os.pääll.ptl
    'RLK ES': 87,  # Rakennuslautakunta Espoo
    'TO PLK': 104,  # Tonttipäällikkö (Make)
    'TOYKSP': 116,  # Tontit-yksikön päällikkö
    'KYLK': 65,  # Kaupunkiympäristölautakunta
    'ATTPLK': 13,  # Asuntotontit tiimipäällikkö
    'YTTPLK': 135,  # Yritystontit tiimipäällikkö
    'TESTAM': 96,  # Testamentti
    'TI PTL': 97,  # Tilakes.päällikön ptl
    'HKLJK': 33,  # Hgin kgin liikennel. johtokunt
    'TO PAL': 103,  # Tonttiosasto Palvelutoimisto
    'PT PTK': 84,  # Palvelutsto. tstopääll.
    'SA JK': 89,  # Helsingin sataman johtokunta
    'TOOPKI': 110,  # Tonttiosaston op kirje
    'AT PTK': 9,  # Asuntotontti tstopääll. ptk
    'YT PTK': 132,  # Yritystontti tstopääll. ptk
    'YTTSTO': 136,  # Yritystonttitoimisto
    'KSV': 59,  # Kaupunkisuunnitteluvirasto
    'KSV VP': 60,  # Ksv virastopäällikkö
    'TO PTL': 105,  # Tonttios. pääll.
    'SOPTII': 92,  # Vuokrasopimustiimi
}
