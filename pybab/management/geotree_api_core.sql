------------------
-- PREREQUSITES --
------------------
/*CREATE EXTENSION IF NOT EXISTS tablefunc;
DROP AGGREGATE IF EXISTS _gt_rec_to_array(anyelement) CASCADE;
CREATE AGGREGATE _gt_rec_to_array(anyelement)
(
	sfunc = array_append,
	stype = anyarray,
	initcond = '{}'
);*/

DROP FUNCTION IF EXISTS _gt_validate_where (text) CASCADE;
CREATE OR REPLACE FUNCTION _gt_validate_where (where_clause text)
RETURNS text AS
$BODY$
DECLARE
	word text;
BEGIN
	FOR word IN SELECT foo FROM regexp_split_to_table(upper(where_clause), E'\\s+') AS foo
	LOOP
		IF (position(';' in word) + position('--' in word) + position('/*' in word) > 0)
		THEN
			RAISE EXCEPTION 'Cannot use semicolon in where clause.';
		END IF;

		CASE word WHEN 'SELECT','INSERT','UPDATE','DELETE','CREATE','TRUNCATE','DELETE','DROP',
			'JOIN','WHERE','CREATE','HAVING','WINDOW','BY','LIMIT','OFFSET','FETCH','FOR','UNION'
			THEN RAISE EXCEPTION 'Reserved word found, cannot continue.';
			ELSE NULL;
		END CASE;
	END LOOP;

	RETURN where_clause;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION _gt_validate_where (text)
	IS 'Checks for possible sql injections in a WHERE clause. Only simple clauses pass this control';

----------------------
-- IMPORT FUNCTIONS --
----------------------

-- IMPORT ELEMENTS FROM LAYER
DROP FUNCTION IF EXISTS gt_layer_import(integer,name,name,double precision) CASCADE;
CREATE OR REPLACE FUNCTION gt_layer_import
	(layerid integer, name_column name, parent_column name, rank double precision,
	OUT total_elements bigint, OUT new_elements bigint, OUT notnew_elements bigint, OUT invalid_parent_elements bigint) AS
$BODY$
DECLARE
	elcode varchar(255);
	elname varchar(255);
	elparent varchar(255);
	layer gt_catalog_layer%rowtype;
	elementid bigint;
	parentid bigint;
BEGIN	
	--recupero l'id del layer, se non esiste lo creo
	SELECT * INTO layer FROM gt_catalog_layer WHERE gt_catalog_layer.id = layerid;
	IF NOT FOUND THEN
		RAISE EXCEPTION 'Layer not found!';
	END IF;

	total_elements := 0; --Elementi totali
	notnew_elements := 0; --Nuovi elementi inseriti
	invalid_parent_elements := 0; --Elementi già presenti nell'albero
	new_elements := 0; --Elementi con padre non valido

	--ciclo su tutti i nuovi elementi
	FOR elcode,elname,elparent IN EXECUTE ('SELECT DISTINCT ON ('|| quote_ident(layer.tablename) ||'.'
		|| quote_ident(layer.code_column) ||')'
		|| quote_ident(layer.tablename) ||'.'|| quote_ident(layer.code_column) ||','
		|| quote_ident(layer.tablename) ||'.'|| quote_ident(name_column) ||','
		|| quote_ident(layer.tablename) ||'.'|| quote_ident(parent_column) ||' FROM '
		|| quote_ident(layer.tableschema) ||'.'|| quote_ident(layer.tablename))
	LOOP
		total_elements := total_elements + 1;

		--recupero l'id dell'elemento, se non esiste lo creo
		SELECT id INTO elementid FROM gt_element WHERE gt_element.code = elcode;
		IF FOUND THEN
			notnew_elements := notnew_elements + 1;
		ELSE
			INSERT INTO gt_element VALUES (DEFAULT,elname,elcode,rank) RETURNING id INTO elementid;
			new_elements := new_elements + 1;
		END IF;

		--cerco l'elemento padre, se esiste creo il link al padre
		SELECT INTO parentid id FROM gt_element WHERE gt_element.code = elparent;
		IF FOUND THEN
			BEGIN
				INSERT INTO gt_tree VALUES (DEFAULT,elementid,parentid);
			EXCEPTION WHEN unique_violation THEN END;
		ELSE
			invalid_parent_elements := invalid_parent_elements + 1;
		END IF;

		--collego l'elemento al layer
		BEGIN
			INSERT INTO gt_element_catalog_link VALUES (DEFAULT,elementid,layerid);
		EXCEPTION WHEN unique_violation THEN END;
	END LOOP;

	RETURN;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_layer_import(integer,name,name,double precision)
	IS 'TODO';

