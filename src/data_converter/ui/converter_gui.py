from pathlib import Path
from typing import List, Optional, Tuple

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QListWidget,
                               QMainWindow, QPushButton, QVBoxLayout, QWidget, 
                               QLabel, QFileDialog, QMessageBox)

from data_converter.ui.settings_window import SettingsWindow
from utilities.utilities.configuration.configuration import Config, ConfigSetup
from utilities.utilities.ui.multi_folder_picker import pick_multiple_folders

WINDOW_TITLE = 'Select Experiment Folder'  # TODO change this?


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
        self.settings_button = QPushButton(
            text="Settings"
        )
        self.add_button = QPushButton(text='+')
        self.remove_button = QPushButton(text='-')
        self.set_destination_button = QPushButton(text='Set Destination')
        self.start_button = QPushButton(
            text="Start Conversion"
        )
        self.folder_list = QListWidget()
        self.folder_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.destination_display = QLabel("Not Set")
        self.settings_dialog = SettingsWindow(self._config, self._config_setup)

        self._connect_signals()
        self._layout_window()

    def _style_controls(self):
        self.start_button.setStyleSheet(
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
        self.start_button.setMinimumHeight(50)

    def _connect_signals(self):
        """Connects all UI element signals to appropriate slots
        """
        self.settings_button.clicked.connect(  # type: ignore
            self.handle_button_clicked_settings
        )
        self.add_button.clicked.connect(  # type: ignore
            self.handle_button_clicked_add
        )
        self.remove_button.clicked.connect(  # type: ignore
            self.handle_button_clicked_remove
        )
        self.start_button.clicked.connect(  # type: ignore
            self.handle_button_clicked_start
        )
        self.set_destination_button.clicked.connect(  # type: ignore
            self.handle_button_clicked_set_dest
        )
        self.settings_dialog.finished.connect(  # type: ignore
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
        list_edit_button_layout.addWidget(self.add_button)
        list_edit_button_layout.addWidget(self.remove_button)
        
        destination_display_layout = QHBoxLayout()
        destination_display_layout.addWidget(QLabel("Destination: "))
        destination_display_layout.addWidget(self.destination_display)
        
        layout = QVBoxLayout()
        layout.addWidget(self.settings_button)
        layout.addWidget(self.folder_list)
        layout.addLayout(list_edit_button_layout)
        layout.addLayout(destination_display_layout)
        layout.addWidget(self.set_destination_button)
        layout.addWidget(self.start_button)

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
        self.settings_dialog.open()

    @Slot(int)
    def handle_settings_closed(self, result: int):
        """Slot handling dialog close events on the "Settings" dialog

        Parameters
        ----------
        result : int
            Dialog status code, indicating how it was closed (i.e. cancel/OK)
        """
        if result == QDialog.Accepted:
            self._config = self.settings_dialog.config

    @Slot()
    def handle_button_clicked_add(self):
        selected_folders = pick_multiple_folders(self, 
                                                 'Choose Experiment Folder(s)')
        if selected_folders:
            valid_folders = [folder for folder in selected_folders 
                             if Path(folder).is_dir()]
            self.folder_list.addItems(valid_folders)
    
    @Slot()
    def handle_button_clicked_remove(self):
        current_selections = [index.row() for index 
                              in self.folder_list.selectedIndexes()]
        current_selections.sort(reverse=True)
        for selection in current_selections:
            item = self.folder_list.takeItem(selection)
            del(item)
    
    @Slot()
    def handle_button_clicked_set_dest(self):
        selected_dest = QFileDialog.getExistingDirectory(
            self, "Choose Dataset Destination")
        if selected_dest:
            self._destination = Path(selected_dest)
            self.destination_display.setText(selected_dest)

    @Slot()
    def handle_button_clicked_start(self):
        """Slot handling click events on the "Start Conversion" button
        """
        if self._destination is None:
            QMessageBox.warning(
                self, 
                "Destination not set", 
                "The dataset destination has not been set yet."+
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
        folders = [
            Path(converter_gui.folder_list.item(folder).text())
            for folder in range(converter_gui.folder_list.count())
        ]
        destination = converter_gui.destination
    else:
        final_config = config
        folders = None
        destination = Path()

    return final_config, folders, destination


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
