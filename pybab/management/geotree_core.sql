------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------
				-- CORE TABLES AND TRIGGERS --
------------------------------------------------------------------------------------------
------------------------------------------------------------------------------------------


------------------------------------------------------------------------------------------
-- PREREQUSITES (USEFUL FUNCS)
------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS gt_perform (query text) CASCADE;
CREATE OR REPLACE FUNCTION gt_perform (query text)
RETURNS VOID AS
$BODY$
BEGIN
	EXECUTE query;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_perform (text)
	IS 'Performs a query';

DROP FUNCTION IF EXISTS gt_select (text) CASCADE;
CREATE OR REPLACE FUNCTION gt_select (query_text text)
RETURNS SETOF record AS
$BODY$
BEGIN
	RETURN QUERY EXECUTE query_text;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_select (text)
	IS 'Executes a select (returns a recordset)';

DROP FUNCTION IF EXISTS gt_cursor (refcursor,text) CASCADE;
CREATE OR REPLACE FUNCTION gt_cursor (curs refcursor,query text)
RETURNS refcursor AS
$BODY$
BEGIN
	OPEN curs FOR EXECUTE query;
	RETURN curs;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_cursor (refcursor,text)
	IS 'Opens and retuns a cursor for input query';

DROP FUNCTION IF EXISTS gt_cur_to_set (refcursor) CASCADE;
CREATE OR REPLACE FUNCTION gt_cur_to_set (curs refcursor)
RETURNS SETOF record AS
$BODY$
DECLARE
	r record;
BEGIN
	LOOP
		FETCH curs INTO r;
		EXIT WHEN r IS NULL;
		RETURN NEXT r;
	END LOOP;
	CLOSE curs;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_cur_to_set (refcursor)
	IS 'Fetches an open cursor into a recordset';

--- LISTS COLUMNS IN A TABLE
DROP FUNCTION IF EXISTS gt_get_table_columns (name,name) CASCADE;
CREATE OR REPLACE FUNCTION gt_get_table_columns (tableschema name, tablename name)
RETURNS TABLE(column_name name, data_type varchar,is_nullable boolean) AS
$BODY$
DECLARE
	query_text text;
	udt_name varchar;
BEGIN
	query_text := 'SELECT column_name,data_type,is_nullable::boolean,udt_name
			FROM information_schema.columns
			WHERE table_schema = '||quote_literal($1)||' AND table_name = '||quote_literal($2)
			|| ' ORDER BY ordinal_position';

	FOR column_name,data_type,is_nullable,udt_name IN EXECUTE query_text
	LOOP
		IF data_type = 'USER-DEFINED' THEN
			data_type := udt_name;
		END IF;
		RETURN NEXT;
	END LOOP;

	IF NOT FOUND THEN
		RAISE EXCEPTION 'Table % not found in schema %',tablename,tableschema;
	END IF;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_get_table_columns (name,name)
	IS 'TODO';
------------------------------------------------------------------------------------------


------------------------------------------------------------------------------------------
-- LABEL
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_label CASCADE;
CREATE TABLE IF NOT EXISTS gt_label (
    id BIGSERIAL PRIMARY KEY,
    name character varying(255) NOT NULL UNIQUE
);
------------------------------------------------------------------------------------------


------------------------------------------------------------------------------------------
-- ELEMENT
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_element CASCADE;
CREATE TABLE IF NOT EXISTS gt_element (
    id BIGSERIAL PRIMARY KEY,
    name character varying(255) NOT NULL,
    code character varying(255) NOT NULL UNIQUE,
    rank double precision NOT NULL
);
INSERT INTO gt_element VALUES (-1,'fakeroot','fakeroot',0);
INSERT INTO gt_element VALUES (0,'root','root',0);

CREATE OR REPLACE FUNCTION gt_element_insert_update_check() RETURNS TRIGGER AS
$BODY$
DECLARE
	rank double precision;
	code varchar(255);
	name varchar(255);
