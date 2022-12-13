from pathlib import Path
from typing import List, Tuple

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QListWidget,
                               QMainWindow, QPushButton, QVBoxLayout, QWidget,
                               QLabel, QFileDialog, QMessageBox)

from data_converter.ui.settings_window import SettingsWindow
from utilities.utilities.configuration.configuration import Config, ConfigSetup
from utilities.utilities.ui.multi_folder_picker import pick_multiple_folders

WINDOW_TITLE = 'Experiment Data Conversion'


class ConverterGui(QMainWindow):
    """The main GUI for the converter, 
    used to change settings and choose experiment folders

    Parameters
    ----------
    config : Dict
        Converter configuration data
    config_setup : Dict[str, Any]
        Config setup data
    """

    def __init__(self, config: Config, config_setup: ConfigSetup):
        super().__init__()
        self._set_window_params()

        # Models
        self._start_conversion = False
        self._config = config
        self._config_setup = config_setup
        self._destination: None | Path = None

        # UI Elements
        self._settings_button = QPushButton(
            text="Settings"
        )
        self._add_button = QPushButton(text='+')
        self._remove_button = QPushButton(text='-')
        self._set_destination_button = QPushButton(text='Set Destination')
        self._start_button = QPushButton(
            text="Start Conversion"
        )
        self._source_list = QListWidget()
        self._source_list.setSelectionMode(QListWidget.ExtendedSelection)
        self._destination_display = QLabel("Not Set")
        self._settings_dialog = SettingsWindow(self._config, self._config_setup)

        self._connect_signals()
        self._layout_window()

    def _style_controls(self):
        self._start_button.setStyleSheet(
            "QPushButton {"
            "color: green;"
            "background-color: white;"
            "font: bold 14px;"
            "border-style: outset;"
            "border-width: 1px;"
            "border-radius: 5px;"
            "border-color: grey;"
            "min-width: 10em;"
            "padding: 6px;"
            "}"
            "QPushButton:pressed {"
            "border-style: inset"
            "}"
        )
        self._start_button.setMinimumHeight(50)

    def _connect_signals(self):
        """Connects all UI element signals to appropriate slots
        """
        self._settings_button.clicked.connect(  # type: ignore
            self.handle_button_clicked_settings
        )
        self._add_button.clicked.connect(  # type: ignore
            self.handle_button_clicked_add
        )
        self._remove_button.clicked.connect(  # type: ignore
            self.handle_button_clicked_remove
        )
        self._start_button.clicked.connect(  # type: ignore
            self.handle_button_clicked_start
        )
        self._set_destination_button.clicked.connect(  # type: ignore
            self.handle_button_clicked_set_dest
        )
        self._settings_dialog.finished.connect(  # type: ignore
            self.handle_settings_closed
        )

    def _set_window_params(self):
        """Sets up all UI window parameters
        """
        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumWidth(800)

    def _layout_window(self):
        """Generates window layout
        """
        list_edit_button_layout = QHBoxLayout()
        list_edit_button_layout.addStretch()
        list_edit_button_layout.addWidget(self._add_button)
        list_edit_button_layout.addWidget(self._remove_button)

        destination_display_layout = QHBoxLayout()
        destination_display_layout.addWidget(QLabel("Destination: "))
        destination_display_layout.addWidget(self._destination_display)

        layout = QVBoxLayout()
        layout.addWidget(self._settings_button)
        layout.addWidget(self._source_list)
        layout.addLayout(list_edit_button_layout)
        layout.addLayout(destination_display_layout)
        layout.addWidget(self._set_destination_button)
        layout.addWidget(self._start_button)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    @property
    def start_conversion(self) -> bool:
        """This property indicates whether the "Start" button has been pressed, 
        and should not be changed
        """
        return self._start_conversion

    @property
    def config(self) -> Config:
        """This property gives the current conversion settings, and should not 
        be changed.
        """
        return self._config

    @property
    def sources(self) -> list[Path]:
        """This property gives the selected data sources, and should not be 
        changed."""
        return [Path(self._source_list.item(source).text())
                for source in range(self._source_list.count())]

    @property
    def destination(self) -> Path:
        """This property gives the dataset destination, and should not be 
        changed.
        If no destination is set, this property defaults to the user's home 
        folder."""
        dest = self._destination
        return dest if dest is not None else Path.home()

    @Slot()
    def handle_button_clicked_settings(self):
        """Slot handling click events on the "Settings" button
        """
        self._settings_dialog.open()

    @Slot(int)
    def handle_settings_closed(self, result: int):
        """Slot handling dialog close events on the "Settings" dialog

        Parameters
        ----------
        result : int
            Dialog status code, indicating how it was closed (i.e. cancel/OK)
        """
        if result == QDialog.Accepted:
            self._config = self._settings_dialog.config

    @Slot()
    def handle_button_clicked_add(self):
        selected_source, _ = QFileDialog.getOpenFileName(
            self, 'Choose Experiment Data Source')
        self._source_list.addItem(selected_source)

    @Slot()
    def handle_button_clicked_remove(self):
        current_selections = [index.row() for index
                              in self._source_list.selectedIndexes()]
        current_selections.sort(reverse=True)
        for selection in current_selections:
            item = self._source_list.takeItem(selection)
            del (item)

    @Slot()
    def handle_button_clicked_set_dest(self):
        selected_dest = QFileDialog.getExistingDirectory(
            self, "Choose Dataset Destination")
        if selected_dest:
            self._destination = Path(selected_dest)
            self._destination_display.setText(selected_dest)

    @Slot()
    def handle_button_clicked_start(self):
        """Slot handling click events on the "Start Conversion" button
        """
        if self._destination is None:
            QMessageBox.warning(
                self,
                "Destination not set",
                "The dataset destination has not been set yet." +
                " Please set it before starting conversion.")
            return
        self._start_conversion = True
        self.close()


def converter_gui(
    config: Config,
    config_setup: ConfigSetup
) -> Tuple[Config, None | list[Path], Path]:
    """Opens a GUI window for user input, including settings changes and folder selection

    Returns
    -------
    Tuple[Dict, Optional[List[Path]]]
        Tuple of:
            - updated settings (or original if no updates)
            - the chosen path, or None if the converter window is closed
    """
    app = QApplication([])
    converter_gui = ConverterGui(config, config_setup)
    converter_gui.show()

    app.exec_()

    if converter_gui.start_conversion:
        final_config = converter_gui.config
        sources = converter_gui.sources
        destination = converter_gui.destination
    else:
        final_config = config
        sources = None
        destination = Path()

    return final_config, sources, destination


if __name__ == "__main__":
    from data_converter.configuration.configuration import load_config_setup
    from utilities.utilities.configuration.configuration import \
        get_configuration

    config_setup = load_config_setup()
    config = get_configuration({}, config_setup)
    config, folder, destination = converter_gui(config, config_setup)
    print(config)
    print(folder)
    print(destination)
