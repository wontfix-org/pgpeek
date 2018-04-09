import logging as _logging

import click as _click

import pgpeek.application as _application
import pgpeek.connection as _connection
import pgpeek.state as _state

# _logging.basicConfig(level=_logging.DEBUG, filename="peek.log")
_log = _logging.getLogger(__name__)


@_click.command()
@_click.argument("dsn", nargs=1)
def cli(dsn):
    state = _state.State(_connection.Connection(dsn))
    _application.Application(state=state).run()
