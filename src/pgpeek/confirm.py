import textual.containers as _containers
import textual.screen as _screen
import textual.widgets as _widgets


class Confirm(_screen.Screen):
    DEFAULT_CSS = """
    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        padding: 1 2;
    }

    #question {
        column-span: 2;
        content-align: center bottom;
        width: 100%;
        height: 100%;
    }

    #dialog Button {
        width: 100%;
    }
    """

    def __init__(self, question, action, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._question = question
        self._action = action

    def compose(self):
        yield _containers.Grid(
            _widgets.Static(self._question, id="question"),
            _widgets.Button("Yes", variant="success", id="yes"),
            _widgets.Button("No", variant="error", id="no"),
            id="dialog",
        )

    def on_button_pressed(self, event: _widgets.Button.Pressed):
        self.app.pop_screen()
        if event.button.id == "yes":
            self._action()
