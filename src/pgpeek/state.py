import logging as _logging
import re as _re

import packaging.version as _version

_log = _logging.getLogger(__name__)

PG9_6 = _version.Version("9.6")
PG10 = _version.Version("10")


class State(object):
    activity_stmt = r"""
        SELECT
            pid,
            client_addr || $$:$$ || client_port as addr,
            {waiting} AS waiting,
            datname,
            usename,
            query,
            NOW() - query_start AS running,
            (SELECT count(1) FROM pg_locks pl WHERE pl.pid = psa.pid and pl.granted = true) AS lcksh,
            (SELECT count(1) FROM pg_locks pl WHERE pl.pid = psa.pid and pl.granted = false) AS lcksw,
            state
        FROM
            pg_stat_activity psa
        WHERE
            true
            AND state is not null
            --AND state != 'idle'
        ORDER BY
            running desc
        ;
    """

    def __init__(self, conn):
        self._conn = conn
        self._set_version()

    @property
    def dsn(self):
        return self._conn.dsn

    def _set_version(self):
        m = _re.match(r"PostgreSQL ([^ ]+)", list(self._conn.callproc("version"))[0][0])
        self.version = _version.parse(m.group(1))
        _log.debug("PostgreSQL version: %r", self.version)

    def _simplecall(self, funcname, *args):
        try:
            result = next(map(dict, self._conn.callproc(funcname, args)))
            _log.debug("RESULT %r", result)
            return result
        finally:
            self._conn.commit()

    def pg_terminate_backend(self, pid):
        return self._simplecall("pg_terminate_backend", int(pid))

    def pg_cancel_backend(self, pid):
        return self._simplecall("pg_cancel_backend", int(pid))

    def get_activity(self):
        _log.debug("Updating activity")
        if self.version >= PG9_6:
            waiting = """
                CASE
                    WHEN wait_event IS NOT NULL THEN false
                    WHEN wait_event = 'Activity' THEN false
                    ELSE true
                END
            """
        else:
            waiting = "waiting"

        stmt = self.activity_stmt.format(
            waiting=waiting,
        )
        try:
            return map(dict, self._conn.execute(stmt))
        finally:
            self._conn.rollback()