BEGIN
	-- check NEW.rank
	IF (NEW.rank <= 0) THEN
		RAISE EXCEPTION 'gt_element: rank value must be higher than 0.';
	END IF;
	
	-- check rank consistency if updated
	IF (TG_OP = 'UPDATE') THEN
	
		-- prevent root modification
		IF (OLD.id = 0) THEN
			NEW.id := 0;
			NEW.name := 'root';
			NEW.code := 'root';
			NEW.rank := 0;
			RAISE NOTICE 'Cannot modify root element. Element ha been reset to default values.';
			RETURN NEW;
		END IF;

		-- prevent fakeroot modification
		IF (OLD.id = -1) THEN
			NEW.id := -1;
			NEW.name := 'fakeroot';
			NEW.code := 'fakeroot';
			NEW.rank := 0;
			RAISE NOTICE 'Cannot modify fakeroot element. Element ha been reset to default values.';
			RETURN NEW;
		END IF;

		-- check rank in parents
		FOR name,code,rank IN (SELECT gt_element.name,gt_element.code,gt_element.rank
			FROM gt_tree,gt_element
			WHERE gt_element_id = NEW.id AND gt_element.id = gt_tree.gt_parent_id)
		LOOP
			IF (NEW.rank <= rank) THEN
				RAISE EXCEPTION 'Cannot update row: parent ''%'' (%) has rank % <= new rank %!',
					name,code,rank,NEW.rank;
			END IF;
		END LOOP;

		-- check rank in children
		FOR name,code,rank IN (SELECT gt_element.name,gt_element.code,gt_element.rank
			FROM gt_tree,gt_element
			WHERE gt_parent_id = NEW.id AND gt_element.id = gt_tree.gt_element_id)
		LOOP
			IF (NEW.rank >= rank) THEN
				RAISE EXCEPTION 'Cannot update row: child ''%'' (%) has rank % >= new rank %!',
					name,code,rank,NEW.rank;
			END IF;
		END LOOP;

	END IF;
	RETURN NEW;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_element_insert_update_check()
	IS 'Makes sure, if rank changes, that the new rank is greater than its parents''
	and lower than its childrens'': in this case, a notice is raised and rank is unchanged
	(although other changes are applied).
	Also checks no new or updated element has rank 0 (reserved for root elements) or less:
	in this case, raises an exception';
DROP TRIGGER IF EXISTS gt_element_check ON gt_element CASCADE;
CREATE TRIGGER gt_element_check BEFORE INSERT OR UPDATE ON gt_element
	FOR EACH ROW EXECUTE PROCEDURE gt_element_insert_update_check();

CREATE OR REPLACE FUNCTION gt_element_after_insert_check() RETURNS TRIGGER AS
$BODY$
DECLARE
BEGIN
	PERFORM id FROM gt_tree WHERE gt_element_id = NEW.id;
	IF NOT FOUND THEN
		INSERT INTO gt_tree VALUES (default,NEW.id,-1);
	END IF;
	RETURN NEW;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_element_after_insert_check()
	IS 'Makes sure, for new elements, that the element has at least one (fake) parent in the tree';
DROP TRIGGER IF EXISTS gt_element_after_check ON gt_element CASCADE;
CREATE TRIGGER gt_element_after_check AFTER INSERT ON gt_element
	FOR EACH ROW EXECUTE PROCEDURE gt_element_after_insert_check();

CREATE OR REPLACE FUNCTION gt_element_before_delete_check() RETURNS TRIGGER AS
$BODY$
DECLARE
BEGIN
	-- prevent (fake)root deletion
	IF (OLD.rank = 0) THEN
		RAISE EXCEPTION 'Cannot delete root elements.';
	END IF;
	RETURN OLD;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_element_before_delete_check()
	IS 'Makes sure root elements are never deleted';
DROP TRIGGER IF EXISTS gt_element_delete_check ON gt_element CASCADE;
CREATE TRIGGER gt_element_delete_check BEFORE DELETE ON gt_element
	FOR EACH ROW EXECUTE PROCEDURE gt_element_before_delete_check();
------------------------------------------------------------------------------------------


------------------------------------------------------------------------------------------
-- TREE (ELEMENT <--> ELEMENT)
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_tree CASCADE;
CREATE TABLE IF NOT EXISTS gt_tree (
	id BIGSERIAL PRIMARY KEY,
	gt_element_id BIGINT NOT NULL REFERENCES gt_element(id) ON UPDATE CASCADE ON DELETE CASCADE,
	gt_parent_id BIGINT NOT NULL REFERENCES gt_element(id) ON UPDATE CASCADE ON DELETE CASCADE,
	UNIQUE (gt_element_id,gt_parent_id)
);

