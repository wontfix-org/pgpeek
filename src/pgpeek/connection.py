import sys as _sys
import weakref as _weakref

import psycopg2 as _pg2
import psycopg2.extensions as _pg2extensions
import psycopg2.extras as _pg2extras
import six as _six


class Connection(object):
    def __init__(self, dsn):
        """Initialization"""
        self._cursors = set()
        self._conn = _pg2.connect(dsn)
        self._dsn = dsn

    @property
    def dsn(self):
        return _pg2extensions.parse_dsn(self._dsn)

    def __del__(self):
        """Destruction"""
        self.close()

    def close(self):
        """Close connection"""
        for cursor in self._cursors:
            self.del_cursor(cursor)
        self._conn.close()

    def _execute(self, method, args, kwargs):
        cursor = self.cursor(cursor_factory=_pg2extras.DictCursor)
        try:
            getattr(cursor, method)(*args, **kwargs)
        except _pg2.OperationalError:
            e = _sys.exc_info()
            try:
                try:
                    cursor.close()
                except _pg2.Error:
                    pass
                _six.reraise(e[0], e[1], e[2])
            finally:
                del e
        self._cursors.add(cursor)
        return ResultSet(self, cursor)

    def execute(self, *args, **kwargs):
        """Execute a statement"""
        return self._execute("execute", args, kwargs)

    def executemany(self, *args, **kwargs):
        """Executemany a statement"""
        return self._execute("executemany", args, kwargs)

    def callproc(self, *args, **kwargs):
        """Callproc"""
        return self._execute("callproc", args, kwargs)

    def cursor(self, *args, **kwargs):
        """Create a cursor"""
        return AutoCursor(self, self._conn.cursor(*args, **kwargs))

    def begin(self):
        """Begin a transaction"""
        return self._conn.begin()

    def commit(self):
        """Commit a transaction"""
        return self._conn.commit()

    def rollback(self):
        """Rollback a transaction"""
        self._conn.rollback()

    def del_cursor(self, cursor):
        """Excplicitly destroy this cursor"""
        self._cursors -= set([cursor])
        try:
            cursor.close()
        except _pg2.Error:
            pass


class AutoCursor(object):
    """Auto cursor"""

    _cursor = None

    def __init__(self, conn, cursor):
        """Initialization"""
        self._conn = _weakref.ref(conn)
        self._cursor = cursor

    def __getattr__(self, name):
        """Delegate to original cursor object by default"""
        return getattr(self._cursor, name)

    def __iter__(self):
        """Return cursor iterator"""
        for row in self._cursor:
            yield row

    def __del__(self):
        self.close()

    def close(self):
        """Close the cursor"""
        cursor, self._cursor = self._cursor, None
        if cursor is not None:
            conn = self._conn()
            if conn is None:
                cursor.close()
            else:
                conn.del_cursor(cursor)


class ResultSet(object):
    """Result set container"""

    def __init__(self, conn, cursor):
        self._conn = conn
        self._cursor = cursor

    def __del__(self):
        self._conn.del_cursor(self._cursor)

    def __iter__(self):
        # we can"t just return iter(self._cursor), because it might trigger self.__del__
        for row in self._cursor:
            yield row

    def __getattr__(self, name):
        """Delegate unknown symbols to the cursor"""
        if name in ("lastrowid", "rownum", "rowcount"):
            return getattr(self._cursor, name)
        raise AttributeError(name)

    def fetchone(self):
        """Fetch next result"""
        return self._cursor.fetchone()
