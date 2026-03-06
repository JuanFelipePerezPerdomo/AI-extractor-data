import tkinter as tk
from tkinter import filedialog, messagebox
import os
import shutil
import time

from .api_gemini import extraer_datos_factura
from .gestor_excel import guardar_en_excel, obtener_ruta_excel


class AppExtractor:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Robot Extractor de Facturas")
        self.ventana.geometry("500x450")
        self.ventana.config(padx=20, pady=20)

        self.carpeta_origen = ""
        self.carpeta_destino = ""
        self.vigilando = False  # Interruptor de encendido/apagado del robot
        self.exitosos = 0
        self.errores = 0

        # --- SECCIÓN 1: CARPETA DE ENTRADA (VIGILADA) ---
        tk.Label(self.ventana, text="1. Carpeta de ENTRADA (Donde descargas las facturas):",
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        btn_origen = tk.Button(self.ventana, text="Elegir Carpeta de Entrada", command=self.seleccionar_origen)
        btn_origen.pack(anchor="w")
        self.lbl_origen = tk.Label(self.ventana, text="Ninguna carpeta seleccionada", fg="gray")
        self.lbl_origen.pack(anchor="w", pady=(5, 10))

        # --- SECCIÓN 2: CARPETA DE SALIDA (ARCHIVO FINAL) ---
        tk.Label(self.ventana, text="2. Carpeta de SALIDA (Donde se guardan procesadas):",
                 font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        btn_destino = tk.Button(self.ventana, text="Elegir Carpeta de Salida", command=self.seleccionar_destino)
        btn_destino.pack(anchor="w")
        self.lbl_destino = tk.Label(self.ventana, text="Ninguna carpeta seleccionada", fg="gray")
        self.lbl_destino.pack(anchor="w", pady=(5, 15))

        # --- SECCIÓN 3: BOTÓN DE VIGILANCIA ---
        ruta_excel = obtener_ruta_excel()
        tk.Label(self.ventana, text=f"Excel destino: {ruta_excel}", fg="green", justify="left").pack(anchor="w",
                                                                                                     pady=(0, 10))

        self.btn_vigilar = tk.Button(self.ventana, text="▶ INICIAR VIGILANCIA AUTOMÁTICA",
                                     command=self.toggle_vigilancia, bg="#0d6efd", fg="white",
                                     font=("Arial", 11, "bold"), height=2)
        self.btn_vigilar.pack(fill="x", pady=5)

        # --- SECCIÓN 4: ESTADÍSTICAS ---
        self.lbl_estado = tk.Label(self.ventana, text="Estado: Detenido", font=("Arial", 10, "italic"))
        self.lbl_estado.pack(pady=5)

        self.lbl_contadores = tk.Label(self.ventana, text="✅ Procesadas: 0   |   ❌ Errores: 0", font=("Arial", 11))
        self.lbl_contadores.pack(pady=5)

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

    def toggle_vigilancia(self):
        # Esta función enciende o apaga el robot
        if not self.vigilando:
            if not self.carpeta_origen or not self.carpeta_destino:
                messagebox.showwarning("Advertencia", "Selecciona ambas carpetas primero.")
                return
            if self.carpeta_origen == self.carpeta_destino:
                messagebox.showwarning("Advertencia", "La carpeta de entrada y salida NO pueden ser la misma.")
                return

            self.vigilando = True
            self.btn_vigilar.config(text="⏹ DETENER VIGILANCIA", bg="#dc3545")  # Cambia a botón rojo
            self.lbl_estado.config(text="Estado: 👁️ Buscando nuevas facturas...", fg="blue")
            self.vigilar_carpeta()  # Arrancamos el motor radar
        else:
            self.vigilando = False
            self.btn_vigilar.config(text="▶ INICIAR VIGILANCIA AUTOMÁTICA", bg="#0d6efd")  # Vuelve a azul
            self.lbl_estado.config(text="Estado: Detenido", fg="black")

    def vigilar_carpeta(self):
        # Si hemos pulsado "Detener", esta función se cancela a sí misma
        if not self.vigilando:
            return

        extensiones_validas = ('.pdf', '.jpg', '.jpeg', '.png')
        # Escaneamos la carpeta buscando archivos
        archivos_en_origen = [f for f in os.listdir(self.carpeta_origen) if f.lower().endswith(extensiones_validas)]

        if archivos_en_origen:
            # Si hay archivos, cogemos el primero de la lista
            archivo_actual = archivos_en_origen[0]
            ruta_completa_origen = os.path.join(self.carpeta_origen, archivo_actual)

            self.lbl_estado.config(text=f"Estado: ⚙️ Procesando '{archivo_actual}'...", fg="#cc5500")  # Color Naranja
            self.ventana.update()

            try:
                # 1. Extraemos los datos con Gemini
                datos_json = extraer_datos_factura(ruta_completa_origen)

                if isinstance(datos_json, dict):
                    # 2. Fabricamos el nombre
                    num_factura = datos_json.get("numero_factura")
                    if not num_factura:
                        num_factura = f"Desconocida_{int(time.time())}"

                    num_factura_limpio = str(num_factura).replace("/", "-").replace("\\", "-")
                    nombre_final_doc = f"Factura_{num_factura_limpio}"
                    datos_json["nombre_documento"] = nombre_final_doc

                    # 3. Guardamos en el Excel
                    guardar_en_excel(datos_json)

                    # 4. Mover a la carpeta de salida
                    extension = os.path.splitext(archivo_actual)[1]
                    nuevo_nombre_con_extension = f"{nombre_final_doc}{extension}"
                    ruta_destino_final = os.path.join(self.carpeta_destino, nuevo_nombre_con_extension)

                    contador = 1
                    while os.path.exists(ruta_destino_final):
                        ruta_destino_final = os.path.join(self.carpeta_destino,
                                                          f"{nombre_final_doc}_{contador}{extension}")
                        contador += 1

                    shutil.move(ruta_completa_origen, ruta_destino_final)
                    self.exitosos += 1
                else:
                    raise ValueError("El JSON devuelto no era un diccionario válido.")

            except Exception as e:
                print(f"Error procesando {archivo_actual}: {str(e)}")
                # MEDIDA DE SEGURIDAD VITAL: Si un archivo da error, le cambiamos la extensión a .error
                # para que el robot lo ignore en la próxima pasada y no se quede atascado en un bucle infinito.
                try:
                    ruta_error = ruta_completa_origen + ".error"
                    os.rename(ruta_completa_origen, ruta_error)
                except Exception:
                    pass
                self.errores += 1

            self.lbl_contadores.config(text=f"✅ Procesadas: {self.exitosos}   |   ❌ Errores: {self.errores}")

            # Al terminar una factura, ordenamos al radar que espere 4 segundos (Rate Limit Google) y vuelva a escanear
            self.lbl_estado.config(text="Estado: ⏳ Pausa de seguridad (4s)...", fg="#cc5500")
            self.ventana.after(4000, self.vigilar_carpeta)

        else:
            # Si NO hay facturas nuevas, ordenamos al radar que vuelva a mirar en 3 segundos
            self.lbl_estado.config(text="Estado: 👁️ Buscando nuevas facturas...", fg="blue")
            self.ventana.after(3000, self.vigilar_carpeta)

    def iniciar(self):
        self.ventana.mainloop()