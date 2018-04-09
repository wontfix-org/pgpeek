import base64 as _base64
import os as _os

import rich.control as _control
import rich.segment as _segment
import textual.app as _app
import textual.containers as _containers
import textual.widgets as _widgets

import pgpeek.activity_table as _activity_table
import pgpeek.connection as _connection
import pgpeek.state as _state


class OSC52Control(_control.Control):
    """OSC control sequence to copy data to the clipboard

    https://en.wikipedia.org/wiki/ANSI_escape_code#OSC
    https://invisible-island.net/xterm/ctlseqs/ctlseqs.html
    """

    # pylint: disable-next=super-init-not-called
    def __init__(self, type_, data):
        encoded = _base64.b64encode(data.encode("utf-8")).decode("utf-8")
        # I am not sure what the contents of the third argument is really used for,
        # it is stored on the `control` attribute and all the code I found is only
        # using it in a boolean way to see if there are supposed to be control
        # characters in the segment...
        self.segment = _segment.Segment(f"\x1b]52;{type_};{encoded}\a", None, [52])


class Toast(_widgets.Static):
    # We just mimic Footer here
    DEFAULT_CSS = """
    Toast {
        background: $accent;
        color: $text;
        text-style: bold;
    }
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.visible = False


class Application(_app.App):
    BINDINGS = [("q", "quit", "Quit")]
    TITLE = "PGPeek"
    CSS_PATH = "pgpeek.css"

    DEFAULT_CSS = """
    #content {
        overflow: hidden;
    }
    """

    def __init__(self, state, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = state

    def on_mount(self):
        self.query_one(_activity_table.ActivityTable).focus()

    def compose(self):
        with _containers.Vertical(id="content"):
            yield _activity_table.ActivityTable(self._state)
            yield _widgets.Footer()
            yield Toast()

    def toast(self, msg):
        footer = self.query_one(_widgets.Footer)
        toast = self.query_one(_widgets.Static)
        footer.visible = False
        toast.visible = True
        toast.update(f">> {msg}")
        self.set_timer(1, self._reset_toast)
        # self.refresh()

    def _reset_toast(self):
        footer = self.query_one(_widgets.Footer)
        toast = self.query_one(_widgets.Static)
        footer.visible = True
        toast.visible = False

    def set_clipboard(self, data, toast=None):
        self.console.control(OSC52Control("c", data))
        if toast is not None:
            self.toast(toast)


class DevApplication(Application):
    """Special version of the app that explicitly inspects PGPEEK_DSN

    This is because the `textual run --dev` command wants to load the app
    class and run it "manually", so we cannot use the standard click entrypoint
    for this, but we still need to configure the database connection somehow.

    I am still not familiar enough with textual to figure out how I really
    should do this, so for now I'll just leave it at this...
    """

    def __init__(self, *args, **kwargs):
        state = _state.State(_connection.Connection(_os.environ["PGPEEK_DSN"]))
        super().__init__(state, *args, **kwargs)
