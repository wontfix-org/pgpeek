import re as _re

import textual.coordinate as _coordinate
import textual.reactive as _reactive
import textual.widget as _widget
import textual.widgets as _widgets

import pgpeek.confirm as _confirm


class ActivityTable(_widget.Widget, can_focus=True):
    show_idle = _reactive.Reactive(False)
    update_table = _reactive.Reactive(True)
    data = _reactive.Reactive(None)

    BINDINGS = [
        ("i", "show_idle", "Show Idle"),
        ("k", "cancel_backend", "Cancel Backend"),
        ("K", "terminate_backend", "Terminate Backend"),
        ("c", "query_to_clipboard", "Query to Clipboard"),
        ("u", "update_table", "Update Table"),
    ]

    _COLUMNS = {
        "pid": {"label": "PID"},
        "addr": {},
        "waiting": {"label": "Wait", "handle": lambda v: str(int(v))},
        "datname": {"label": "Database"},
        "usename": {"label": "User"},
        "query": {"handle": lambda v: _re.sub(r"\s+", " ", v.replace("\n", " "))},
        "running": {
            "handle": lambda v: str(int(v.total_seconds())) if v else "",
        },
        "lcksh": {"label": "LcksH"},
        "lcksw": {"label": "LcksW"},
        "state": {},
    }

    DEFAULT_CSS = """
    #activity {
        overflow: hidden;
    }
    """

    def __init__(self, state, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = state

    def compose(self):
        table = _widgets.DataTable(id="activity")
        table.cursor_type = "row"
        yield table

    def on_mount(self):
        table = self.query_one(_widgets.DataTable)
        for key, opts in self._COLUMNS.items():
            label = opts.get("label", key.title())
            table.add_column(label, key=key, width=opts.get("width", len(label)))
        self.update()

    def on_focus(self):
        table = self.query_one(_widgets.DataTable)
        table.focus()

    # pylint: disable-next=unused-argument
    def on_resize(self, event):
        self._update_column_widths()
        # self.refresh()

    def update(self):
        if self.update_table:
            a = [
                {k: self._COLUMNS.get(k, {}).get("handle", str)(v).strip() for k, v in row.items()}
                for row in self._state.get_activity()
            ]
            self.data = [_ for _ in a if self.show_idle or _["state"] != "idle"]

            self.set_timer(1, self.update)

    def _update_column_widths(self):
        widths = {}
        for key, opts in self._COLUMNS.items():
            widths[key] = len(opts.get("label", key.title()))

        if self.data is not None:
            for row in self.data:
                for key, opts in self._COLUMNS.items():
                    widths[key] = max(opts.get("width", 0), widths[key], len(row[key]))

        widths["query"] = (
            self.app.size.width - sum(v for k, v in widths.items() if k != "query")
        ) - 10

        for key, value in widths.items():
            self.log(f"Setting {key}.width = {value}")
            self.get_column(key).width = value

        table = self.query_one(_widgets.DataTable)
        table.refresh()

    def watch_data(self):
        self._update_column_widths()
        table = self.query_one(_widgets.DataTable)

        # If there are rows, remember the pid of the selected on
        current = None
        if table.row_count:
            current = table.get_cell_at(table.cursor_coordinate)

        table.clear()

        for idx, row in enumerate(self.data):
            values = list(row.values())
            table.add_row(*values)
            # Check if the PID matches the one of the last selected row,
            # and if so, set the cursor position to it
            if current and values[0] == current:
                table.cursor_coordinate = _coordinate.Coordinate(idx, 0)
                # FIXME(mvb): Shouldn't this be done by watch_cursor_coordinate inside the table?
                table._scroll_cursor_into_view()

    def watch_show_idle(self):
        self.redraw()

    def action_show_idle(self):
        self.show_idle = not self.show_idle

    def action_cancel_backend(self):
        row = self.get_current_row()
        self.app.push_screen(
            _confirm.Confirm(
                f"Cancel backend {row!r}",
                lambda: self._state.pg_cancel_backend(row[0]),
            ),
        )

    def action_terminate_backend(self):
        row = self.get_current_row()
        self.app.push_screen(
            _confirm.Confirm(
                f"terminate backend {row!r}",
                lambda: self._state.pg_terminate_backend(row[0]),
            ),
        )

    def action_update_table(self):
        self.log("Toggled table updating")
        self.update_table = not self.update_table

    def watch_update_table(self):
        if self.update_table:
            self.set_timer(1, self.update)

    def action_query_to_clipboard(self):
        self.app.set_clipboard(self.get_current_query(), "Query copied to clipboard")

    def get_current_row(self):
        table = self.query_one(_widgets.DataTable)
        return table.get_row_at(table.cursor_coordinate.row)

    def get_current_query(self):
        return self.get_current_row()[5]

    def get_column(self, key):
        table = self.query_one(_widgets.DataTable)
        return table.columns[key]

    def get_current_pid(self):
        return self.get_current_row()[0]
