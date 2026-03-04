import tkinter as tk
from tkinter import filedialog, messagebox

# Importamos las herramientas de nuestros otros módulos
from .api_gemini import extraer_datos_factura
from .gestor_csv import guardar_en_csv, obtener_ruta_csv


class AppExtractor:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Procesador Automático de Facturas")
        self.ventana.geometry("450x250")
        self.ventana.config(padx=20, pady=20)

        tk.Label(self.ventana, text="1. Selecciona la factura a procesar:", font=("Arial", 10, "bold")).pack(anchor="w",
                                                                                                             pady=(0,
                                                                                                                   5))

        btn_archivo = tk.Button(self.ventana, text="Explorar Archivos", command=self.seleccionar_archivo)
        btn_archivo.pack(anchor="w")

        self.lbl_archivo_seleccionado = tk.Label(self.ventana, text="Ningún archivo seleccionado", fg="gray")
        self.lbl_archivo_seleccionado.pack(anchor="w", pady=(5, 15))

        ruta_csv = obtener_ruta_csv()
        lbl_info = tk.Label(self.ventana, text=f"Los datos se guardarán automáticamente en:\n{ruta_csv}", fg="blue",
                            justify="left")
        lbl_info.pack(anchor="w", pady=(0, 15))

        self.btn_procesar = tk.Button(self.ventana, text="Procesar y Añadir a CSV", command=self.procesar_documento,
                                      bg="#0d6efd", fg="white", font=("Arial", 11, "bold"))
        self.btn_procesar.pack(fill="x")

    def seleccionar_archivo(self):
        filepath = filedialog.askopenfilename(
            title="Selecciona una factura",
            filetypes=(("PDFs", "*.pdf"), ("Imágenes", "*.jpg *.jpeg *.png"), ("Todos los archivos", "*.*"))
        )
        if filepath:
            self.lbl_archivo_seleccionado.config(text=filepath)

    def procesar_documento(self):
        ruta_archivo = self.lbl_archivo_seleccionado.cget("text")

        if ruta_archivo == "Ningún archivo seleccionado" or not ruta_archivo:
            messagebox.showwarning("Advertencia", "Por favor, selecciona un archivo primero.")
            return

        self.btn_procesar.config(text="Procesando Factura...", state=tk.DISABLED)
        self.ventana.update()

        try:
            # 1. Hablamos con Gemini
            datos_json = extraer_datos_factura(ruta_archivo)

            # 2. Guardamos en el CSV
            if isinstance(datos_json, dict):
                ruta_guardado = guardar_en_csv(datos_json)
                messagebox.showinfo("Éxito", f"Factura procesada y añadida a:\n{ruta_guardado}")
                self.lbl_archivo_seleccionado.config(text="Ningún archivo seleccionado")
            else:
                messagebox.showwarning("Aviso", "El modelo no devolvió la estructura esperada.")

        except ValueError as error_controlado:
            messagebox.showerror("Error", str(error_controlado))
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error inesperado:\n{str(e)}")
        finally:
            self.btn_procesar.config(text="Procesar y Añadir a CSV", state=tk.NORMAL)

    def iniciar(self):
        self.ventana.mainloop()