CREATE OR REPLACE FUNCTION gt_tree_after_delete_check() RETURNS TRIGGER AS
$BODY$
DECLARE
BEGIN
	PERFORM id FROM gt_tree WHERE gt_element_id = OLD.gt_element_id;
	IF NOT FOUND THEN
		BEGIN
			INSERT INTO gt_tree VALUES (default,OLD.gt_element_id,-1);
			RAISE NOTICE 'No parents found, fakeroot link created.';
		EXCEPTION WHEN foreign_key_violation THEN
			RAISE NOTICE 'Element has been deleted, fakeroot link not restored.';
		END;
	END IF;
	RETURN OLD;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_tree_after_delete_check()
	IS 'Sets fake parent if no more parents are present';
DROP TRIGGER IF EXISTS gt_tree_delete_check ON gt_tree CASCADE;
CREATE TRIGGER gt_tree_delete_check AFTER DELETE ON gt_tree
	FOR EACH ROW EXECUTE PROCEDURE gt_tree_after_delete_check();

CREATE OR REPLACE FUNCTION gt_tree_insert_update_check() RETURNS TRIGGER AS
$BODY$
DECLARE
	element gt_element%rowtype;
	parent gt_element%rowtype;
	num integer;
BEGIN
	SELECT INTO element * FROM gt_element WHERE id = NEW.gt_element_id;
	SELECT INTO parent * FROM gt_element WHERE id = NEW.gt_parent_id;
	IF (parent.rank >= element.rank) THEN
		RAISE EXCEPTION 'Parent element must have lower rank!';
	END IF;

	IF (TG_OP = 'UPDATE' AND NEW.gt_element_id != OLD.gt_element_id) THEN
		PERFORM id FROM gt_tree WHERE gt_element_id = OLD.gt_element_id;
		IF NOT FOUND THEN
			BEGIN
				INSERT INTO gt_tree VALUES (default,OLD.gt_element_id,-1);
				RAISE NOTICE 'No parents found, fakeroot link created.';
			EXCEPTION WHEN foreign_key_violation THEN
				RAISE NOTICE 'Element id changed, no need to recreate fakeroot link.';
			END;
		END IF;
	END IF;

	IF (TG_OP = 'INSERT') THEN
		SELECT INTO num count(id) as c FROM gt_tree WHERE gt_element_id = NEW.gt_element_id;
		IF (num > 1) THEN
			PERFORM id FROM gt_tree WHERE gt_element_id = NEW.gt_element_id AND gt_parent_id = -1;
			IF FOUND THEN
				DELETE FROM gt_tree WHERE gt_element_id = NEW.gt_element_id AND gt_parent_id = -1;
				RAISE NOTICE 'Fakeroot link removed. Current parents: %',num-1;
			END IF;
		ELSE
			RAISE NOTICE 'Current parents: %',num;
		END IF;
	END IF;
	
	RETURN NEW;
END
$BODY$
LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS gt_tree_check ON gt_tree CASCADE;
CREATE TRIGGER gt_tree_check AFTER INSERT OR UPDATE ON gt_tree
	FOR EACH ROW EXECUTE PROCEDURE gt_tree_insert_update_check();
------------------------------------------------------------------------------------------


------------------------------------------------------------------------------------------
-- ATTRIBUTE
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_attribute CASCADE;
CREATE TABLE IF NOT EXISTS gt_attribute (
	id BIGSERIAL PRIMARY KEY,
	gt_element_id BIGINT NOT NULL references gt_element(id) ON UPDATE CASCADE ON DELETE CASCADE,
	gt_label_id BIGINT NOT NULL references gt_label(id) ON UPDATE CASCADE ON DELETE CASCADE,
	timeStart timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP,
	timeEnd timestamp(0) NOT NULL DEFAULT 'infinity',
	CHECK (timeEnd > timeStart),
	UNIQUE (gt_element_id,gt_label_id)
);
------------------------------------------------------------------------------------------


