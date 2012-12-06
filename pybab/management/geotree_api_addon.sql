------------------
--- GETTERS    ---
------------------
-- GET ELEMENTS BY PARENT NAME 
DROP FUNCTION IF EXISTS gt_elements_by_parent (varchar) CASCADE;
CREATE OR REPLACE FUNCTION gt_elements_by_parent (parent_name varchar(255))
RETURNS TABLE (code varchar(255), name varchar(255), rank double precision) AS
$BODY$
	SELECT el.code,el.name,el.rank
		FROM gt_element el, gt_tree tr, gt_element parent
		WHERE parent.code = $1
			AND tr.gt_parent_id = parent.id
			AND tr.gt_element_id = el.id
		ORDER BY code;
$BODY$
LANGUAGE sql;
COMMENT ON FUNCTION gt_elements_by_parent (varchar)
	IS 'TODO';

-- GET PARENTS BY ELEMENT NAME 
DROP FUNCTION IF EXISTS gt_parents_by_element (varchar) CASCADE;
CREATE OR REPLACE FUNCTION gt_parents_by_element (parent_name varchar(255))
RETURNS TABLE (code varchar(255), name varchar(255), rank double precision) AS
$BODY$
	SELECT  parent.code, parent.name, parent.rank
		FROM gt_element el, gt_tree tr, gt_element parent
		WHERE el.code = $1
			AND tr.gt_parent_id = parent.id
			AND tr.gt_element_id = el.id
		ORDER BY code;
$BODY$
LANGUAGE sql;
COMMENT ON FUNCTION gt_parents_by_element (varchar)
	IS 'TODO';

--- GET ELEMENTS BY LAYER (with geometries)
DROP FUNCTION IF EXISTS gt_elements_by_layer (bigint,boolean) CASCADE;
CREATE OR REPLACE FUNCTION gt_elements_by_layer (layerid bigint, explode_geom boolean)
RETURNS TABLE (code varchar(255), name varchar(255), rank double precision, the_geom geometry) AS
$BODY$
DECLARE
	layer gt_catalog_layer%rowtype;
	query_text text;
BEGIN
	SELECT INTO layer * FROM gt_catalog_layer WHERE gt_catalog_layer.id = $1;
	IF NOT FOUND THEN
		RETURN;
	END IF;

	IF explode_geom THEN
		query_text := '
		SELECT gt_element.code,gt_element.name,gt_element.rank,
			'||quote_ident(layer.tablename)||'.'||quote_ident(layer.geom_column)||'
		FROM gt_element,gt_catalog_layer,gt_element_catalog_link,
			'||quote_ident(layer.tableschema)||'.'||quote_ident(layer.tablename)||'
		WHERE gt_catalog_layer.id = '||$1||'
			AND gt_element_catalog_link.gt_catalog_id = gt_catalog_layer.id
			AND gt_element_catalog_link.gt_element_id = gt_element.id
			AND '||quote_ident(layer.tablename)||'.'||quote_ident(layer.code_column)||' = gt_element.code
		ORDER BY gt_element.code';
	ELSE
		query_text :=  '
		SELECT gt_element.code,gt_element.name,gt_element.rank,
			ST_Collect('||quote_ident(layer.tablename)||'.'||quote_ident(layer.geom_column)||')
		FROM gt_element,gt_catalog_layer,gt_element_catalog_link,
			'||quote_ident(layer.tableschema)||'.'||quote_ident(layer.tablename)||'
		WHERE gt_catalog_layer.id = '||$1||'
			AND gt_element_catalog_link.gt_catalog_id = gt_catalog_layer.id
			AND gt_element_catalog_link.gt_element_id = gt_element.id
			AND '||quote_ident(layer.tablename)||'.'||quote_ident(layer.code_column)||' = gt_element.code
		GROUP BY gt_element.code,gt_element.name,gt_element.rank
		ORDER BY gt_element.code';
	END IF;

	RETURN QUERY EXECUTE query_text;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_elements_by_layer (bigint,boolean)
	IS 'TODO';

