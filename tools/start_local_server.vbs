' Arranca un servidor local (http://localhost:8000) sirviendo la carpeta
' del proyecto, en segundo plano y sin ventana visible. Doble clic para
' iniciarlo; se queda corriendo hasta que apagues o reinicies el PC.
' No modifica nada del proyecto ni de la web real (Vercel) - solo sirve
' los archivos en local para poder verlos en el navegador.

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\guia-regalos"
WshShell.Run "cmd /c python -m http.server 8000", 0, False