------------------------------------------------------------------------------------------
-- CATALOG
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_catalog CASCADE;
CREATE TABLE IF NOT EXISTS gt_catalog (
	id BIGSERIAL NOT NULL PRIMARY KEY,
	name VARCHAR(255) NOT NULL,
	creation_time timestamp(0) NOT NULL DEFAULT CURRENT_TIMESTAMP,
	numcode INTEGER NOT NULL DEFAULT 0,
	remotehost varchar(255),
	remoteport integer CHECK (remoteport > 0 AND remoteport <= 65535),
	remotedb varchar(255),
	remoteuser varchar(255),
	remotepass varchar(255),
	tableschema name,
	tablename name,
	code_column name,
	time_column name,
	CONSTRAINT set_all_remote_fields CHECK
		(remotehost is null = remoteport is null AND remoteport is null = remotedb is null
		AND remotedb is null = remoteuser is null AND remoteuser is null = remotepass is null)
);

CREATE OR REPLACE FUNCTION gt_catalog_noedit() RETURNS TRIGGER AS
$BODY$
DECLARE
	reln name;
BEGIN
	SELECT INTO reln p.relname FROM pg_class p WHERE TG_RELID = p.oid;

	IF (reln = 'gt_catalog') THEN
		RAISE EXCEPTION 'Cannot insert or edit gt_catalog directly!';
	END IF;

	RETURN NEW;
END
$BODY$
LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS gt_catalog_noedit_check ON gt_catalog CASCADE;
CREATE TRIGGER gt_catalog_noedit_check BEFORE INSERT OR UPDATE OR DELETE ON gt_catalog
	EXECUTE PROCEDURE gt_catalog_noedit();
------------------------------------------------------------------------------------------


------------------------------------------------------------------------------------------
-- ELEMENT <--> CATALOG
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_element_catalog_link CASCADE;
CREATE TABLE IF NOT EXISTS gt_element_catalog_link (
	id BIGSERIAL PRIMARY KEY,
	gt_element_id BIGINT NOT NULL REFERENCES gt_element(id) ON UPDATE CASCADE ON DELETE CASCADE,
	gt_catalog_id BIGINT NOT NULL, --REFERENCES gt_catalog(id) ON UPDATE CASCADE ON DELETE CASCADE - Using Trigger fo this!
	UNIQUE (gt_element_id,gt_catalog_id)
);

CREATE OR REPLACE FUNCTION gt_element_catalog_insert_update_check() RETURNS TRIGGER AS
$BODY$
BEGIN
	PERFORM id FROM gt_catalog WHERE id = NEW.gt_catalog_id;

	IF NOT FOUND THEN
		RAISE EXCEPTION foreign_key_violation;
	END IF;

	RETURN NEW;
END
$BODY$
LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS gt_element_catalog_check ON gt_element_catalog_link CASCADE;
CREATE TRIGGER gt_element_catalog_check BEFORE INSERT OR UPDATE ON gt_element_catalog_link
	FOR EACH ROW EXECUTE PROCEDURE gt_element_catalog_insert_update_check();


---XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX>-INDICATOR-<XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX---
------------------------------------------------------------------------------------------
-- CATALOG INDICATOR GROUP
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_indicator_group CASCADE;
CREATE TABLE IF NOT EXISTS gt_indicator_group (
	id BIGSERIAL PRIMARY KEY,
	name VARCHAR(255) NOT NULL
);
INSERT INTO gt_indicator_group VALUES (0,'root');
------------------------------------------------------------------------------------------
-- CATALOG INDICATOR (triggers are below)
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_catalog_indicator CASCADE;
CREATE TABLE IF NOT EXISTS gt_catalog_indicator (
	id BIGINT NOT NULL UNIQUE,
	indicator_group_id BIGINT NOT NULL DEFAULT 0 REFERENCES gt_indicator_group(id)
		ON UPDATE CASCADE ON DELETE CASCADE,
	tableschema name NOT NULL,
	tablename name NOT NULL,
	code_column name NOT NULL,
	data_column name NOT NULL,
--	time_column name,
	ui_palette VARCHAR(255),
	ui_quartili TEXT,
	gs_name VARCHAR(255) NOT NULL,
	gs_workspace VARCHAR(255),
	gs_url VARCHAR(255) NOT NULL,
	UNIQUE (tableschema,tablename,code_column,data_column)
) INHERITS (gt_catalog);
------------------------------------------------------------------------------------------
-- CATALOG INDICATOR GROUP TREE (triggers are below)
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_indicator_tree CASCADE;
CREATE TABLE IF NOT EXISTS gt_indicator_tree (
	id BIGSERIAL PRIMARY KEY,
	group_id BIGINT NOT NULL UNIQUE REFERENCES gt_indicator_group(id) ON UPDATE CASCADE ON DELETE CASCADE,
	parent_group_id BIGINT NOT NULL REFERENCES gt_indicator_group(id) ON UPDATE CASCADE ON DELETE CASCADE
);
insert into gt_indicator_tree values (0,0,0);
---XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX---


---XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX>-STATISTICAL-<XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX---
------------------------------------------------------------------------------------------
-- CATALOG STATISTICAL GROUP
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_statistical_group CASCADE;
CREATE TABLE IF NOT EXISTS gt_statistical_group (
	id BIGSERIAL PRIMARY KEY,
	name VARCHAR(255) NOT NULL
);
INSERT INTO gt_statistical_group VALUES (0,'root');
------------------------------------------------------------------------------------------
-- CATALOG STATISTICAL (triggers are below)
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_catalog_statistical CASCADE;
CREATE TABLE IF NOT EXISTS  gt_catalog_statistical (
	id BIGINT NOT NULL UNIQUE,
	statistical_group_id BIGINT NOT NULL DEFAULT 0 REFERENCES gt_statistical_group(id)
		ON UPDATE CASCADE ON DELETE CASCADE,
	tableschema name NOT NULL,
	tablename name NOT NULL,
	code_column name NOT NULL,
	data_column name NOT NULL,
--	time_column name,
	UNIQUE (tableschema,tablename,code_column,data_column)
) INHERITS (gt_catalog);
------------------------------------------------------------------------------------------
-- CATALOG STATISTICAL GROUP TREE (triggers are below)
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_statistical_tree CASCADE;
CREATE TABLE IF NOT EXISTS gt_statistical_tree (
	id BIGSERIAL PRIMARY KEY,
	group_id BIGINT NOT NULL UNIQUE REFERENCES gt_statistical_group(id) ON UPDATE CASCADE ON DELETE CASCADE,
	parent_group_id BIGINT NOT NULL REFERENCES gt_statistical_group(id) ON UPDATE CASCADE ON DELETE CASCADE
);
insert into gt_statistical_tree values (0,0,0);
---XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX---


---XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX>-LAYER-<XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX---
------------------------------------------------------------------------------------------
-- CATALOG LAYER GROUP
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_layer_group CASCADE;
CREATE TABLE IF NOT EXISTS gt_layer_group (
	id BIGSERIAL PRIMARY KEY,
	name VARCHAR(255) NOT NULL
);
INSERT INTO gt_layer_group VALUES (0,'root');
------------------------------------------------------------------------------------------
-- CATALOG LAYER (triggers are below)
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_catalog_layer CASCADE;
CREATE TABLE IF NOT EXISTS  gt_catalog_layer (
	id BIGINT NOT NULL UNIQUE,
	layer_group_id BIGINT NOT NULL DEFAULT 0 REFERENCES gt_layer_group(id)
		ON UPDATE CASCADE ON DELETE CASCADE,
--	code_column name,
--	time_column name,
	geom_column name,
	ui_qtip VARCHAR(255),
	gs_name VARCHAR(255) NOT NULL,
	gs_workspace VARCHAR(255),
	gs_url VARCHAR(255) NOT NULL,
	gs_legend_url VARCHAR(255),
	UNIQUE (tableschema,tablename,code_column,geom_column),
	CONSTRAINT set_all_table_fields CHECK
	((tableschema is null = tablename is null AND tablename is null = code_column is null
		AND code_column is null = geom_column is null) OR
	(tableschema is not null AND tablename is not null AND code_column is null AND geom_column is null))
) INHERITS (gt_catalog);
------------------------------------------------------------------------------------------
-- CATALOG LAYER GROUP TREE (triggers are below)
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_layer_tree CASCADE;
CREATE TABLE IF NOT EXISTS gt_layer_tree (
	id BIGSERIAL PRIMARY KEY,
	group_id BIGINT NOT NULL UNIQUE REFERENCES gt_layer_group(id) ON UPDATE CASCADE ON DELETE CASCADE,
	parent_group_id BIGINT NOT NULL REFERENCES gt_layer_group(id) ON UPDATE CASCADE ON DELETE CASCADE
);
insert into gt_layer_tree values (0,0,0);
---XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX---


