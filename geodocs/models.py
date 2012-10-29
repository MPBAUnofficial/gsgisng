from django.db import models
from django.core.validators import \
    MaxValueValidator as MaxVal, \
    MinValueValidator as MinVal
from django.utils.translation import ugettext_lazy as _
from django.dispatch import receiver
from django.db.models.signals import post_syncdb

from profiles.models import GeographicArea


DEGREE_CHOICES = tuple((i, str(i)) for i in range(1, 6)) # 1 to 5

_lon_validators = [MinVal(-360), MaxVal(360)] # quite large...
_lat_validators = [MinVal(-90), MaxVal(90)]

class Point(models.Model):
    degree = models.IntegerField(_('degree'), choices=DEGREE_CHOICES)
    address = models.CharField(_('address'), max_length=511)
    lon = models.FloatField(_('longitude'), validators=_lon_validators)
    lat = models.FloatField(_('latitude'), validators=_lat_validators)
    area = models.ForeignKey(GeographicArea, null=True, blank=True,
                             verbose_name=_('geographic area'))

    def __unicode__(self):
        return u'Point {pk}'.format(pk=self.pk)

    def as_dict(self):
        return {'pk': self.pk,
                'degree': self.degree,
                'address': self.address,
                'lon': self.lon,
                'lat': self.lat,
                'area': \
                    ({'pk': self.area.pk,
                      'code': self.area.cod,
                      'name': self.area.name,
                      } 
                     if self.area else None),
                'images': [img.image.url for img in 
                           self.image_set.all()],
                'docs': [doc.doc.url for doc in
                         self.document_set.all()],
                }

class Image(models.Model):
    point = models.ForeignKey(Point)
    image = models.ImageField(_('image'), upload_to='geodocs/images')

class Document(models.Model):
    point = models.ForeignKey(Point)
    doc = models.FileField(_('document'), upload_to='geodocs/documents')

# This is here, not in another file, just because cursor.execute() gave "syntax error" otherways
_trigger_query = """DO
  $BODY$
    BEGIN
      ALTER TABLE "{table_name}" ADD COLUMN "the_geom" geometry(Point, {SRID});
    EXCEPTION
      WHEN duplicate_column THEN
        NULL;
    END;
  $BODY$
  LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION "{table_name}_geom_trigger_function"()
  RETURNS trigger AS
  $BODY$
    BEGIN
      NEW.the_geom := st_transform(st_setsrid(st_makepoint(NEW.lon,NEW.lat), 4326), {SRID});
      RETURN NEW;
    END;
  $BODY$
  LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS "{table_name}_geom_trigger" ON "{table_name}";
CREATE TRIGGER "{table_name}_geom_trigger"
  BEFORE INSERT OR UPDATE
  ON "{table_name}"
  FOR EACH ROW
  EXECUTE PROCEDURE "{table_name}_geom_trigger_function"();
"""

@receiver(post_syncdb) # is there a way I can use the sender argument?
def create_geom_col_and_trigger(sender, **kwargs):
    if sender.__name__ == __name__: # instead of sender above
        from geodocs.geodocs_settings import GEODOCS_SRID
        from django.db import connection, transaction
        from django.core.exceptions import ImproperlyConfigured
        import os.path

        if GEODOCS_SRID is None:
            raise ImproperlyConfigured(
                'You MUST set GEODOCS_SRID in your settings module!'
            )

        if kwargs['verbosity'] >= 1:
            print 'Installing geodocs geometry management ...'

        q_params = {'table_name': Point._meta.db_table,
                    'SRID': GEODOCS_SRID}

        # This did not work, I guess because of coding problems
        #sqlpath = os.path.join(os.path.dirname(sender.__file__),
        #                       'sql', 'geometry_init.sql')
        #with open(sqlpath, 'UTF8') as f:
        #    query = unicode(f.read().format(**q_params))

        query = _trigger_query.format(**q_params)
        cur = connection.cursor()
        cur.execute(query)
        transaction.commit_unless_managed()
