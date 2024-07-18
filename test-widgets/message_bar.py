import sys

import _set_source_path  # noqa
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from source.widgets.message_bar import MessageBar


class MainWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupWidgets()

    def setupWidgets(self) -> None:
        self.message_bar = MessageBar()

        close_show_button = QPushButton("Show MessageClose")
        close_show_button.clicked.connect(
            lambda: self.message_bar.displayMessage(
                "Showing MessageClose", True)
        )

        self.message_bar.connectClose(self.onClose)

        prompt_show_button = QPushButton("Show MessagePrompt")
        prompt_show_button.clicked.connect(
            lambda: self.message_bar.displayPrompt(
                "Showing MessagePrompt \n Next line", True)
        )

        self.message_bar.connect(self.message_bar.displayPrompt,
                                 "Showing Another Message Prompt")

        vertical_spacer = QSpacerItem(
            20, 0, QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )

        layout = QVBoxLayout()
        layout.addWidget(close_show_button)
        layout.addWidget(prompt_show_button)
        layout.addSpacerItem(vertical_spacer)
        layout.addWidget(self.message_bar)
        layout.setContentsMargins(0, 0, 0, 0)

        main_widget = QWidget()
        main_widget.setLayout(layout)

        self.stacked_widget = QStackedWidget()
        self.stacked_widget.addWidget(main_widget)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

    def onClose(self) -> None:
        if '\n' in self.message_bar.message_close.label.text():
            self.message_bar.displayMessage("Showing MessageClose", True)
        else:
            self.message_bar.displayMessage(
                "Showing MessageClose\n XMS\n TXMS", True
            )


if __name__ == '__main__':
    import qdarkstyle  # type: ignore
    app = QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet(  # type: ignore
        qt_api='pyqt6'))
    main_widget = MainWidget()
    main_widget.resize(650, 450)
    main_widget.setWindowTitle("Message bar")
    main_widget.show()
    sys.exit(app.exec())