------------------------------------------------------------------------------------------
-- CATALOG * TREE TRIGGERS
------------------------------------------------------------------------------------------
-- private func --
DROP FUNCTION IF EXISTS _gt_group_find_subtree (bigint,name) CASCADE;
CREATE OR REPLACE FUNCTION _gt_group_find_subtree (group_id bigint, catalog_tree_table name)
RETURNS TABLE (id bigint) AS
$BODY$
BEGIN
	RETURN QUERY EXECUTE 'WITH RECURSIVE subtree(elem) AS (
		(SELECT group_id FROM '||quote_ident($2)||' WHERE parent_group_id = '||$1||')
		UNION
		(SELECT group_id FROM '||quote_ident($2)||',subtree
		 WHERE '||quote_ident($2)||'.parent_group_id = subtree.elem)
	)
	SELECT elem FROM subtree';
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION _gt_group_find_subtree (bigint,name) IS 'TODO';

CREATE OR REPLACE FUNCTION gt_group_tree_check() RETURNS TRIGGER AS
$BODY$
BEGIN
	IF (NEW.group_id = 0) THEN
		RETURN NEW;
	END IF;

	IF (NEW.parent_group_id NOT IN
		(SELECT gid FROM gt_select('SELECT group_id FROM '||TG_TABLE_NAME) AS (gid bigint))
	) THEN
		RAISE EXCEPTION 'Parent not present in tree.';
	END IF;

	IF (NEW.group_id IN (SELECT * FROM _gt_group_find_subtree(NEW.group_id,TG_TABLE_NAME))) THEN
		RAISE EXCEPTION 'Cannot set a descendant as parent.';
	END IF;

	RETURN NEW;
END
$BODY$
LANGUAGE plpgsql;

--gt_indicator_tree
DROP TRIGGER IF EXISTS gt_indicator_tree_after_check ON gt_indicator_tree CASCADE;
CREATE TRIGGER gt_indicator_tree_after_check AFTER INSERT OR UPDATE ON gt_indicator_tree
	FOR EACH ROW EXECUTE PROCEDURE gt_group_tree_check();

--gt_statistical_tree
DROP TRIGGER IF EXISTS gt_statistical_tree_after_check ON gt_statistical_tree CASCADE;
CREATE TRIGGER gt_statistical_tree_after_check AFTER INSERT OR UPDATE ON gt_statistical_tree
	FOR EACH ROW EXECUTE PROCEDURE gt_group_tree_check();

--gt_layer_tree
DROP TRIGGER IF EXISTS gt_layer_tree_after_check ON gt_layer_tree CASCADE;
CREATE TRIGGER gt_layer_tree_after_check AFTER INSERT OR UPDATE ON gt_layer_tree
	FOR EACH ROW EXECUTE PROCEDURE gt_group_tree_check();
------------------------------------------------------------------------------------------


------------------------------------------------------------------------------------------
-- CATALOG * TRIGGERS
------------------------------------------------------------------------------------------
DROP FUNCTION IF EXISTS gt_catalog_link_to_elements (bigint) CASCADE;
CREATE OR REPLACE FUNCTION gt_catalog_link_to_elements (catalog_id bigint,
OUT elements_found bigint, OUT elements_changed bigint) AS
$BODY$
DECLARE
	reln name;
	table_schema name;
	table_name name;
	cod_column name;
	elid bigint;
