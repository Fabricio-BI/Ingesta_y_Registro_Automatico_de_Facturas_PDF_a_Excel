@echo off
:: Cambiar al directorio del proyecto
cd /d "C:\Users\HP\Documents\1.Fabricio Coque\17.Portfolio Web\Ingesta _y_Registro_Automático_de_Facturas_PDF_a_Excel"

:: Activar el entorno virtual usando la ruta absoluta encerrada en comillas para evitar fallos
call "%CD%\.venv\Scripts\activate.bat"

cls

echo       EXTRACCION PDF A EXCEL

echo.
echo Ejecutando extraccion...
python main.py

echo.

echo       PROCESO COMPLETADO

echo.
echo Ahora abre el archivo .pbix y presiona Actualizar.
echo.

pause