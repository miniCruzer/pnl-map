@echo off
REM Run tests for each module
echo ** Testing src\mapper.py
python -m src.mapper
echo ** Testing src\libexcel.py
python -m src.libexcel