/*
insert into gt_catalog_layer (name,tableschema,tablename,code_column,geom_column,gs_name,gs_url)
values
('Provincia','administrative','ammprv','code','the_geom','localhost','localhost'),
('Comunità di Valle','administrative','ammcva','code','the_geom','localhost','localhost'),
('Comprensorio','administrative','ammcmp','code','the_geom','localhost','localhost'),
('Comune','administrative','ammcom_cmp_cva_isole','code','the_geom','localhost','localhost')
returning id,name;

select * from gt_layer_import(1,'desc','parent',5.0);
select * from gt_layer_import(2,'desc_','parent',6.0);
select * from gt_layer_import(3,'desc','parent',6.0);
select * from gt_layer_import(4,'DESC','CVA',7.0);
select * from gt_layer_import(4,'DESC','COMP',7.0);
*/


------------------
-- GETTERS      --
------------------

-- GET ELEMENTS BY LABEL
DROP FUNCTION IF EXISTS gt_elements_by_label (varchar) CASCADE;
CREATE OR REPLACE FUNCTION gt_elements_by_label (label_name varchar(255))
RETURNS TABLE (code varchar(255), name varchar(255), rank double precision) AS
$BODY$
	SELECT gt_element.code,gt_element.name,gt_element.rank
		FROM gt_element,gt_label,gt_attribute
		WHERE gt_label.name = $1
			AND gt_attribute.gt_label_id = gt_label.id
			AND gt_attribute.gt_element_id = gt_element.id
		ORDER BY code;
$BODY$
LANGUAGE sql;
COMMENT ON FUNCTION gt_elements_by_label (varchar)
	IS 'TODO';

-- GET ELEMENTS THAT MATCH AT LEAST ONE LABEL
DROP FUNCTION IF EXISTS gt_elements_by_labels (varchar[]) CASCADE;
CREATE OR REPLACE FUNCTION gt_elements_by_labels (label_names varchar(255)[])
RETURNS TABLE (code varchar(255), name varchar(255), rank double precision, labels varchar(255)[]) AS
$BODY$
	SELECT gt_element.code,gt_element.name,gt_element.rank,array_agg(gt_label.name)
		FROM gt_element,gt_label,gt_attribute
		WHERE gt_label.name IN (SELECT x FROM unnest($1) AS x)
			AND gt_attribute.gt_label_id = gt_label.id
			AND gt_attribute.gt_element_id = gt_element.id
		GROUP BY gt_element.code,gt_element.name,gt_element.rank
		ORDER BY gt_element.code;
$BODY$
LANGUAGE sql;
COMMENT ON FUNCTION gt_elements_by_labels (varchar[])
	IS 'TODO';

-- GET ELEMENTS THAT MATCH ALL LABELS
DROP FUNCTION IF EXISTS gt_elements_by_labels_strict (varchar[]) CASCADE;
CREATE OR REPLACE FUNCTION gt_elements_by_labels_strict (label_names varchar(255)[])
RETURNS TABLE (code varchar(255), name varchar(255), rank double precision) AS
$BODY$
	SELECT gt_element.code,gt_element.name,gt_element.rank
		FROM (SELECT gt_attribute.gt_element_id,array_agg(gt_label.name) as arr
			FROM gt_attribute,gt_label
			WHERE gt_attribute.gt_label_id = gt_label.id
			GROUP BY gt_attribute.gt_element_id)
		AS c, gt_element
		WHERE c.arr @> $1::varchar[]
			AND gt_element.id = c.gt_element_id
		ORDER BY gt_element.code;
$BODY$
LANGUAGE sql;
COMMENT ON FUNCTION gt_elements_by_labels_strict (varchar[])
	IS 'TODO';