BEGIN
	elements_found := 0; --Elementi totali
	elements_changed := 0; --Nuovi elementi inseriti

	SELECT INTO reln,table_schema,table_name,cod_column
		p.relname,c.tableschema,c.tablename,c.code_column FROM pg_class p, gt_catalog c
		WHERE c.tableoid = p.oid AND c.id = catalog_id;
	IF NOT FOUND THEN
		RAISE EXCEPTION 'Catalog not found!';
	END IF;

	FOR elid IN EXECUTE ('SELECT DISTINCT (gt_element.id) id FROM gt_element,'
		|| quote_ident(table_schema) ||'.'|| quote_ident(table_name) ||
		' WHERE gt_element.code = '|| quote_ident(table_name) ||'.'|| quote_ident(cod_column))
	LOOP
		elements_found := elements_found +1;
		--collego l'elemento al catalog
		BEGIN
			INSERT INTO gt_element_catalog_link VALUES (DEFAULT,elid,catalog_id);
			elements_changed := elements_changed +1;
		EXCEPTION WHEN unique_violation THEN END;
	END LOOP;
END
$BODY$
LANGUAGE plpgsql;
COMMENT ON FUNCTION gt_catalog_link_to_elements (bigint) IS 'TODO';

CREATE OR REPLACE FUNCTION gt_catalog_statindi_after_insert_check() RETURNS TRIGGER AS
$BODY$
DECLARE
	colname name;
	datatype varchar;
	codefound boolean = false;
	datafound boolean = false;
BEGIN
	FOR colname,datatype IN SELECT column_name, data_type
		FROM gt_get_table_columns(NEW.tableschema,NEW.tablename)
	LOOP
		IF (NEW.code_column = column_name AND datatype = 'character varying'::varchar) THEN
			codefound := true;
		END IF;
		IF (NEW.data_column = column_name) THEN
			datafound := true;
		END IF;
	END LOOP;

	IF (NOT codefound) THEN
		RAISE EXCEPTION 'column ''%'' with type ''character varying'' not found in table ''%.%''',
			NEW.code_column,NEW.tableschema,NEW.tablename;
	END IF;
	
	IF (NOT datafound) THEN
		RAISE EXCEPTION 'column ''%'' not found in table ''%.%''',
			NEW.data_column,NEW.tableschema,NEW.tablename;
	END IF;

	PERFORM gt_catalog_link_to_elements(NEW.id);

	RETURN NEW;
END
$BODY$
LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION gt_catalog_layer_after_insert_check() RETURNS TRIGGER AS
$BODY$
DECLARE
	colname name;
	datatype varchar;
	codefound boolean = false;
	datafound boolean = false;
BEGIN
	IF NEW.geom_column IS NOT NULL THEN
		IF (NEW.geom_column,'geometry'::varchar) NOT IN
		(SELECT column_name, data_type FROM gt_get_table_columns(NEW.tableschema,NEW.tablename)) THEN
			RAISE EXCEPTION 'column ''%'' with type ''geometry'' not found in table ''%.%''',
				NEW.geom_column,NEW.tableschema,NEW.tablename;
		END IF;
	END IF;

	IF NEW.code_column IS NOT NULL THEN
		IF (NEW.code_column,'character varying'::varchar) NOT IN
		(SELECT column_name, data_type FROM gt_get_table_columns(NEW.tableschema,NEW.tablename)) THEN
			RAISE EXCEPTION 'column ''%'' with type ''character varying'' not found in table ''%.%''',
				NEW.code_column,NEW.tableschema,NEW.tablename;
		END IF;
	END IF;

	RETURN NEW;
END
$BODY$
LANGUAGE plpgsql;


/*insert into gt_catalog_statistical (name,tableschema,tablename,code_column,data_column)
values ('Provincia','administrative','ammprv','code','the_geoms')
truncate table gt_catalog_layer*/

CREATE OR REPLACE FUNCTION gt_catalog_update_delete_check() RETURNS TRIGGER AS
$BODY$
BEGIN
	IF (TG_OP = 'DELETE') THEN
		DELETE FROM gt_element_catalog_link WHERE gt_catalog_id = OLD.id;
		RETURN OLD;
	END IF;

	IF (TG_OP = 'UPDATE') THEN
		UPDATE gt_element_catalog_link SET gt_catalog_id = NEW.id WHERE gt_catalog_id = OLD.id;
		RETURN NEW;
	END IF;
