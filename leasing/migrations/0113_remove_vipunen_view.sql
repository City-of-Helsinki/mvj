DO
$$BEGIN
    IF EXISTS (
        SELECT FROM pg_roles
        WHERE rolname = 'kami'
    ) THEN
        -- Revoke all privileges granted to the role
        DROP OWNED BY kami;
        -- Remove role
        DROP ROLE kami;
    END IF;
END$$;

-- Drop Vipunen database view
DROP VIEW IF EXISTS public.paikkatietovipunen_vuokraalueet;