--------------------------
--- LABELING FUNCTIONS ---
--------------------------

-- ADD LABEL TO ELEMENT(S) (with timestamps)
DROP FUNCTION IF EXISTS gt_elements_add_label
	(varchar[],varchar,timestamp(0) without time zone,timestamp(0) without time zone) CASCADE;
CREATE OR REPLACE FUNCTION gt_elements_add_label (elements varchar(255)[], label_name varchar(255),
	time_start timestamp(0) without time zone, time_end timestamp(0) without time zone,
	OUT input_elements bigint, OUT elements_found bigint, OUT elements_changed bigint, OUT new_label boolean) AS
$BODY$
DECLARE
	element varchar(255);
	labelid bigint;
	elementid bigint;
	attr gt_attribute%ROWTYPE;
BEGIN
	input_elements := 0;
	elements_found := 0;
	elements_changed := 0;
	new_label := false;

	--recupero l'id della label, se non esiste la creo
	SELECT id INTO labelid FROM gt_label WHERE gt_label.name = label_name;
	IF NOT FOUND THEN
		INSERT INTO gt_label VALUES (DEFAULT, label_name) RETURNING id INTO labelid;
		new_label := true;
	END IF;

	--aggiungo l'attributo agli elementi
	FOREACH element IN ARRAY elements LOOP
		input_elements := input_elements + 1;
		SELECT id INTO elementid FROM gt_element WHERE gt_element.code = element;
		IF FOUND THEN
			elements_found := elements_found + 1;
			BEGIN
				INSERT INTO gt_attribute VALUES (DEFAULT,elementid,labelid,time_start,time_end);
				elements_changed := elements_changed + 1;
			EXCEPTION WHEN unique_violation THEN
				SELECT INTO attr * FROM gt_attribute
					WHERE gt_element_id = elementid AND gt_label_id = labelid;
				IF (attr.timestart != time_start OR attr.timend != time_end) THEN
					UPDATE gt_attribute SET (timestart,timeend) = (time_start,time_end)
						WHERE gt_attribute.id = attr.id;
				END IF;
			END;
		END IF;
	END LOOP;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_elements_add_label
	(varchar[],varchar,timestamp(0) without time zone,timestamp(0) without time zone)
	IS 'TODO';

-- ADD LABEL TO ELEMENT(S)
DROP FUNCTION IF EXISTS gt_elements_add_label (varchar[],varchar) CASCADE;
CREATE OR REPLACE FUNCTION gt_elements_add_label (elements varchar(255)[], label_name varchar(255),
OUT input_elements bigint, OUT elements_found bigint, OUT elements_changed bigint, OUT new_label boolean) AS
$BODY$
BEGIN
	SELECT INTO input_elements,elements_found,elements_changed,new_label * FROM
		gt_elements_add_label(elements,label_name, 
		CURRENT_TIMESTAMP::timestamp(0) without time zone,'infinity'::timestamp(0) without time zone);
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_elements_add_label (varchar[],varchar)
	IS 'TODO';

-- REMOVE LABEL FROM ELEMENT(S)
DROP FUNCTION IF EXISTS gt_elements_remove_label (varchar[],varchar) CASCADE;
CREATE OR REPLACE FUNCTION gt_elements_remove_label (elements varchar(255)[], label_name varchar(255),
OUT elements_changed bigint) AS
$BODY$
DECLARE
	element varchar(255);
	labelid bigint;
BEGIN
	elements_changed := 0;

	--recupero l'id della label, errore se non esiste
	SELECT id INTO labelid FROM gt_label WHERE gt_label.name = label_name;
	IF NOT FOUND THEN
		RAISE NOTICE '$$label_not_found$$: %',label_name;
		RETURN;
	END IF;

	--rimuovo l'attributo dagli elementi
	DELETE FROM gt_attribute WHERE gt_label_id = labelid AND gt_element_id IN
		(SELECT id FROM gt_element WHERE code IN (SELECT x FROM unnest(elements) AS x));
	GET DIAGNOSTICS elements_changed = ROW_COUNT;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_elements_remove_label (varchar[],varchar)
	IS 'TODO';


