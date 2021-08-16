-- Compact log entries to the log table.
--
-- Combines the individual log entries of a single job run (specified by
-- log_run_id) from the log entry table (batchrun_jobrunlogentry) to a
-- row in the (compacted) log table (batchrun_jobrunlog).
--
-- NOTE: Before calling this procedure, a row for the specified job run
-- should be created to the log table with empty content and entry_data
-- fields.  Those fields are then filled with this procedure.  The
-- input log entries are not deleted.
--
-- What is log compacting and why it is needed?
-- --------------------------------------------
--
-- In the log entry table each logged line or part of a line is stored
-- to a single database row with timestamp and stream kind (stdout/err).
-- This makes it simple to store the log data to the database on the fly
-- when log lines are being produced, but is not space efficient for
-- long time storage, since individual log lines are not compressed (and
-- wouldn't compress very well either).  Certain database queries to the
-- log entry table also begin to slow down after the table grows to too
-- many millions of rows.  One of such queries is SELECT COUNT(*) over
-- all rows which Django Admin wants to do for its pagination.
--
-- To make the log data compressable and lessen the burden from the log
-- entry table, older log entries can be "compacted".  This means that
-- the individual log entries are sorted by time and concatenated as a
-- single big text content and the metadata information of the log entry
-- boundaries, timestamps and stream kinds is stored to additional JSON
-- field called entry_data.  These database fields are then
-- automatically compressed by the PostgreSQL's TOAST mechanism saving a
-- lot of disk space compared to the individually stored log entries (in
-- factor of ten).
--
-- There is a Python class CompactLog which can iterate the log entries
-- (as if they were still separated) of the compacted logs by utilizing
-- the metadata in the entry_data field.
create procedure batchrun_compact_log_entries (log_run_id integer)
    language plpgsql
as $$
declare
    existing_log_id integer;
    start_timestamp timestamp with time zone;
begin
    -- Make sure that the log row is already created
    begin
        select id into strict existing_log_id
        from batchrun_jobrunlog
        where run_id=log_run_id;
    exception
        when no_data_found then
            raise exception 'Create an entry to batchrun_jobrunlog first';
        when too_many_rows then
            raise exception 'Too many entries in batchrun_jobrunlog';
    end;

    -- Make sure that the log row is not yet populated
    begin
        select id into strict existing_log_id
        from batchrun_jobrunlog
        where run_id=log_run_id
            and entry_data is null
            and content = '';
    exception
        when no_data_found then
            raise exception 'Entry in batchrun_jobrunlog is not empty';
    end;

    -- Construct metadata rows
    -- raise notice 'Create md_rows';
    create temporary table md_rows (
        "time" timestamp with time zone,
        "id" integer,
        "delta" bigint,
        "kind" integer,
        "len" integer) on commit drop;
    insert into md_rows
        select
            time,
            id,
            coalesce((extract(epoch from time - p_time) * 1000000)::bigint, 0),
            kind,
            len
        from (
            select
                time,
                id,
                lag(time) over (order by time, id) as p_time,
                kind,
                length(text) as len
            from batchrun_jobrunlogentry
            where run_id=log_run_id
            order by time, id) as subqry
        order by time, id;

    select min(time) into start_timestamp from md_rows;

    -- Create entry_data key-value pairs
    -- raise notice 'Generate entry_data';
    create temporary table entry_data (
        "k" varchar(5),
        "v" json) on commit drop;
    insert into entry_data values ('v', to_json(1));
    insert into entry_data values ('p', to_json(1));
    insert into entry_data values ('s', (select to_json(start_timestamp)));
    insert into entry_data values ('d', (
        select json_build_array(
                json_agg("delta" order by time, id),
                json_agg("kind" order by time, id),
                json_agg("len" order by time, id))
        from md_rows));

    -- Update the log table row:
    --  * Concatenate content from the log entry text fields
    --  * Store the computed entry_data JSON
    --  * Update start/end datetime and entry/error count fields
    -- raise notice 'Store results to the log row';
    update batchrun_jobrunlog set
    "content"=(
        select string_agg(text, '' order by time, id)
        from batchrun_jobrunlogentry where run_id=log_run_id),
    "entry_data"=(select json_object_agg(k, v) from entry_data),
    "start"=start_timestamp,
    "end"=(select max(time) from md_rows),
    "entry_count"=(select count(*) from md_rows),
    "error_count"=(select count(*) from md_rows where kind=2)
    where run_id=log_run_id;
end;
$$;
