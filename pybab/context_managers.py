from django.db import connection, transaction

class get_raw_cursor(object):
    def __enter__(self):
        return connection.cursor()

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            return False

        transaction.commit_unless_managed()
