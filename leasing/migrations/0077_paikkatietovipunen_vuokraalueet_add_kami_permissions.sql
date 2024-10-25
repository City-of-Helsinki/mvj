-- View: public.paikkatietovipunen_vuokraalueet

CREATE OR REPLACE VIEW public.paikkatietovipunen_vuokraalueet
AS
SELECT lease.id AS vuokraus_id,
    l_area.identifier AS kiinteistotunnus,
    ltype.identifier AS tyypin_tunnus,
    lid.identifier AS vuokraustunnus,
    (
        SELECT leasing_contract.contract_number
        FROM leasing_contract
        WHERE leasing_contract.lease_id = lease.id
        ORDER BY leasing_contract.contract_number
        LIMIT 1
    ) AS sopimusnumero,
    (
        SELECT leasing_contract.signing_date
        FROM leasing_contract
        WHERE leasing_contract.lease_id = lease.id
        ORDER BY leasing_contract.contract_number
        LIMIT 1
    ) AS sopimus_allekirjoitettu,
    lease.reference_number AS vuokraus_diaari,
    (
        SELECT array_to_string(
            array_agg(
                CASE
                    WHEN c.type::text = 'person'::text THEN 'Henkilö'::text
                    WHEN c.type::text = 'business'::text THEN 'Yritys'::text
                    WHEN c.type::text = 'unit'::text THEN 'Yksikkö'::text
                    WHEN c.type::text = 'association'::text THEN 'Yhteisö'::text
                    WHEN c.type::text = 'other'::text THEN 'Muu'::text
                    ELSE NULL::text
                END
            ), ', '::text
        ) AS array_to_string
        FROM leasing_contact c
        WHERE (
            c.id IN (
                SELECT DISTINCT tc.contact_id
                FROM leasing_tenantcontact tc
                WHERE tc.type::text = 'tenant'::text
                    AND (
                        tc.end_date IS NULL OR tc.end_date > now()
                    )
                    AND (
                        tc.tenant_id IN (
                            SELECT t.id
                            FROM leasing_tenant t
                            WHERE t.lease_id = lease.id
                        )
                    )
            )
        )
    ) AS vuokralaiset_tyypit,
    (
        SELECT array_to_string(
            array_agg(
                CASE
                    WHEN c.type::text = 'person'::text THEN concat(c.last_name, ' ', c.first_name)
                    WHEN c.type::text = 'business'::text THEN c.name::text
                    WHEN c.type::text = 'unit'::text THEN c.name::text
                    WHEN c.type::text = 'association'::text THEN c.name::text
                    WHEN c.type::text = 'other'::text THEN c.name::text
                    ELSE NULL::text
                END
            ), ', '::text
        ) AS array_to_string
        FROM leasing_contact c
        WHERE (
            c.id IN (
                SELECT DISTINCT tc.contact_id
                FROM leasing_tenantcontact tc
                WHERE tc.type::text = 'tenant'::text
                    AND (
                        tc.end_date IS NULL OR tc.end_date > now()
                    )
                    AND (
                        tc.tenant_id IN (
                            SELECT t.id
                            FROM leasing_tenant t
                            WHERE t.lease_id = lease.id
                        )
                    )
            )
        )
    ) AS vuokralaiset_nimet,
    (
        SELECT array_to_string(
            array_agg(c.address), ', '::text
        ) AS array_to_string
        FROM leasing_contact c
        WHERE (
            c.id IN (
                SELECT DISTINCT tc.contact_id
                FROM leasing_tenantcontact tc
                WHERE tc.type::text = 'tenant'::text
                    AND (
                        tc.end_date IS NULL
                        OR tc.end_date > now()
                    )
                    AND (
                        tc.tenant_id IN (
                            SELECT t.id
                            FROM leasing_tenant t
                            WHERE t.lease_id = lease.id
                        )
                    )
            )
        )
    ) AS vuokralaiset_osoitteet,
    (
        SELECT array_to_string(
            array_agg(
                CASE
                    WHEN c.type::text = 'person'::text THEN 'Henkilö'::text
                    WHEN c.type::text = 'business'::text THEN 'Yritys'::text
                    WHEN c.type::text = 'unit'::text THEN 'Yksikkö'::text
                    WHEN c.type::text = 'association'::text THEN 'Yhteisö'::text
                    WHEN c.type::text = 'other'::text THEN 'Muu'::text
                    ELSE NULL::text
                END
            ), ', '::text
        ) AS array_to_string
        FROM leasing_contact c
        WHERE (
            c.id IN (
                SELECT DISTINCT tc.contact_id
                FROM leasing_tenantcontact tc
                WHERE tc.type::text = 'contact'::text
                    AND (
                        tc.end_date IS NULL
                        OR tc.end_date > now()
                    )
                    AND (
                        tc.tenant_id IN (
                            SELECT t.id
                            FROM leasing_tenant t
                            WHERE t.lease_id = lease.id
                        )
                    )
            )
        )
    ) AS yhteyshenkilot_tyypit,
    (
        SELECT array_to_string(
            array_agg(
                CASE
                    WHEN c.type::text = 'person'::text THEN concat(c.last_name, ' ', c.first_name)
                    WHEN c.type::text = 'business'::text THEN c.name::text
                    WHEN c.type::text = 'unit'::text THEN c.name::text
                    WHEN c.type::text = 'association'::text THEN c.name::text
                    WHEN c.type::text = 'other'::text THEN c.name::text
                    ELSE NULL::text
                END
            ), ', '::text
        ) AS array_to_string
        FROM leasing_contact c
        WHERE (
            c.id IN (
                SELECT DISTINCT tc.contact_id
                FROM leasing_tenantcontact tc
                WHERE tc.type::text = 'contact'::text
                    AND (
                        tc.end_date IS NULL
                        OR tc.end_date > now()
                    )
                    AND (
                        tc.tenant_id IN (
                            SELECT t.id
                            FROM leasing_tenant t
                            WHERE t.lease_id = lease.id
                        )
                    )
            )
        )
    ) AS yhteyshenkilot_nimet,
    (
        SELECT array_to_string(
            array_agg(c.address), ', '::text
        ) AS array_to_string
        FROM leasing_contact c
        WHERE (
            c.id IN (
                SELECT DISTINCT tc.contact_id
                FROM leasing_tenantcontact tc
                WHERE tc.type::text = 'contact'::text
                    AND (
                        tc.end_date IS NULL
                        OR tc.end_date > now()
                    ) AND (
                        tc.tenant_id IN (
                            SELECT t.id
                            FROM leasing_tenant t
                            WHERE t.lease_id = lease.id
                        )
                    )
            )
        )
    ) AS yhteyshenkilot_osoitteet,
    (
        SELECT aa.address
        FROM leasing_leaseareaaddress aa
        WHERE aa.lease_area_id = l_area.id AND aa.is_primary
        LIMIT 1
    ) AS ensisijainen_osoite,
    lease.start_date AS vuokraus_alkupvm,
    lease.end_date AS vuokraus_loppupvm,
    np.name AS irtisanomisaika,
    liu.name AS vuokraus_kayttotarkoitus,
    CASE
        WHEN lease.end_date IS NULL THEN 'kyllä'::text
        WHEN lease.end_date > now() THEN 'kyllä'::text
        WHEN lease.end_date < now() THEN 'ei'::text
        ELSE NULL::text
    END AS vuokraus_voimassa,
    CASE
        WHEN lease.state::text = 'permission'::text THEN 'Lupa'::text
        WHEN lease.state::text = 'lease'::text THEN 'Vuokraus'::text
        WHEN lease.state::text = 'short_term_lease'::text THEN 'Lyhytaikainen vuokraus'::text
        WHEN lease.state::text = 'long_term_lease'::text THEN 'Pitkäaikainen vuokraus'::text
        WHEN lease.state::text = 'reservation'::text THEN 'Varaus'::text
        WHEN lease.state::text = 'reserve'::text THEN 'Varanto'::text
        WHEN lease.state::text = 'application'::text THEN 'Hakemus'::text
        WHEN lease.state::text = 'rya'::text THEN 'RYA'::text
        ELSE NULL::text
    END AS vuokraus_tila,
    l_area.area AS pintaala,
    l_area.section_area AS leikkauspintaala,
    (
        SELECT sum(leasing_rent.payable_rent_amount) AS sum
        FROM leasing_rent
        WHERE leasing_rent.lease_id = lease.id
    ) AS perittava_vuokra_summa,
    (
        SELECT concat(
            to_char(
                leasing_rent.payable_rent_start_date::timestamp with time zone, 'fmDD.fmMM.YYYY'::text
            ),
            ' - ',
            to_char(
                leasing_rent.payable_rent_end_date::timestamp with time zone, 'fmDD.fmMM.YYYY'::text
                )
        ) AS concat
        FROM leasing_rent
        WHERE leasing_rent.lease_id = lease.id
        ORDER BY leasing_rent.payable_rent_start_date DESC
        LIMIT 1
    ) AS perittava_vuokra_jakso,
    lease.note AS vuokraus_huom,
    ltype.name AS vuokraus_tyyppi,
    CASE
        WHEN l_area.location::text = 'surface'::text THEN 'Yläpuolella'::text
        WHEN l_area.location::text = 'underground'::text THEN 'Alapuolella'::text
        ELSE NULL::text
    END AS sijainti,
    st_transform(l_area.geometry, 3879) AS geometria,
    CASE
        WHEN su.id = 1 THEN 'MAKE/Tontit'
        WHEN su.id = 2 THEN 'AKV'
        WHEN su.id = 3 THEN 'KUVA (LIPA)'
        WHEN su.id = 4 THEN 'KUVA (UPA)'
        WHEN su.id = 5 THEN 'KUVA (NUP)'
        ELSE NULL::text
    END AS palvelukokonaisuus,
    CASE
        WHEN lessor.type::text = 'person'::text THEN concat(lessor.last_name, ' ', lessor.first_name)
        WHEN lessor.type::text = 'business'::text THEN lessor.name::text
        WHEN lessor.type::text = 'unit'::text THEN lessor.name::text
        WHEN lessor.type::text = 'association'::text THEN lessor.name::text
        WHEN lessor.type::text = 'other'::text THEN lessor.name::text
        ELSE NULL::text
    END AS vuokranantaja