END
$BODY$
LANGUAGE plpgsql;

--gt_catalog_indicator
DROP TRIGGER IF EXISTS gt_catalog_indicator_delete_check ON gt_catalog_indicator CASCADE;
CREATE TRIGGER gt_catalog_indicator_delete_check AFTER UPDATE OR DELETE ON gt_catalog_indicator
	FOR EACH ROW EXECUTE PROCEDURE gt_catalog_update_delete_check();
DROP TRIGGER IF EXISTS gt_catalog_indicator_after_check ON gt_catalog_indicator CASCADE;
CREATE TRIGGER gt_catalog_indicator_after_check AFTER INSERT ON gt_catalog_indicator
	FOR EACH ROW EXECUTE PROCEDURE gt_catalog_statindi_after_insert_check();

--gt_catalog_statistical
DROP TRIGGER IF EXISTS gt_catalog_statistical_delete_check ON gt_catalog_statistical CASCADE;
CREATE TRIGGER gt_catalog_statistical_delete_check AFTER UPDATE OR DELETE ON gt_catalog_statistical
	FOR EACH ROW EXECUTE PROCEDURE gt_catalog_update_delete_check();
DROP TRIGGER IF EXISTS gt_catalog_statistical_after_check ON gt_catalog_statistical CASCADE;
CREATE TRIGGER gt_catalog_statistical_after_check AFTER INSERT ON gt_catalog_statistical
	FOR EACH ROW EXECUTE PROCEDURE gt_catalog_statindi_after_insert_check();

--gt_catalog_layer
DROP TRIGGER IF EXISTS gt_catalog_layer_delete_check ON gt_catalog_layer CASCADE;
CREATE TRIGGER gt_catalog_layer_delete_check AFTER UPDATE OR DELETE ON gt_catalog_layer
	FOR EACH ROW EXECUTE PROCEDURE gt_catalog_update_delete_check();
DROP TRIGGER IF EXISTS gt_catalog_layer_after_check ON gt_catalog_layer CASCADE;
CREATE TRIGGER gt_catalog_layer_after_check AFTER INSERT ON gt_catalog_layer
	FOR EACH ROW EXECUTE PROCEDURE gt_catalog_layer_after_insert_check();

/*insert into gt_layer_group values (default,'p1'),(default,'f1'),(default,'f2')
select * from gt_layer_tree
insert into gt_layer_tree values (default,2,1),(default,3,1),(default,3,1)
select * from _gt_group_find_subtree(1,'gt_layer_tree')*/
------------------------------------------------------------------------------------------


------------------------------------------------------------------------------------------
-- CATALOG METADATA
------------------------------------------------------------------------------------------
DROP TABLE IF EXISTS gt_meta CASCADE;
CREATE TABLE IF NOT EXISTS gt_meta (
	id BIGSERIAL NOT NULL PRIMARY KEY,
	gt_catalog_id BIGINT UNIQUE NOT NULL REFERENCES gt_catalog(id) ON UPDATE CASCADE ON DELETE CASCADE,
	description TEXT,
	source TEXT,
	measure_unit TEXT
);

/*CREATE TABLE iet.metastat
(
  id integer NOT NULL DEFAULT nextval('iet.metastat_id_seq1'::regclass),
  nome character varying,
  tipo_fonte character varying,
  fonte_accreditata boolean,
  denominazione_fonte character varying,
  cognome_nome character varying,
  telefono integer,
  mail character varying,
  descrizione_breve character varying,
  descrizione_processo character varying,
  unita_misura character varying,
  tipo_dato character varying,
  disponibilita character varying,
  segreto_statistico boolean,
  argomento character varying,
  fonte character varying,
  primo_anno integer,
  periodicita character varying,
  territorialita character varying,
  scopo character varying,
  ultimo_anno integer,
  id_catalog_stat integer,
  CONSTRAINT id_metastat_pk PRIMARY KEY (id),
  CONSTRAINT metastat_fk FOREIGN KEY (id_catalog_stat)
      REFERENCES iet.catalog_stat (id) MATCH SIMPLE
      ON UPDATE NO ACTION ON DELETE NO ACTION
)*/