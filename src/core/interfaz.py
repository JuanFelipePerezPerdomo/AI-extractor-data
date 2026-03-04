import tkinter as tk
from tkinter import filedialog, messagebox
import time

from .api_gemini import extraer_datos_factura
from .gestor_csv import guardar_en_csv, obtener_ruta_csv


class AppExtractor:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Procesador Automático de Facturas")
        self.ventana.geometry("450x250")
        self.ventana.config(padx=20, pady=20)

        # Lista para guardar las rutas de todos los archivos seleccionados
        self.archivos_seleccionados = []

        tk.Label(self.ventana, text="1. Selecciona las facturas a procesar:", font=("Arial", 10, "bold")).pack(
            anchor="w", pady=(0, 5))

        btn_archivo = tk.Button(self.ventana, text="Explorar Archivos", command=self.seleccionar_archivos)
        btn_archivo.pack(anchor="w")

        self.lbl_archivo_seleccionado = tk.Label(self.ventana, text="0 archivos seleccionados", fg="gray")
        self.lbl_archivo_seleccionado.pack(anchor="w", pady=(5, 15))

        ruta_csv = obtener_ruta_csv()
        lbl_info = tk.Label(self.ventana, text=f"Los datos se guardan en:\n{ruta_csv}", fg="blue", justify="left")
        lbl_info.pack(anchor="w", pady=(0, 15))

        self.btn_procesar = tk.Button(self.ventana, text="Procesar y Añadir a CSV", command=self.procesar_documentos,
                                      bg="#0d6efd", fg="white", font=("Arial", 11, "bold"))
        self.btn_procesar.pack(fill="x")

    def seleccionar_archivos(self):
        # askopenfilenames (en plural) permite selección múltiple
        filepaths = filedialog.askopenfilenames(
            title="Selecciona una o varias facturas",
            filetypes=(("PDFs", "*.pdf"), ("Imágenes", "*.jpg *.jpeg *.png"), ("Todos los archivos", "*.*"))
        )
        if filepaths:
            # Convertimos la tupla que devuelve Tkinter a una lista de Python
            self.archivos_seleccionados = list(filepaths)
            self.lbl_archivo_seleccionado.config(
                text=f"{len(self.archivos_seleccionados)} archivos seleccionados listos")

    def procesar_documentos(self):
        if not self.archivos_seleccionados:
            messagebox.showwarning("Advertencia", "Por favor, selecciona al menos un archivo primero.")
            return

        self.btn_procesar.config(state=tk.DISABLED)

        total_archivos = len(self.archivos_seleccionados)
        exitosos = 0
        errores = 0

        # Recorremos todas las facturas seleccionadas
        for i, ruta_archivo in enumerate(self.archivos_seleccionados):
            self.btn_procesar.config(text=f"Procesando {i + 1} de {total_archivos}...")
            self.ventana.update()  # Forzamos a la ventana a actualizar el texto

            try:
                datos_json = extraer_datos_factura(ruta_archivo)

                if isinstance(datos_json, dict):
                    guardar_en_csv(datos_json)
                    exitosos += 1
                else:
                    errores += 1

            except Exception as e:
                print(f"Error con el archivo {ruta_archivo}: {str(e)}")
                errores += 1

            # PAUSA DE SEGURIDAD (Rate Limit de Google)
            # Solo hacemos la pausa si NO estamos en la última factura
            if i < total_archivos - 1:
                self.btn_procesar.config(text=f"Pausa de seguridad... ({i + 1}/{total_archivos})")
                self.ventana.update()
                time.sleep(4)  # Esperamos 4 segundos

        # Terminamos todo el lote
        self.btn_procesar.config(text="Procesar y Añadir a CSV", state=tk.NORMAL)
        self.archivos_seleccionados = []
        self.lbl_archivo_seleccionado.config(text="0 archivos seleccionados")

        mensaje_final = f"Proceso de lote finalizado.\n\n✅ Éxitos: {exitosos}\n❌ Errores: {errores}"
        messagebox.showinfo("Resumen de Extracción", mensaje_final)

    def iniciar(self):
        self.ventana.mainloop()