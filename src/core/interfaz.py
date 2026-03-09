import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import shutil
import time
import threading
import queue
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from .api_gemini import extraer_datos_factura

from .gestor_excel import guardar_en_excel, obtener_ruta_excel, factura_existe_en_excel


class DetectarNuevaFactura(FileSystemEventHandler):
    def __init__(self, cola, funcion_log):
        self.cola = cola
        self.funcion_log = funcion_log

    def on_created(self, event):
        if not event.is_directory and event.src_path.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
            nombre_arch = os.path.basename(event.src_path)
            self.funcion_log(f"Detectado nuevo archivo: {nombre_arch}", "SISTEMA")
            self.cola.put(event.src_path)


class AppExtractor:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Robot RPA: Extractor de Facturas")
        self.ventana.geometry("600x650")
        self.ventana.config(padx=20, pady=10)

        self.ventana.protocol("WM_DELETE_WINDOW", self.cerrar_aplicacion)

        self.carpeta_origen = ""
        self.carpeta_destino = ""
        self.vigilando = False
        self.cerrando = False
        self.exitosos = 0
        self.errores = 0
        self.duplicados = 0

        self.cola_archivos = queue.Queue()
        self.observer = None

        threading.Thread(target=self.trabajador_en_segundo_plano, daemon=True).start()

        frame_carpetas = tk.Frame(self.ventana)
        frame_carpetas.pack(fill="x", pady=5)

        tk.Label(frame_carpetas, text="1. Carpeta ENTRADA:", font=("Arial", 9, "bold")).grid(row=0, column=0,
                                                                                             sticky="w", pady=2)
        tk.Button(frame_carpetas, text="Elegir", command=self.seleccionar_origen).grid(row=0, column=1, padx=5, pady=2)
        self.lbl_origen = tk.Label(frame_carpetas, text="Ninguna", fg="gray", width=40, anchor="w")
        self.lbl_origen.grid(row=0, column=2, sticky="w")

        tk.Label(frame_carpetas, text="2. Carpeta SALIDA:", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="w",
                                                                                            pady=2)
        tk.Button(frame_carpetas, text="Elegir", command=self.seleccionar_destino).grid(row=1, column=1, padx=5, pady=2)
        self.lbl_destino = tk.Label(frame_carpetas, text="Ninguna", fg="gray", width=40, anchor="w")
        self.lbl_destino.grid(row=1, column=2, sticky="w")

        ruta_excel = obtener_ruta_excel()
        tk.Label(self.ventana, text=f"Excel destino: {ruta_excel}", fg="green", font=("Arial", 9)).pack(anchor="w",
                                                                                                        pady=(5, 0))

        self.btn_vigilar = tk.Button(self.ventana, text="▶ INICIAR VIGILANCIA", command=self.toggle_vigilancia,
                                     bg="#0d6efd", fg="white", font=("Arial", 11, "bold"))
        self.btn_vigilar.pack(fill="x", pady=10)

        self.lbl_estado = tk.Label(self.ventana, text="Estado: Detenido", font=("Arial", 10, "italic"))
        self.lbl_estado.pack()

        self.lbl_contadores = tk.Label(self.ventana, text="✅ Proc: 0   |   ⚠️ Dupl: 0   |   ❌ Err: 0",
                                       font=("Arial", 11, "bold"))
        self.lbl_contadores.pack(pady=5)

        tk.Label(self.ventana, text="Registro de Actividad:", font=("Arial", 10, "bold")).pack(anchor="w")

        self.txt_log = scrolledtext.ScrolledText(self.ventana, height=12, state=tk.DISABLED, font=("Consolas", 9),
                                                 bg="#f4f4f4")
        self.txt_log.pack(fill="both", expand=True)

        self.txt_log.tag_config("INFO", foreground="black")
        self.txt_log.tag_config("EXITO", foreground="green")
        self.txt_log.tag_config("ERROR", foreground="red")
        self.txt_log.tag_config("SISTEMA", foreground="blue")
        self.txt_log.tag_config("WARNING", foreground="#cc5500")

        self.escribir_log("Sistema iniciado. Anti-duplicados activado.", "SISTEMA")

    def escribir_log(self, mensaje, nivel="INFO"):
        def _escribir():
            self.txt_log.config(state=tk.NORMAL)
            hora = time.strftime("%H:%M:%S")
            self.txt_log.insert(tk.END, f"[{hora}] {mensaje}\n", nivel)
            self.txt_log.see(tk.END)
            self.txt_log.config(state=tk.DISABLED)

        self.ventana.after(0, _escribir)

    def cerrar_aplicacion(self):
        self.cerrando = True
        self.vigilando = False
        self.btn_vigilar.config(state=tk.DISABLED)
        self.escribir_log("Cerrando aplicación...", "SISTEMA")
        self.actualizar_ui(self.lbl_estado, "Estado: Cerrando procesos...", "red")

        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=2)

        self.ventana.destroy()
        os._exit(0)

    def seleccionar_origen(self):
        carpeta = filedialog.askdirectory(title="Selecciona la carpeta de Entrada")
        if carpeta:
            self.carpeta_origen = carpeta
            self.lbl_origen.config(text=self.carpeta_origen)

    def seleccionar_destino(self):
        carpeta = filedialog.askdirectory(title="Selecciona la carpeta de Salida")
        if carpeta:
            self.carpeta_destino = carpeta
            self.lbl_destino.config(text=self.carpeta_destino)

    def actualizar_ui(self, elemento, texto, color="black"):
        self.ventana.after(0, lambda: elemento.config(text=texto, fg=color))

    def toggle_vigilancia(self):
        if not self.vigilando:
            if not self.carpeta_origen or not self.carpeta_destino:
                messagebox.showwarning("Advertencia", "Selecciona ambas carpetas primero.")
                return
            if self.carpeta_origen == self.carpeta_destino:
                messagebox.showwarning("Advertencia", "Las carpetas NO pueden ser la misma.")
                return

            self.vigilando = True
            self.btn_vigilar.config(text="⏹ DETENER VIGILANCIA", bg="#dc3545")
            self.actualizar_ui(self.lbl_estado, "Estado: 👁️ Ojos de Watchdog activados...", "blue")

            extensiones_validas = ('.pdf', '.jpg', '.jpeg', '.png')
            archivos_existentes = [f for f in os.listdir(self.carpeta_origen) if
                                   f.lower().endswith(extensiones_validas)]

            if archivos_existentes:
                self.escribir_log(f"Encontrados {len(archivos_existentes)} archivos pendientes. Procesando...",
                                  "SISTEMA")
                for archivo in archivos_existentes:
                    self.cola_archivos.put(os.path.join(self.carpeta_origen, archivo))

            manejador_eventos = DetectarNuevaFactura(self.cola_archivos, self.escribir_log)
            self.observer = Observer()
            self.observer.schedule(manejador_eventos, self.carpeta_origen, recursive=False)
            self.observer.start()
        else:
            self.vigilando = False
            self.btn_vigilar.config(text="▶ INICIAR VIGILANCIA", bg="#0d6efd")
            self.actualizar_ui(self.lbl_estado, "Estado: Detenido", "black")

            if self.observer:
                self.observer.stop()
                self.observer.join()

    def trabajador_en_segundo_plano(self):
        while not self.cerrando:
            try:
                ruta_completa_origen = self.cola_archivos.get(timeout=1)
            except queue.Empty:
                continue

            if not self.vigilando or self.cerrando:
                self.cola_archivos.task_done()
                continue

            archivo_actual = os.path.basename(ruta_completa_origen)
            time.sleep(1)

            self.actualizar_ui(self.lbl_estado, f"Estado: ⚙️ Procesando '{archivo_actual}'...", "#cc5500")

            try:
                datos_json = extraer_datos_factura(ruta_completa_origen)

                if isinstance(datos_json, dict):
                    proveedor = datos_json.get("proveedor_emisor")
                    num_factura = datos_json.get("numero_factura")

                    if not num_factura:
                        num_factura = f"Desc_{int(time.time())}"

                    num_factura_limpio = str(num_factura).replace("/", "-").replace("\\", "-")
                    nombre_final_doc = f"Factura_{num_factura_limpio}"
                    datos_json["nombre_documento"] = nombre_final_doc
                    extension = os.path.splitext(archivo_actual)[1]

                    # --- LÓGICA ANTI-DUPLICADOS ---
                    if factura_existe_en_excel(proveedor, num_factura):
                        self.duplicados += 1
                        self.escribir_log(
                            f"⚠️ IGNORADA: La factura '{num_factura}' de '{proveedor}' ya existe en Excel.", "WARNING")

                        # Creamos carpeta Duplicados si no existe
                        carpeta_duplicados = os.path.join(self.carpeta_destino, "Duplicados")
                        os.makedirs(carpeta_duplicados, exist_ok=True)

                        nuevo_nombre = f"Duplicado_{nombre_final_doc}{extension}"
                        ruta_destino_final = os.path.join(carpeta_duplicados, nuevo_nombre)

                        contador = 1
                        while os.path.exists(ruta_destino_final):
                            ruta_destino_final = os.path.join(carpeta_duplicados,
                                                              f"Duplicado_{nombre_final_doc}_{contador}{extension}")
                            contador += 1

                        shutil.move(ruta_completa_origen, ruta_destino_final)
                    else:
                        # FACTURA NUEVA (PROCESO NORMAL)
                        guardar_en_excel(datos_json)

                        nuevo_nombre_con_extension = f"{nombre_final_doc}{extension}"
                        ruta_destino_final = os.path.join(self.carpeta_destino, nuevo_nombre_con_extension)

                        contador = 1
                        while os.path.exists(ruta_destino_final):
                            ruta_destino_final = os.path.join(self.carpeta_destino,
                                                              f"{nombre_final_doc}_{contador}{extension}")
                            contador += 1

                        shutil.move(ruta_completa_origen, ruta_destino_final)
                        self.exitosos += 1
                        self.escribir_log(f"Completado: {archivo_actual} -> {nuevo_nombre_con_extension}", "EXITO")
                    # -------------------------------

                else:
                    raise ValueError("La respuesta de Gemini no era válida.")

            except Exception as e:
                self.errores += 1
                self.escribir_log(f"Fallo en {archivo_actual} -> Motivo: {str(e)}", "ERROR")
                try:
                    os.rename(ruta_completa_origen, ruta_completa_origen + ".error")
                except:
                    pass

            # Actualizamos el contador incluyendo los duplicados
            texto_contadores = f"✅ Proc: {self.exitosos}   |   ⚠️ Dupl: {self.duplicados}   |   ❌ Err: {self.errores}"
            self.actualizar_ui(self.lbl_contadores, texto_contadores)

            for segundo in range(4, 0, -1):
                if not self.vigilando or self.cerrando: break
                self.actualizar_ui(self.lbl_estado, f"Estado: ⏳ Enfriando motor ({segundo}s)...", "#cc5500")
                time.sleep(1)

            if self.vigilando and not self.cerrando:
                self.actualizar_ui(self.lbl_estado, "Estado: 👁️ Ojos de Watchdog activados...", "blue")

            self.cola_archivos.task_done()

    def iniciar(self):
        self.ventana.mainloop()