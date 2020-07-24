@echo off

@rem Delete the DB and the migration repo.

rd /s /q %~dp0\.localdata\db_repository
del /s /q %~dp0\.localdata\ms-cli.db

