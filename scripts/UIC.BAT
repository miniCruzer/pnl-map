@echo off
echo ** Building MapEditor
pyuic5 -o .\src\ui\mapeditor.py ui\mapeditor.ui

echo ** Building MainWindow
pyuic5 -o .\src\ui\mainwindow.py ui\mainwindow.ui