--------------------------------------------
--- RETRIEVE DATA FROM CATALOG FUNCTIONS ---
--------------------------------------------

--- BUILDS TEXT QUERY FOR gt_elements_by_catalog 
DROP FUNCTION IF EXISTS _gt_elements_by_catalog (bigint,name[],text) CASCADE;
CREATE OR REPLACE FUNCTION _gt_elements_by_catalog (catalog_id bigint,extra_columns name[],where_clause text)
RETURNS text AS
$BODY$
DECLARE
	clog gt_catalog%rowtype;
	query_text text;
BEGIN
	SELECT INTO clog * FROM gt_catalog WHERE gt_catalog.id = $1;
	IF NOT FOUND THEN
		RAISE EXCEPTION 'Catalog not found!';
	END IF;

	query_text := 'SELECT gt_element.id,gt_element.code,gt_element.name,gt_element.rank';

	IF array_length(extra_columns, 1) > 0 THEN
		query_text := query_text||','||quote_ident(clog.tablename)||'.'||
			array_to_string(extra_columns,','||quote_ident(clog.tablename)||'.','*')||'';
	END IF;

	query_text := query_text||'
		FROM gt_element,gt_catalog,gt_element_catalog_link,
			'||quote_ident(clog.tableschema)||'.'||quote_ident(clog.tablename)||'
		WHERE gt_catalog.id = '||$1||'
			AND gt_element_catalog_link.gt_catalog_id = gt_catalog.id
			AND gt_element_catalog_link.gt_element_id = gt_element.id
			AND '||quote_ident(clog.tablename)||'."'||quote_ident(clog.code_column)||'" = gt_element.code';
	
	IF char_length(where_clause) > 0 THEN
		query_text := query_text||' AND '|| _gt_validate_where(where_clause);
	END IF;

	query_text := query_text||'
		ORDER BY gt_element.code';

	RETURN query_text;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION _gt_elements_by_catalog (bigint,name[],text)
	IS 'TODO';

--- BUILDS TEXT QUERY FOR gt_elements_by_catalog 
DROP FUNCTION IF EXISTS _gt_elements_by_catalog (bigint,name[],text,text,text) CASCADE;
CREATE OR REPLACE FUNCTION _gt_elements_by_catalog
	(catalog_id bigint,extra_columns name[],where_clause text,pre_wrap text,post_wrap text)
RETURNS text AS
$BODY$
DECLARE
	query_text text;
BEGIN
	query_text := _gt_elements_by_catalog(catalog_id,extra_columns,where_clause);

	IF char_length(pre_wrap) > 0 AND char_length(post_wrap) > 0 THEN
		query_text := pre_wrap || query_text || post_wrap;
	END IF;

	RAISE NOTICE '%',query_text;
	RETURN query_text;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION _gt_elements_by_catalog (bigint,name[],text,text,text)
	IS 'TODO';

--- GET ELEMENTS BY CATALOG WITH OPTIONAL DATA FROM COLUMNS 
DROP FUNCTION IF EXISTS gt_elements_by_catalog (refcursor,bigint,name[],text,text,text) CASCADE;
CREATE OR REPLACE FUNCTION gt_elements_by_catalog
	(curs refcursor,catalog_id bigint,extra_columns name[],where_clause text,pre_wrap text,post_wrap text)
RETURNS refcursor AS
$BODY$
BEGIN
	OPEN curs FOR EXECUTE _gt_elements_by_catalog(catalog_id,extra_columns,where_clause,pre_wrap,post_wrap);
	RETURN curs;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_elements_by_catalog (refcursor,bigint,name[],text,text,text)
	IS 'TODO';

/*
SELECT * FROM gt_cur_to_set(gt_elements_by_catalog('c',5,ARRAY['AREA','PERIMETER'],'"PERIMETER" > 80000',NULL,NULL))
AS (code varchar,name varchar,rank double precision,area double precision,perimeter double precision);

SELECT * FROM gt_elements_by_catalog('a',5,ARRAY[NULL]::varchar[],NULL,NULL,NULL);
FETCH ALL IN a;

SELECT * FROM gt_elements_by_catalog('b',5,ARRAY['"AREA"','"PERIMETER"'],'"PERIMETER" > 80000',NULL,NULL);
FETCH ALL IN b;

SELECT * FROM gt_select('c',_gt_elements_by_catalog (5,ARRAY['"AREA"','"PERIMETER"'],'"PERIMETER" > 80000',NULL,NULL));
FETCH ALL IN c;*/


