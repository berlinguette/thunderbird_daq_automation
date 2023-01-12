import re
from pathlib import Path
from typing import Iterable

from data_converter.conversion.support.abstract_folder_converter import \
    AbstractFolderConverter
from data_converter.conversion.support.bin_folder_to_parquet import \
    BINtoParquetFolderConverter
from data_converter.conversion.support.csv_folder_to_parquet import \
    CSVtoParquetFolderConverter
from data_converter.conversion.support.enums import CAENDataFormat
from utilities.utilities.configuration.configuration import Config


class FolderConverterFactory:
    def make_folder_converter(self, folder: Path, destination: Path | Iterable[Path], config: Config, logfile_path: Path) -> AbstractFolderConverter:
        folder_format = self._determine_folder_contents(folder)
        if folder_format == CAENDataFormat.CSV:
            return CSVtoParquetFolderConverter(
                folder, destination, config, logfile_path)
        elif folder_format == CAENDataFormat.BIN:
            return BINtoParquetFolderConverter(
                folder, destination, config, logfile_path)
        else:
            raise ValueError(
                f"Folder {folder.name} contained unsupported file type")

    def _determine_folder_contents(self, folder: Path) -> CAENDataFormat | None:
        bin_pattern = re.compile(r".*\.bin", flags=re.IGNORECASE)
        csv_pattern = re.compile(r".*\.csv", flags=re.IGNORECASE)
        contains_bin = any((
            bin_pattern.fullmatch(file.name) for file in folder.iterdir()
        ))
        contains_csv = any((
            csv_pattern.fullmatch(file.name) for file in folder.iterdir()
        ))
        if contains_bin:
            return CAENDataFormat.BIN
        if contains_csv:
            return CAENDataFormat.CSV
        return None  # STUB
