import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import customtkinter as ctk
import pandas as pd
from dian_parser import parse_dian_xml
from threading import Thread

# Configuración de apariencia
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SuperFacturasApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SuperFacturas DIAN - Anexo Técnico 1.9")
        self.geometry("1400x900")

        # Variables de estado
        self.folder_path = ""
        self.documents = []
        self.columns_config = [
            # Info Básica
            ("tipoDocLabel", "Tipo Doc", True),
            ("numero", "Número", True),
            ("fechaEmision", "Fecha", True),
            ("horaEmision", "Hora", False),
            ("fechaVencimiento", "Vencimiento", False),
            ("moneda", "Moneda", False),
            # Emisor
            ("emisorNombre", "Emisor Nombre", True),
            ("emisorNit", "Emisor NIT", True),
            ("emisorCiudad", "Emisor Ciudad", False),
            ("emisorEmail", "Emisor Email", False),
            # Receptor
            ("receptorNombre", "Receptor Nombre", True),
            ("receptorNit", "Receptor NIT", True),
            ("receptorCiudad", "Receptor Ciudad", False),
            ("receptorEmail", "Receptor Email", False),
            # Pagos
            ("metodoPago", "Método Pago", False),
            ("canalPago", "Canal Pago", False),
            ("fechaLimitePago", "Límite Pago", False),
            # Totales
            ("totalBruto", "Subtotal Bruto", True),
            ("baseImponible", "Base Impuestos", True),
            ("totalDescuentos", "Descuentos", False),
            ("totalImpuestos", "Total Impuestos", True),
            ("totalPagar", "Total a Pagar", True),
            # Ítems (en modo detalle)
            ("lineId", "Ítem #", True),
            ("descripcion", "Descripción", True),
            ("cantidad", "Cant", True),
            ("unidadMedida", "UM", False),
            ("precioUnitario", "Precio Unit", True),
            ("lineaBase", "Línea Base", True),
            ("lineaImpuestos", "Línea Imp", True),
            ("marca", "Marca", False),
            ("modelo", "Modelo", False),
            ("codigoEstandar", "Cód Estándar", False),
            # Otros
            ("cufe", "CUFE", False),
            ("fileName", "Archivo", False),
        ]
        
        self.setup_ui()

    def setup_ui(self):
        # Grid layout 1x2
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Barra Lateral
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="SuperFacturas", font=ctk.CTkFont(family="Outfit", size=24, weight="bold"))
        self.logo_label.pack(pady=20, padx=20)

        # Nivel de Detalle
        self.detail_label = ctk.CTkLabel(self.sidebar, text="NIVEL DE DETALLE", font=ctk.CTkFont(size=12, weight="bold"))
        self.detail_label.pack(pady=(20, 5), padx=20, anchor="w")
        
        self.detail_var = ctk.StringVar(value="summary")
        self.radio_summary = ctk.CTkRadioButton(self.sidebar, text="Resumen (Totales)", variable=self.detail_var, value="summary", command=self.update_preview)
        self.radio_summary.pack(pady=5, padx=30, anchor="w")
        self.radio_items = ctk.CTkRadioButton(self.sidebar, text="Detalle (Por Ítem)", variable=self.detail_var, value="items", command=self.update_preview)
        self.radio_items.pack(pady=5, padx=30, anchor="w")

        # Opciones de Excel
        self.options_label = ctk.CTkLabel(self.sidebar, text="OPCIONES DE EXCEL", font=ctk.CTkFont(size=12, weight="bold"))
        self.options_label.pack(pady=(20, 5), padx=20, anchor="w")
        
        self.group_var = ctk.BooleanVar(value=False)
        self.check_group = ctk.CTkCheckBox(self.sidebar, text="Separar por pestañas", variable=self.group_var)
        self.check_group.pack(pady=5, padx=30, anchor="w")

        # Columnas
        self.cols_label = ctk.CTkLabel(self.sidebar, text="COLUMNAS VISIBLES", font=ctk.CTkFont(size=12, weight="bold"))
        self.cols_label.pack(pady=(20, 5), padx=20, anchor="w")
        
        self.scrollable_cols = ctk.CTkScrollableFrame(self.sidebar, height=200, label_text="Configurar Columnas")
        self.scrollable_cols.pack(pady=10, padx=10, fill="both", expand=True)
        
        self.col_vars = {}
        for key, label, enabled in self.columns_config:
            var = ctk.BooleanVar(value=enabled)
            cb = ctk.CTkCheckBox(self.scrollable_cols, text=label, variable=var, command=self.update_preview)
            cb.pack(pady=2, padx=5, anchor="w")
            self.col_vars[key] = var

        # Botón Exportar
        self.btn_export = ctk.CTkButton(self.sidebar, text="Exportar Excel", command=self.export_excel, fg_color="#10b981", hover_color="#059669")
        self.btn_export.pack(pady=20, padx=20, side="bottom", fill="x")

        # Área Principal
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Cabecera de acción
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        self.btn_select = ctk.CTkButton(self.header_frame, text="Seleccionar Carpeta", command=self.select_folder)
        self.btn_select.pack(side="left")
        
        self.path_label = ctk.CTkLabel(self.header_frame, text="Ninguna carpeta seleccionada", text_color="gray")
        self.path_label.pack(side="left", padx=20)

        # Tabla de Vista Previa
        self.preview_container = ctk.CTkFrame(self.main_frame, corner_radius=10)
        self.preview_container.grid(row=1, column=0, sticky="nsew")
        
        # Usamos Treeview de ttk para la tabla, pero la estilizamos
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#1e293b", 
                        foreground="#f8fafc", 
                        rowheight=25, 
                        fieldbackground="#1e293b",
                        borderwidth=0)
        style.map("Treeview", background=[('selected', '#4f46e5')])
        style.configure("Treeview.Heading", background="#0f172a", foreground="white", borderwidth=0)

        self.tree_frame = tk.Frame(self.preview_container, bg="#1e293b")
        self.tree_frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        self.tree_scroll_y = ctk.CTkScrollbar(self.preview_container, orientation="vertical")
        self.tree_scroll_y.pack(side="right", fill="y")
        
        self.tree_scroll_x = ctk.CTkScrollbar(self.preview_container, orientation="horizontal")
        self.tree_scroll_x.pack(side="bottom", fill="x")

        self.tree = ttk.Treeview(self.tree_frame, selectmode="browse", yscrollcommand=self.tree_scroll_y.set, xscrollcommand=self.tree_scroll_x.set)
        self.tree.pack(fill="both", expand=True)
        
        self.tree_scroll_y.configure(command=self.tree.yview)
        self.tree_scroll_x.configure(command=self.tree.xview)

    def select_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.folder_path = path
            self.path_label.configure(text=path, text_color="white")
            self.load_documents(path)

    def load_documents(self, path):
        self.documents = []
        xml_files = [f for f in os.listdir(path) if f.lower().endswith('.xml')]
        
        if not xml_files:
            messagebox.showwarning("Aviso", "No se encontraron archivos XML en la carpeta seleccionada.")
            return

        def process():
            for f in xml_files:
                doc = parse_dian_xml(os.path.join(path, f))
                if doc:
                    self.documents.append(doc)
            self.after(0, self.update_preview)

        Thread(target=process).start()

    def update_preview(self, *args):
        # Limpiar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Determinar todos los nombres de impuestos y campos sectoriales presentes
        all_tax_names = set()
        all_extra_fields = set()
        for doc in self.documents:
            for t_data in doc.get('impuestosDesglose', {}).values():
                all_tax_names.add(t_data['name'])
            for key in doc.keys():
                if key.startswith(('Salud_', 'Transporte_')):
                    all_extra_fields.add(key)
            for item in doc['items']:
                for it_t_data in item.get('lineaImpuestosDetalle', {}).values():
                    all_tax_names.add(it_t_data['name'])
        
        tax_names = sorted(list(all_tax_names))
        extra_list = sorted(list(all_extra_fields))
            
        # Configurar columnas visibles
        visible_keys = [key for key, _, _ in self.columns_config if self.col_vars[key].get()]
        visible_labels = [label for key, label, _ in self.columns_config if self.col_vars[key].get()]
        
        final_cols = []
        final_labels = []
        
        item_keys = ['lineId', 'descripcion', 'cantidad', 'unidadMedida', 'precioUnitario', 'lineaBase', 'lineaImpuestos', 'marca', 'modelo', 'codigoEstandar']
        is_summary = self.detail_var.get() == "summary"

        for key, label in zip(visible_keys, visible_labels):
            if is_summary and key in item_keys:
                continue
            final_cols.append(key)
            final_labels.append(label)
            
            # Inyectar desglose de impuestos agrupados por Nombre
            if key == 'totalImpuestos' or key == 'lineaImpuestos':
                for t_name in tax_names:
                    col_val = f"tax_val_{t_name}"
                    col_rate = f"tax_rate_{t_name}"
                    
                    if col_val not in final_cols:
                        final_cols.append(col_val)
                        final_labels.append(f"{t_name} (Valor)")
                        final_cols.append(col_rate)
                        final_labels.append(f"{t_name} %")

        # Inyectar campos sectoriales al final si existen
        for extra in extra_list:
            final_cols.append(extra)
            final_labels.append(extra.replace('_', ' '))

        self.tree["columns"] = final_cols
        self.tree["show"] = "headings"
        
        for col, label in zip(final_cols, final_labels):
            self.tree.heading(col, text=label)
            self.tree.column(col, width=110, anchor="center")

        # Insertar datos
        for doc in self.documents:
            if is_summary:
                row = []
                for col in final_cols:
                    if col.startswith("tax_val_"):
                        t_name = col[8:]
                        # Sumar todos los montos para este nombre de impuesto
                        total_tax_val = sum(t['amount'] for t in doc.get('impuestosDesglose', {}).values() if t['name'] == t_name)
                        row.append(total_tax_val)
                    elif col.startswith("tax_rate_"):
                        t_name = col[9:]
                        # Consolidar todas las tasas aplicadas
                        rates = sorted(list(set(t['rate'] for t in doc.get('impuestosDesglose', {}).values() if t['name'] == t_name)))
                        row.append(", ".join(rates))
                    elif col in doc:
                        row.append(doc[col])
                    else:
                        row.append("")
                self.tree.insert("", "end", values=row)
            else:
                for item in doc['items']:
                    row = []
                    for col in final_cols:
                        if col.startswith("tax_val_"):
                            t_name = col[8:]
                            # Valor en la línea
                            it_tax_val = sum(t['amount'] for t in item.get('lineaImpuestosDetalle', {}).values() if t['name'] == t_name)
                            row.append(it_tax_val)
                        elif col.startswith("tax_rate_"):
                            t_name = col[9:]
                            it_rates = sorted(list(set(t['rate'] for t in item.get('lineaImpuestosDetalle', {}).values() if t['name'] == t_name)))
                            row.append(", ".join(it_rates))
                        elif col in item:
                            row.append(item[col])
                        elif col in doc:
                            row.append(doc[col])
                        else:
                            row.append("")
                    self.tree.insert("", "end", values=row)

    def export_excel(self):
        if not self.documents:
            messagebox.showerror("Error", "No hay datos para exportar.")
            return

        save_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not save_path:
            return

        try:
            # Determinar todos los nombres de impuestos y campos sectoriales presentes
            all_tax_names = set()
            all_extra_fields = set()
            for doc in self.documents:
                for t_data in doc.get('impuestosDesglose', {}).values():
                    all_tax_names.add(t_data['name'])
                for key in doc.keys():
                    if key.startswith(('Salud_', 'Transporte_')):
                        all_extra_fields.add(key)
                for item in doc['items']:
                    for it_t_data in item.get('lineaImpuestosDetalle', {}).values():
                        all_tax_names.add(it_t_data['name'])
            
            tax_names = sorted(list(all_tax_names))
            extra_list = sorted(list(all_extra_fields))

            rows = []
            is_item_mode = self.detail_var.get() == "items"
            visible_keys = [key for key, _, _ in self.columns_config if self.col_vars[key].get()]
            column_labels = {key: label for key, label, _ in self.columns_config}
            item_keys = ['lineId', 'descripcion', 'cantidad', 'unidadMedida', 'precioUnitario', 'lineaBase', 'lineaImpuestos', 'marca', 'modelo', 'codigoEstandar']

            for doc in self.documents:
                if is_item_mode:
                    for item in doc['items']:
                        row = {}
                        for key in visible_keys:
                            val = item.get(key, doc.get(key, ""))
                            row[column_labels.get(key, key)] = val
                            if key == 'totalImpuestos' or key == 'lineaImpuestos':
                                for t_name in tax_names:
                                    it_val = sum(t['amount'] for t in item.get('lineaImpuestosDetalle', {}).values() if t['name'] == t_name)
                                    it_rates = sorted(list(set(t['rate'] for t in item.get('lineaImpuestosDetalle', {}).values() if t['name'] == t_name)))
                                    row[f"{t_name} (Valor)"] = it_val
                                    row[f"{t_name} %"] = ", ".join(it_rates)
                        for extra in extra_list:
                            row[extra.replace('_', ' ')] = doc.get(extra, "")
                        rows.append(row)
                else:
                    row = {}
                    for key in visible_keys:
                        if key not in item_keys:
                            val = doc.get(key, "")
                            row[column_labels.get(key, key)] = val
                            if key == 'totalImpuestos':
                                for t_name in tax_names:
                                    total_val = sum(t['amount'] for t in doc.get('impuestosDesglose', {}).values() if t['name'] == t_name)
                                    rates = sorted(list(set(t['rate'] for t in doc.get('impuestosDesglose', {}).values() if t['name'] == t_name)))
                                    row[f"{t_name} (Valor)"] = total_val
                                    row[f"{t_name} %"] = ", ".join(rates)
                    for extra in extra_list:
                        row[extra.replace('_', ' ')] = doc.get(extra, "")
                    rows.append(row)

            df = pd.DataFrame(rows)
            
            if self.group_var.get():
                with pd.ExcelWriter(save_path) as writer:
                    tipo_doc_label = column_labels.get('tipoDocLabel', 'Tipo Doc')
                    if tipo_doc_label in df.columns:
                        for doc_type in df[tipo_doc_label].unique():
                            type_df = df[df[tipo_doc_label] == doc_type]
                            sheet_name = str(doc_type)[:31].replace('[', '').replace(']', '').replace('*', '').replace(':', '').replace('?', '').replace('/', '').replace('\\', '')
                            type_df.to_excel(writer, sheet_name=sheet_name or "Hoja", index=False)
                    else:
                        df.to_excel(writer, sheet_name="Resultados", index=False)
            else:
                df.to_excel(save_path, index=False)

            messagebox.showinfo("Éxito", "Archivo exportado correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al exportar: {e}")

if __name__ == "__main__":
    app = SuperFacturasApp()
    app.mainloop()
