@echo on
::Tushare Stock
Set PYTHON_FILES=*.py
::Set C_FILES=*.c
::Set H_FILES=*.h
Set BAT_FILES=*.bat
::Set DOC_FILES=*.docx
::Set XLS_FILES=*.xlsx
::Set SRC_FOLDER1=C:\Myfolder\Project_sz\AVR_prj\mega128\sw_mega128
if exist E:\tushare_stock_quant\*.py (
    Set OBJ_FOLDER1=E:\tushare_stock_quant) else (
    Set OBJ_FOLDER1=D:\tushare_stock_quant
    )
echo %OBJ_FOLDER1%


echo Back to U_Disk

@echo on
pause

::copy sw_mega128 to U_disk
::echo d|xcopy %cd%"\%C_FILES%" "%OBJ_FOLDER1%\%C_FILES%" /r/y/D
::echo d|xcopy %cd%"\%H_FILES%" "%OBJ_FOLDER1%\%H_FILES%" /r/y/D
echo d|xcopy %cd%"\%BAT_FILES%" "%OBJ_FOLDER1%\%BAT_FILES%" /r/y/D
::echo d|xcopy %cd%"\%DOC_FILES%" "%OBJ_FOLDER1%\%DOC_FILES%" /r/y/D
::echo d|xcopy %cd%"\%XLS_FILES%" "%OBJ_FOLDER1%\%XLS_FILES%" /r/y/D
echo d|xcopy %cd%"\%PYTHON_FILES%" "%OBJ_FOLDER1%\%PYTHON_FILES%" /r/y/D


pause