-----------------------------
--- AGGREGATION FUNCTIONS ---
-----------------------------

-- private func --
DROP FUNCTION IF EXISTS _gt_find_subtree (bigint) CASCADE;
CREATE OR REPLACE FUNCTION _gt_find_subtree (id bigint)
RETURNS TABLE (id bigint) AS
$BODY$
	WITH RECURSIVE subtree(elem) AS (
		(SELECT $1::BIGINT)
		UNION
		(SELECT gt_element_id
		 FROM gt_tree, subtree WHERE gt_tree.gt_parent_id = subtree.elem)
	)
	SELECT elem FROM subtree WHERE elem <> $1
$BODY$
LANGUAGE sql;
COMMENT ON FUNCTION _gt_find_subtree (bigint) IS 'TODO';

DROP FUNCTION IF EXISTS gt_aggregate (varchar[],varchar[],bigint,text) CASCADE;
CREATE OR REPLACE FUNCTION gt_aggregate (from_elements varchar[],to_elements varchar[],gt_catalog_id bigint,where_clause text)
RETURNS TABLE (code varchar(255), name varchar(255), vals double precision[], elems varchar[]) AS
$BODY$
DECLARE
	reln name;
	query text;
BEGIN
	SELECT INTO reln p.relname FROM pg_class p, gt_catalog c
	WHERE c.tableoid = p.oid AND c.id = gt_catalog_id;
	IF NOT FOUND THEN
		RAISE WARNING 'Nothing found';
		RETURN;
	ELSIF (reln = 'gt_catalog_layer') THEN
		RAISE WARNING 'Do You Think You''re Funny?! You''re NOT supposed to do this.';
	END IF;

	
	
	WITH elem_val AS (
	select gt_element.id,gt_element.code,sum(ammcom_cmp_cva_isole."AREA")::double precision as val
	from gt_element,gt_element_catalog_link,administrative.ammcom_cmp_cva_isole
	WHERE gt_element.code IN (SELECT x FROM unnest(ARRAY['istat022001',
	'istat022007',
	'istat022013',
	'istat022025'
	]) AS x)
	AND gt_element_catalog_link.gt_catalog_id = 4
	AND gt_element.id = gt_element_catalog_link.gt_element_id
	AND gt_element.code = ammcom_cmp_cva_isole.code
	group by gt_element.id), 

	roots AS (
	select gt_element.id,gt_element.code
	from gt_element
	WHERE gt_element.code IN (SELECT x FROM unnest(ARRAY['cva10','cva11']) AS x)),

	descendents AS (
	SELECT roots.code as ancestor, _gt_find_subtree(roots.id) as id FROM roots
	)

	SELECT descendents.ancestor AS from_el, elem_val.code AS to_el, elem_val.val AS val
	FROM roots,elem_val,descendents
	WHERE roots.code=descendents.ancestor AND descendents.id = elem_val.id

	
	--RETURN QUERY SELECT * FROM gt_to_element;
END	
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_aggregate (varchar[],varchar[],bigint)
	IS 'TODO';

select sum(area) from administrative.ammprv
select code,sum("AREA") as area from administrative.ammcom_cmp_cva_isole group by code


/*WITH base_query AS (
	select gt_element.code
	from gt_element,gt_element_catalog_link
	WHERE gt_element.code IN (SELECT x FROM unnest(ARRAY['istat022001',
	'istat022007',
	'istat022013',
	'istat022025'
	]) AS x)
	AND gt_element_catalog_link.gt_catalog_id = 4
	AND gt_element.id = gt_element_catalog_link.gt_element_id
)
SELECT base_query.code, sum(ammcom_cmp_cva_isole."AREA")::double precision as val
FROM base_query, administrative.ammcom_cmp_cva_isole
WHERE base_query.code = ammcom_cmp_cva_isole.code
GROUP BY base_query.code;*/

