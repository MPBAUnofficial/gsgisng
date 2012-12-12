from django.db import models

class PgFuzzySearchManager(models.Manager):
    def __init__(self,colname=None):
        super(PgFuzzySearchManager,self).__init__()
        self.colname = colname

    def f_search(self, keyword, colname=None, max_dist=None):
        """
        Returns a list of models, approximately matching keyword.
        colname: column to search. Optional if provided at initialization time.
        max_dist: maximum lehvenstein's distance from keyword allowed.
                  if not provided, defaults to max(1, int(len(keyword) / 3))
        """
        from django.db import connection
        if max_dist is None:
            max_dist = max(1, int(len(keyword) / 3))
        if colname is None:
            colname = self.colname
        if colname is None:
            raise TypeError("Colname argument must be specified "
                            "since no default was given")
        cursor = connection.cursor()
        tablename = self.model._meta.db_table
        cursor.callproc("fuzzysearch",[tablename,colname,keyword,max_dist])
        results = cursor.fetchall()
        cursor.close()

        ret = []
        for val in range(0, max_dist + 1):
            filter_kwargs = {colname + '__in': [row[0] for row in results if row[1]==val]}
            ret.extend(self.filter(**filter_kwargs))
        return ret

