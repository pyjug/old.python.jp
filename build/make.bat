@echo off

:: If you don't have a specific PYTHON env var set, take it off the path.
if "%PYTHON%" == "" (set PYTHON=python.exe)

if not "%1" == "" goto notnew
"%PYTHON%" new-build\build.py --cache=pydotorg.cache -v -d data -o out -r images,styles,files,js
:notnew

if not "%1" == "serve" goto notserve
%PYTHON% new-build\run-server.py
:notserve

if not "%1" == "clean" goto notclean
if not exist pydotorg.cache goto nocache
del /F pydotorg.cache
:nocache
if not exist out goto noout
rmdir /S /Q out
:noout
:notclean