--- GET ELEMENTS BY LAYER (without geometries)
DROP FUNCTION IF EXISTS gt_elements_by_layer_nogeom (bigint) CASCADE;
CREATE OR REPLACE FUNCTION gt_elements_by_layer_nogeom (layerid bigint)
RETURNS TABLE (code varchar(255), name varchar(255), rank double precision) AS
$BODY$
DECLARE
	layer gt_catalog_layer%rowtype;
	query_text text;
BEGIN
	SELECT INTO layer * FROM gt_catalog_layer WHERE gt_catalog_layer.id = $1;
	IF NOT FOUND THEN
		RETURN;
	END IF;

	RETURN QUERY EXECUTE 
	'SELECT DISTINCT gt_element.code,gt_element.name,gt_element.rank
	FROM gt_element,gt_catalog_layer,gt_element_catalog_link,
		'||quote_ident(layer.tableschema)||'.'||quote_ident(layer.tablename)||'
	WHERE gt_catalog_layer.id = '||$1||'
		AND gt_element_catalog_link.gt_catalog_id = gt_catalog_layer.id
		AND gt_element_catalog_link.gt_element_id = gt_element.id
		AND '||quote_ident(layer.tablename)||'.'||quote_ident(layer.code_column)||' = gt_element.code
	ORDER BY gt_element.code';
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_elements_by_layer_nogeom (bigint)
	IS 'TODO';

--- GET ELEMENTS BY LAYER WITH LAYER ATTRIBUTES FILTERED BY WHERE CLAUSE (with exploded geometries)
DROP FUNCTION IF EXISTS gt_elements_by_layer_with_attirbutes (bigint,name[],text) CASCADE;
CREATE OR REPLACE FUNCTION gt_elements_by_layer_with_attirbutes (layerid bigint,columns_list name[],where_clause text)
RETURNS TABLE (code varchar(255), name varchar(255), rank double precision, geom geometry, fields character varying[]) AS
$BODY$
DECLARE
	layer gt_catalog_layer%rowtype;
	query_text text;
BEGIN
	SELECT INTO layer * FROM gt_catalog_layer WHERE gt_catalog_layer.id = $1;
	IF NOT FOUND THEN
		RETURN;
	END IF;

	query_text := 'SELECT gt_element.code,gt_element.name,gt_element.rank,
			'||quote_ident(layer.tablename)||'.'||quote_ident(layer.geom_column)||'';

	IF array_length(columns_list, 1) > 0 THEN
		query_text := query_text||',ARRAY['||quote_ident(layer.tablename)||'."'||
			array_to_string(columns_list,'"::varchar,'||quote_ident(layer.tablename)||'."','*')||'"::varchar]';
	ELSE
		query_text := query_text||',ARRAY[''''::varchar]';
	END IF;

	query_text := query_text||'
		FROM gt_element,gt_catalog_layer,gt_element_catalog_link,
			'||quote_ident(layer.tableschema)||'.'||quote_ident(layer.tablename)||'
		WHERE gt_catalog_layer.id = '||$1||'
			AND gt_element_catalog_link.gt_catalog_id = gt_catalog_layer.id
			AND gt_element_catalog_link.gt_element_id = gt_element.id
			AND '||quote_ident(layer.tablename)||'.'||quote_ident(layer.code_column)||' = gt_element.code';
	
	IF char_length(where_clause) > 0 THEN
		query_text := query_text ||' AND '|| _gt_validate_where(where_clause);
	END IF;

	query_text := query_text||'
		ORDER BY gt_element.code';

	raise notice '%',query_text;

	RETURN QUERY EXECUTE query_text;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_elements_by_layer_with_attirbutes (bigint,name[],text)
	IS 'TODO';


/*SELECT * FROM gt_elements_by_layer_with_attirbutes(5,ARRAY['AREA','PERIMETER'],'"PERIMETER" > 80000');

SELECT * FROM gt_elements_by_layer_with_attirbutes(1,NULL,NULL);

SELECT * FROM gt_elements_by_layer(1,false);

SELECT * FROM gt_elements_by_layer_nogeom(5);

select * FROM gt_layer_import('ammcva','administrative','ammcva','the_geom','code','desc_','prov',5.0);
select * FROM gt_layer_import('administrative','ammcom_cmp_cva_isole','the_geom','code','DESC','CVA',7.0);*/

