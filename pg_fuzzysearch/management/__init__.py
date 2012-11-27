from django.db.models.signals import post_syncdb
import pg_fuzzysearch.models
from django.db import connection, transaction

def my_callback(sender, **kwargs):
    cursor = connection.cursor()
    print "Setting up pg_fuzzysearch ..."
    with open("pg_fuzzysearch/setup.sql","r") as f:
        query = f.read()
        with transaction.commit_on_success():
            cursor.execute(query)

post_syncdb.connect(my_callback, sender=pg_fuzzysearch.models)