WITH elem_val AS (

select gt_element.id,sum(ammcom_cmp_cva_isole."AREA")::double precision as val
from gt_element,gt_element_catalog_link,administrative.ammcom_cmp_cva_isole
WHERE gt_element.code IN (SELECT x FROM unnest(ARRAY['istat022001',
'istat022007',
'istat022013',
'istat022025'
]) AS x)
AND gt_element_catalog_link.gt_catalog_id = 4
AND gt_element.id = gt_element_catalog_link.gt_element_id
AND gt_element.code = ammcom_cmp_cva_isole.code
group by gt_element.id

), 
roots AS (

select gt_element.id
from gt_element
WHERE gt_element.code IN (SELECT x FROM unnest(ARRAY['cva10','cva11']) AS x)

)

SELECT descendents.ancestor_id AS from_el, descendents.id AS to_, elem_val.val AS val
FROM roots,elem_val,(SELECT roots2.id as ancestor_id, _gt_find_subtree(roots2.id) as id FROM roots roots2) AS descendents
WHERE roots.id=descendents.ancestor_id AND descendents.id = elem_val.id --join



WITH elem_val AS (
select gt_element.id,gt_element.code,sum(ammcom_cmp_cva_isole."AREA")::double precision as val
from gt_element,gt_element_catalog_link,administrative.ammcom_cmp_cva_isole
WHERE gt_element.code IN (SELECT x FROM unnest(ARRAY['istat022001',
'istat022007',
'istat022013',
'istat022025'
]) AS x)
AND gt_element_catalog_link.gt_catalog_id = 4
AND gt_element.id = gt_element_catalog_link.gt_element_id
AND gt_element.code = ammcom_cmp_cva_isole.code
group by gt_element.id), 

roots AS (
select gt_element.id,gt_element.code
from gt_element
WHERE gt_element.code IN (SELECT x FROM unnest(ARRAY['cva10','cva11']) AS x)),

descendents AS (
SELECT roots.code as ancestor, _gt_find_subtree(roots.id) as id FROM roots
)

SELECT descendents.ancestor AS from_el, elem_val.code AS to_el, elem_val.val AS val
FROM roots,elem_val,descendents
WHERE roots.code=descendents.ancestor AND descendents.id = elem_val.id




CREATE OR REPLACE FUNCTION gt_try (els varchar[])
RETURNS TABLE (id bigint) AS
$BODY$
BEGIN
return query execute 'select gt_element.id
from gt_element
WHERE gt_element.code IN (SELECT x FROM unnest($1) AS x)' using els;
END	
$BODY$
LANGUAGE plpgsql;
select * from gt_try(ARRAY['cva10','cva11']);

SELECT gt_element.id,sum(ammcom_cmp_cva_isole."AREA")::double precision as val
FROM gt_element,gt_element_catalog_link,administrative.ammcom_cmp_cva_isole
WHERE gt_element.code IN (SELECT x FROM unnest(from_elements) AS x)
AND gt_element.id IN ()

DROP FUNCTION IF EXISTS gt_raise_error (text) CASCADE;
CREATE OR REPLACE FUNCTION gt_raise_error (t text)
RETURNS VOID AS
$BODY$
BEGIN
	RAISE EXCEPTION t;
END
$BODY$
LANGUAGE plpgsql;

/*drop view incidenza_view;
create view incidenza_view as
select anagrafica.indirizzo,anagrafica.civico,anagrafica.cap,anagrafica.comune,incidenza.*
from incidenza,anagrafica
where incidenza.anagrafica_id = anagrafica.id
order by incidenza.id;

select _gt_find_subtree(3)

select array(select a.id from (SELECT id FROM _gt_find_subtree(3)) AS a,unnest(ARRAY[29,35,39,51]) as b where a.id = b);


select * from gt_elements_by_parent('cva10')
select * from gt_parents_by_element('istat022100')

SELECT id FROM gt_element WHERE code = 'cva10'

select gt_aggregate(ARRAY['istat022001',
'istat022007',
'istat022013',
'istat022025'
],ARRAY['cva10'],4)*/
