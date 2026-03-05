import tkinter as tk
from tkinter import filedialog, messagebox
import time

from .api_gemini import extraer_datos_factura
# NUEVO: Importamos desde el gestor_excel
from .gestor_excel import guardar_en_excel, obtener_ruta_excel


class AppExtractor:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Procesador Automático de Facturas")
        self.ventana.geometry("450x250")
        self.ventana.config(padx=20, pady=20)

        self.archivos_seleccionados = []

        tk.Label(self.ventana, text="1. Selecciona las facturas a procesar:", font=("Arial", 10, "bold")).pack(
            anchor="w", pady=(0, 5))

        btn_archivo = tk.Button(self.ventana, text="Explorar Archivos", command=self.seleccionar_archivos)
        btn_archivo.pack(anchor="w")

        self.lbl_archivo_seleccionado = tk.Label(self.ventana, text="0 archivos seleccionados", fg="gray")
        self.lbl_archivo_seleccionado.pack(anchor="w", pady=(5, 15))

        ruta_excel = obtener_ruta_excel()
        lbl_info = tk.Label(self.ventana, text=f"Los datos se guardan en:\n{ruta_excel}", fg="green", justify="left")
        lbl_info.pack(anchor="w", pady=(0, 15))

        # Textos actualizados a Excel
        self.btn_procesar = tk.Button(self.ventana, text="Procesar y Añadir a Excel", command=self.procesar_documentos,
                                      bg="#107c41", fg="white", font=("Arial", 11, "bold"))
        self.btn_procesar.pack(fill="x")

    def seleccionar_archivos(self):
        filepaths = filedialog.askopenfilenames(
            title="Selecciona una o varias facturas",
            filetypes=(("PDFs", "*.pdf"), ("Imágenes", "*.jpg *.jpeg *.png"), ("Todos los archivos", "*.*"))
        )
        if filepaths:
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

        for i, ruta_archivo in enumerate(self.archivos_seleccionados):
            self.btn_procesar.config(text=f"Procesando {i + 1} de {total_archivos}...")
            self.ventana.update()

            try:
                datos_json = extraer_datos_factura(ruta_archivo)

                if isinstance(datos_json, dict):
                    # NUEVO: Llamamos a la función de Excel
                    guardar_en_excel(datos_json)
                    exitosos += 1
                else:
                    errores += 1

            except Exception as e:
                print(f"Error con el archivo {ruta_archivo}: {str(e)}")
                errores += 1

            if i < total_archivos - 1:
                self.btn_procesar.config(text=f"Pausa de seguridad... ({i + 1}/{total_archivos})")
                self.ventana.update()
                time.sleep(4)

        self.btn_procesar.config(text="Procesar y Añadir a Excel", state=tk.NORMAL)
        self.archivos_seleccionados = []
        self.lbl_archivo_seleccionado.config(text="0 archivos seleccionados")

        mensaje_final = f"Proceso de lote finalizado.\n\n✅ Éxitos: {exitosos}\n❌ Errores: {errores}"
        messagebox.showinfo("Resumen de Extracción", mensaje_final)

    def iniciar(self):
        self.ventana.mainloop()