@echo off

%~dp0\.venv\Scripts\activate && python3 %~dp0\src\data_converter.py% & deactivate