import tkinter as tk
from tkinter import filedialog, messagebox
import time
import os
import shutil  # NUEVO: Librería de Python para mover archivos físicamente

from .api_gemini import extraer_datos_factura
from .gestor_excel import guardar_en_excel, obtener_ruta_excel


class AppExtractor:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Procesador Automático de Facturas")
        # Hemos hecho la ventana un poquito más alta para el nuevo botón
        self.ventana.geometry("500x350")
        self.ventana.config(padx=20, pady=20)

        self.archivos_seleccionados = []
        self.carpeta_destino = ""  # NUEVO: Guardará la ruta donde mover los PDFs

        # --- SECCIÓN 1: ARCHIVOS ORIGEN ---
        tk.Label(self.ventana, text="1. Selecciona las facturas a procesar:", font=("Arial", 10, "bold")).pack(
            anchor="w", pady=(0, 5))
        btn_archivo = tk.Button(self.ventana, text="Explorar Archivos", command=self.seleccionar_archivos)
        btn_archivo.pack(anchor="w")
        self.lbl_archivo_seleccionado = tk.Label(self.ventana, text="0 archivos seleccionados", fg="gray")
        self.lbl_archivo_seleccionado.pack(anchor="w", pady=(5, 10))

        # --- SECCIÓN 2: CARPETA DESTINO (NUEVO) ---
        tk.Label(self.ventana, text="2. ¿A qué carpeta movemos los documentos listos?",
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        btn_carpeta = tk.Button(self.ventana, text="Elegir Carpeta Destino", command=self.seleccionar_carpeta)
        btn_carpeta.pack(anchor="w")
        self.lbl_carpeta_destino = tk.Label(self.ventana, text="Ninguna carpeta seleccionada", fg="gray")
        self.lbl_carpeta_destino.pack(anchor="w", pady=(5, 15))

        # --- SECCIÓN 3: PROCESAR ---
        ruta_excel = obtener_ruta_excel()
        lbl_info = tk.Label(self.ventana, text=f"Los datos se guardan en:\n{ruta_excel}", fg="green", justify="left")
        lbl_info.pack(anchor="w", pady=(0, 15))

        self.btn_procesar = tk.Button(self.ventana, text="Procesar, Guardar y Mover", command=self.procesar_documentos,
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

    def seleccionar_carpeta(self):
        # NUEVO: Abre un diálogo exclusivo para elegir carpetas
        carpeta = filedialog.askdirectory(title="Selecciona la carpeta destino")
        if carpeta:
            self.carpeta_destino = carpeta
            self.lbl_carpeta_destino.config(text=self.carpeta_destino)

    def procesar_documentos(self):
        if not self.archivos_seleccionados:
            messagebox.showwarning("Advertencia", "Por favor, selecciona al menos un archivo primero.")
            return

        # NUEVO: Bloqueamos si el usuario olvidó elegir la carpeta destino
        if not self.carpeta_destino:
            messagebox.showwarning("Advertencia",
                                   "Por favor, elige la carpeta de destino donde se moverán los documentos.")
            return

        self.btn_procesar.config(state=tk.DISABLED)

        total_archivos = len(self.archivos_seleccionados)
        exitosos = 0
        errores = 0

        for i, ruta_archivo in enumerate(self.archivos_seleccionados):
            self.btn_procesar.config(text=f"Procesando {i + 1} de {total_archivos}...")
            self.ventana.update()

            try:
                # 1. Extraemos los datos de Gemini
                datos_json = extraer_datos_factura(ruta_archivo)

                if isinstance(datos_json, dict):
                    # 2. Construir el nombre del documento
                    num_factura = datos_json.get("numero_factura")

                    # Seguridad: Si por algún motivo Gemini no encontró el número, ponemos una marca de tiempo
                    if not num_factura:
                        num_factura = f"Desconocida_{int(time.time())}"

                    # Seguridad: Quitamos barras (/) para que Windows no crea que son subcarpetas
                    num_factura_limpio = str(num_factura).replace("/", "-").replace("\\", "-")
                    nombre_final_doc = f"Factura_{num_factura_limpio}"

                    # 3. Lo inyectamos en el JSON para que el gestor_excel lo escriba en su columna
                    datos_json["nombre_documento"] = nombre_final_doc

                    # 4. Guardamos en el Excel
                    guardar_en_excel(datos_json)

                    # 5. MOVER Y RENOMBRAR EL ARCHIVO FÍSICO
                    extension = os.path.splitext(ruta_archivo)[1]  # Extrae si es .pdf, .jpg, etc.
                    nuevo_nombre_con_extension = f"{nombre_final_doc}{extension}"
                    ruta_destino_final = os.path.join(self.carpeta_destino, nuevo_nombre_con_extension)

                    # Seguridad: Si ya existiera un archivo con ese exacto nombre en la carpeta, le añade un "_1"
                    contador = 1
                    while os.path.exists(ruta_destino_final):
                        ruta_destino_final = os.path.join(self.carpeta_destino,
                                                          f"{nombre_final_doc}_{contador}{extension}")
                        contador += 1

                    # ¡Mueve la factura original a su nuevo hogar con su nuevo nombre!
                    shutil.move(ruta_archivo, ruta_destino_final)

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

        self.btn_procesar.config(text="Procesar, Guardar y Mover", state=tk.NORMAL)
        self.archivos_seleccionados = []
        self.lbl_archivo_seleccionado.config(text="0 archivos seleccionados")

        mensaje_final = f"Proceso finalizado.\n\n✅ Éxitos: {exitosos}\n❌ Errores: {errores}\n\nLos archivos procesados se han movido a:\n{self.carpeta_destino}"
        messagebox.showinfo("Resumen de Extracción", mensaje_final)

    def iniciar(self):
        self.ventana.mainloop()