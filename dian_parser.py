import os
from lxml import etree

def get_tag_value(element, xpath, namespaces):
    try:
        nodes = element.xpath(xpath, namespaces=namespaces)
        if nodes:
            return nodes[0].text
        return ""
    except:
        return ""

def parse_dian_xml(file_path):
    try:
        parser = etree.XMLParser(recover=True, remove_comments=True)
        tree = etree.parse(file_path, parser=parser)
        root = tree.getroot()
        
        # Namespaces
        ns = {
            'cac': "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
            'cbc': "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
            'ext': "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2",
            'sts': "dian:gov:co:facturaelectronica:Structures-2-1"
        }

        tag_name = etree.QName(root).localname
        
        doc_type = "Desconocido"
        if tag_name == "Invoice": doc_type = "Factura"
        elif tag_name == "CreditNote": doc_type = "Nota Crédito"
        elif tag_name == "DebitNote": doc_type = "Nota Débito"
        elif tag_name == "NominaElectronica": doc_type = "Nómina"

        # 1. Cabecera (Header)
        data = {
            'documentType': tag_name,
            'tipoDocLabel': doc_type,
            'ublVersion': get_tag_value(root, "//cbc:UBLVersionID", ns),
            'customizationID': get_tag_value(root, "//cbc:CustomizationID", ns),
            'profileID': get_tag_value(root, "//cbc:ProfileID", ns),
            'profileExecutionID': get_tag_value(root, "//cbc:ProfileExecutionID", ns),
            'numero': get_tag_value(root, "//cbc:ID", ns),
            'cufe': get_tag_value(root, "//cbc:UUID", ns),
            'fechaEmision': get_tag_value(root, "//cbc:IssueDate", ns),
            'horaEmision': get_tag_value(root, "//cbc:IssueTime", ns),
            'fechaVencimiento': get_tag_value(root, "//cbc:DueDate", ns),
            'tipoFactura': get_tag_value(root, "//cbc:InvoiceTypeCode", ns),
            'moneda': get_tag_value(root, "//cbc:DocumentCurrencyCode", ns),
            'notas': get_tag_value(root, "//cbc:Note", ns),
            'lineasCount': get_tag_value(root, "//cbc:LineCountNumeric", ns),
            'fileName': os.path.basename(file_path)
        }

        # 2. Emisor (Supplier/Employer)
        emisor_xpath = "//cac:AccountingSupplierParty/cac:Party" if doc_type != "Nómina" else "//cac:EmployerParty"
        data.update({
            'emisorNit': get_tag_value(root, f"{emisor_xpath}//cbc:CompanyID", ns) or get_tag_value(root, f"{emisor_xpath}//cbc:ID", ns),
            'emisorNombre': get_tag_value(root, f"{emisor_xpath}//cac:PartyName/cbc:Name", ns) or get_tag_value(root, f"{emisor_xpath}//cbc:RegistrationName", ns),
            'emisorRegimen': get_tag_value(root, f"{emisor_xpath}//cbc:TaxLevelCode", ns),
            'emisorCiudad': get_tag_value(root, f"{emisor_xpath}//cbc:CityName", ns),
            'emisorDepto': get_tag_value(root, f"{emisor_xpath}//cbc:CountrySubentity", ns),
            'emisorDireccion': get_tag_value(root, f"{emisor_xpath}//cac:AddressLine/cbc:Line", ns),
            'emisorEmail': get_tag_value(root, f"{emisor_xpath}//cbc:ElectronicMail", ns),
        })

        # 3. Adquiriente (Customer/Employee)
        receptor_xpath = "//cac:AccountingCustomerParty/cac:Party" if doc_type != "Nómina" else "//cac:EmployeeParty"
        data.update({
            'receptorNit': get_tag_value(root, f"{receptor_xpath}//cbc:CompanyID", ns) or get_tag_value(root, f"{receptor_xpath}//cbc:ID", ns),
            'receptorNombre': get_tag_value(root, f"{receptor_xpath}//cac:PartyName/cbc:Name", ns) or get_tag_value(root, f"{receptor_xpath}//cbc:RegistrationName", ns) or \
                              (get_tag_value(root, f"{receptor_xpath}//cbc:FirstName", ns) + " " + get_tag_value(root, f"{receptor_xpath}//cbc:FamilyName", ns) if doc_type == "Nómina" else ""),
            'receptorCiudad': get_tag_value(root, f"{receptor_xpath}//cbc:CityName", ns),
            'receptorDepto': get_tag_value(root, f"{receptor_xpath}//cbc:CountrySubentity", ns),
            'receptorDireccion': get_tag_value(root, f"{receptor_xpath}//cac:AddressLine/cbc:Line", ns),
            'receptorEmail': get_tag_value(root, f"{receptor_xpath}//cbc:ElectronicMail", ns),
        })

        # 4. Pagos (PaymentMeans / PaymentTerms)
        data.update({
            'metodoPago': get_tag_value(root, "//cac:PaymentMeans/cbc:PaymentMeansCode", ns),
            'canalPago': get_tag_value(root, "//cac:PaymentMeans/cbc:ID", ns),
            'fechaLimitePago': get_tag_value(root, "//cac:PaymentMeans/cbc:PaymentDueDate", ns),
        })

        # 5. Totales (MonetaryTotal)
        totals_xpath = "//cac:LegalMonetaryTotal" if doc_type != "Nómina" else "//cac:RequestedMonetaryTotal"
        data.update({
            'totalBruto': float(get_tag_value(root, f"{totals_xpath}/cbc:LineExtensionAmount", ns) or 0),
            'baseImponible': float(get_tag_value(root, f"{totals_xpath}/cbc:TaxExclusiveAmount", ns) or 0),
            'totalIvaInc': float(get_tag_value(root, f"{totals_xpath}/cbc:TaxInclusiveAmount", ns) or 0),
            'totalDescuentos': float(get_tag_value(root, f"{totals_xpath}/cbc:AllowanceTotalAmount", ns) or 0),
            'totalCargos': float(get_tag_value(root, f"{totals_xpath}/cbc:ChargeTotalAmount", ns) or 0),
            'totalAnticipos': float(get_tag_value(root, f"{totals_xpath}/cbc:PrepaidAmount", ns) or 0),
            'totalPagar': float(get_tag_value(root, f"{totals_xpath}/cbc:PayableAmount", ns) or 0),
        })

        # 6. Impuestos Detallados (Global)
        tax_totals = root.xpath("//cac:TaxTotal", namespaces=ns)
        global_taxes = {} # { 'IVA_19.00': {'name': 'IVA', 'rate': '19.00', 'amount': 100}, ... }
        for tax_total in tax_totals:
            if tax_total.getparent().tag.endswith('Line'): continue
            
            subtotals = tax_total.xpath("cac:TaxSubtotal", namespaces=ns)
            for sub in subtotals:
                t_id = get_tag_value(sub, "cac:TaxCategory/cac:TaxScheme/cbc:ID", ns)
                t_name = get_tag_value(sub, "cac:TaxCategory/cac:TaxScheme/cbc:Name", ns) or t_id
                t_percent = get_tag_value(sub, "cac:TaxCategory/cbc:Percent", ns) or "0"
                t_amount = float(get_tag_value(sub, "cbc:TaxAmount", ns) or 0)
                
                # Crear clave única por nombre y tasa
                tax_key = f"{t_name}_{t_percent}"
                if tax_key not in global_taxes:
                    global_taxes[tax_key] = {'name': t_name, 'rate': t_percent, 'amount': 0}
                global_taxes[tax_key]['amount'] += t_amount

        data['impuestosDesglose'] = global_taxes
        data['totalImpuestos'] = sum(t['amount'] for t in global_taxes.values())

        # 7. Información Sectorial (Anexo 1.9 - Salud, Transporte, etc.)
        # Sector Salud (Resolución 2275 - Código 050)
        health_refs = root.xpath("//cac:AdditionalDocumentReference[cbc:DocumentTypeCode='050']", namespaces=ns)
        for ref in health_refs:
            field_code = get_tag_value(ref, "cac:IssuerParty/cac:PartyIdentification/cbc:ID", ns)
            field_val = get_tag_value(ref, "cbc:ID", ns)
            if field_code:
                data[f'Salud_Campo_{field_code}'] = field_val

        # Sector Transporte (Códigos 06 al 09)
        trans_refs = root.xpath("//cac:AdditionalDocumentReference[cbc:DocumentTypeCode='06' or cbc:DocumentTypeCode='07' or cbc:DocumentTypeCode='08' or cbc:DocumentTypeCode='09']", namespaces=ns)
        for ref in trans_refs:
            t_type = get_tag_value(ref, "cbc:DocumentTypeCode", ns)
            t_id = get_tag_value(ref, "cbc:ID", ns)
            label = {'06': 'Manifiesto', '07': 'Remesa', '08': 'DTA', '09': 'OTM'}.get(t_type, t_type)
            data[f'Transporte_{label}'] = t_id

        # 8. Líneas de Detalle (Items)
        items = []
        line_xpath = f"//cac:{tag_name}Line"
        lines = root.xpath(line_xpath, namespaces=ns)
        for line in lines:
            line_taxes = {} # { 'IVA_19.00': {'name': 'IVA', 'rate': '19.00', 'amount': 10}, ... }
            item_tax_totals = line.xpath("cac:TaxTotal", namespaces=ns)
            for it_tax in item_tax_totals:
                it_subtotals = it_tax.xpath("cac:TaxSubtotal", namespaces=ns)
                for it_sub in it_subtotals:
                    it_tax_name = get_tag_value(it_sub, "cac:TaxCategory/cac:TaxScheme/cbc:Name", ns) or \
                                  get_tag_value(it_sub, "cac:TaxCategory/cac:TaxScheme/cbc:ID", ns)
                    it_percent = get_tag_value(it_sub, "cac:TaxCategory/cbc:Percent", ns) or "0"
                    it_tax_amount = float(get_tag_value(it_sub, "cbc:TaxAmount", ns) or 0)
                    
                    it_key = f"{it_tax_name}_{it_percent}"
                    if it_key not in line_taxes:
                        line_taxes[it_key] = {'name': it_tax_name, 'rate': it_percent, 'amount': 0}
                    line_taxes[it_key]['amount'] += it_tax_amount

            items.append({
                'lineId': get_tag_value(line, "cbc:ID", ns),
                'descripcion': get_tag_value(line, "cac:Item/cbc:Description", ns),
                'cantidad': float(get_tag_value(line, "cbc:InvoicedQuantity", ns) or 0),
                'unidadMedida': get_tag_value(line, "cbc:InvoicedQuantity/@unitCode", ns),
                'precioUnitario': float(get_tag_value(line, "cac:Price/cbc:PriceAmount", ns) or 0),
                'lineaBase': float(get_tag_value(line, "cbc:LineExtensionAmount", ns) or 0),
                'lineaImpuestos': sum(t['amount'] for t in line_taxes.values()),
                'lineaImpuestosDetalle': line_taxes,
                'codigoEstandar': get_tag_value(line, "cac:Item/cac:StandardItemIdentification/cbc:ID", ns),
                'marca': get_tag_value(line, "cac:Item/cbc:BrandName", ns),
                'modelo': get_tag_value(line, "cac:Item/cbc:ModelName", ns),
            })
        
        data['items'] = items
        return data

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return None