FROM leasing_leasearea l_area
    JOIN leasing_lease lease ON l_area.lease_id = lease.id
    JOIN leasing_leaseidentifier lid ON l_area.lease_id = lid.id
    JOIN leasing_leasetype ltype ON lease.type_id = ltype.id
    LEFT JOIN leasing_intendeduse liu ON lease.intended_use_id = liu.id
    LEFT JOIN leasing_noticeperiod np ON lease.notice_period_id = np.id
    LEFT JOIN leasing_contact lessor ON lessor.id = lease.lessor_id
    LEFT JOIN leasing_serviceunit su ON lease.service_unit_id = su.id
WHERE
    lease.deleted IS NULL
    AND l_area.archived_at IS NULL
    AND l_area.deleted IS NULL
    AND (lease.end_date IS NULL OR lease.end_date > now());

-- Create the Vipunen role "kami" if it didn't exist already.
--
-- NOTE: Set the password manually afterwards if the role did't exist already,
-- before giving Vipunen personnel access to the new role:
--     ALTER ROLE kami WITH PASSWORD 'strong password here';
DO
$do$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_roles
        WHERE rolname = 'kami'
    ) THEN
        CREATE ROLE kami;
    END IF;
END
$do$;

-- Grant the necessary permissions to Vipunen role "kami".
--
-- NOTE: Give the role the additional permission to connect to the correct MVJ
-- database, if the role didn't exist before:
--     GRANT CONNECT ON DATABASE <db name here> TO kami;

ALTER ROLE kami LOGIN;
GRANT USAGE ON SCHEMA public TO kami;
GRANT SELECT ON public.paikkatietovipunen_vuokraalueet TO kami;
