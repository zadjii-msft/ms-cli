@echo off

rd /s /q %~dp0\.localdata\db_repository
del /s /q %~dp0\.localdata\ms-cli.db

python repop.py
