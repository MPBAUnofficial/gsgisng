CREATE EXTENSION IF NOT EXISTS fuzzystrmatch;

DROP FUNCTION IF EXISTS fuzzysearch(name,name,text,integer);
CREATE OR REPLACE FUNCTION fuzzysearch(tablename name, colname name, keyword text, max_dist integer)
RETURNS TABLE (val text, dist integer) AS
$BODY$
BEGIN
	RETURN QUERY EXECUTE 'select * from (
	    select '||quote_ident(tablename)||'.'||quote_ident(colname)||'::text as val,
	    levenshtein(upper('||quote_literal(keyword)||'), upper('||quote_ident(colname)||')) as dist
	    from '||quote_ident(tablename)||'
	    order by dist
	) as x where x.dist <= '||max_dist;
END
$BODY$
LANGUAGE plpgsql;