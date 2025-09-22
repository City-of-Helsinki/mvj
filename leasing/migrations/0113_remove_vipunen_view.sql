-- Remove role `kami`'s permissions
REVOKE ALL PRIVILEGES ON SCHEMA public FROM kami;
REVOKE ALL PRIVILEGES ON public.paikkatietovipunen_vuokraalueet FROM kami;
-- Remove `kami` role
-- Potentially there could be a problem if the role has an active connection
DROP ROLE IF EXISTS kami;
-- Drop Vipunen database view
DROP VIEW IF EXISTS public.paikkatietovipunen_vuokraalueet;
