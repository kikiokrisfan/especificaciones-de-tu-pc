import os
import platform
import shutil
import subprocess
import sys
import tkinter as tk

ES_WINDOWS = sys.platform.startswith("win")


def ejecutar_powershell(comando):
    """Ejecuta un comando de PowerShell sin abrir ventana. Devuelve lista de líneas."""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", comando],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )
        return [l.strip() for l in r.stdout.splitlines() if l.strip()]
    except Exception:
        return []


def nombre_cpu():
    if ES_WINDOWS:
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
            ) as k:
                return winreg.QueryValueEx(k, "ProcessorNameString")[0].strip()
        except Exception:
            pass
    return platform.processor() or "Desconocido"


def nucleos_fisicos():
    if ES_WINDOWS:
        lineas = ejecutar_powershell(
            "(Get-CimInstance Win32_Processor | "
            "Measure-Object -Property NumberOfCores -Sum).Sum"
        )
        if lineas and lineas[0].isdigit():
            return int(lineas[0])
    return None


def ram_total_bytes():
    if ES_WINDOWS:
        try:
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            m = MEMORYSTATUSEX()
            m.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return m.ullTotalPhys
        except Exception:
            return None
    try:
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except Exception:
        return None


def nombres_gpu():
    if ES_WINDOWS:
        return ejecutar_powershell(
            "Get-CimInstance Win32_VideoController | "
            "Select-Object -ExpandProperty Name"
        )
    return []


def discos():
    resultado = []
    if ES_WINDOWS:
        rutas = [f"{c}:\\" for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if os.path.exists(f"{c}:\\")]
    else:
        rutas = ["/"]
    for ruta in rutas:
        try:
            total = shutil.disk_usage(ruta).total
            resultado.append(f"{ruta}  {total / 1024**3:.0f} GB")
        except Exception:
            pass
    return resultado


def obtener_datos(pantalla=None):
    datos = []

    datos.append(("Sistema operativo", f"{platform.system()} {platform.release()}"))
    datos.append(("Nombre del equipo", platform.node() or "Desconocido"))

    datos.append(("CPU", nombre_cpu()))
    fisicos = nucleos_fisicos()
    hilos = os.cpu_count()
    if fisicos and hilos:
        datos.append(("Núcleos / hilos", f"{fisicos} núcleos / {hilos} hilos"))
    elif hilos:
        datos.append(("Hilos", str(hilos)))

    ram = ram_total_bytes()
    if ram:
        datos.append(("RAM", f"{round(ram / 1024**3)} GB"))

    gpus = nombres_gpu()
    if gpus:
        datos.append(("GPU", "\n".join(gpus)))

    d = discos()
    if d:
        datos.append(("Almacenamiento", "\n".join(d)))

    if pantalla:
        datos.append(("Pantalla", f"{pantalla[0]} x {pantalla[1]}"))

    return datos


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Especificaciones del PC")
        self.resizable(False, False)
        self.configure(padx=20, pady=16)

        self.datos = obtener_datos((self.winfo_screenwidth(), self.winfo_screenheight()))

        for fila, (etiqueta, valor) in enumerate(self.datos):
            tk.Label(
                self, text=etiqueta + ":", font=("Segoe UI", 11, "bold"),
                anchor="ne", justify="right",
            ).grid(row=fila, column=0, sticky="ne", padx=(0, 12), pady=4)
            tk.Label(
                self, text=valor, font=("Segoe UI", 11),
                anchor="nw", justify="left",
            ).grid(row=fila, column=1, sticky="nw", pady=4)

        tk.Button(
            self, text="Copiar", font=("Segoe UI", 10), command=self.copiar
        ).grid(row=len(self.datos), column=0, columnspan=2, pady=(14, 0))

    def copiar(self):
        texto = "\n".join(f"{e}: {v}" for e, v in self.datos)
        self.clipboard_clear()
        self.clipboard_append(texto)


if __name__ == "__main__":
    App().mainloop()
