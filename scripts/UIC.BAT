@echo off
echo ** Building MapEditor
pyuic5 -o .\src\ui\mapeditor.py ui\mapeditor.ui

echo ** Building MainWindow
pyuic5 -o .\src\ui\mainwindow.py ui\mainwindow.ui

echo ** Building PreloadRows
pyuic5 -o .\src\ui\preload.py ui\preload.ui

echo ** Building MapConfig
pyuic5 -o .\src\ui\mapconfig.py ui\mapconfig.ui
