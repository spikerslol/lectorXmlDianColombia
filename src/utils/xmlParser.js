import { parseStringPromise } from 'xml2js';

export const parseDIANXml = async (xmlContent) => {
    try {
        const result = await parseStringPromise(xmlContent, {
            explicitArray: false,
            ignoreAttrs: false,
        });

        const rootName = Object.keys(result)[0];
        const root = result[rootName];

        // Determine type
        let type = 'Unknown';
        if (rootName === 'Invoice') type = 'Factura';
        if (rootName === 'CreditNote') type = 'Nota Crédito';
        if (rootName === 'DebitNote') type = 'Nota Débito';
        if (rootName === 'NominaElectronica') type = 'Nómina';

        const getValue = (path, obj = root) => {
            return path.split('.').reduce((acc, part) => acc && acc[part], obj);
        };

        // Extract Header Info
        const header = {
            tipoDoc: type,
            numero: getValue('cbc:ID'),
            fecha: getValue('cbc:IssueDate'),
            hora: getValue('cbc:IssueTime'),
            cufe: getValue('cbc:UUID._') || getValue('cbc:UUID'),
            moneda: getValue('cbc:DocumentCurrencyCode._') || getValue('cbc:DocumentCurrencyCode'),
        };

        // Extract Party Info
        let supplierRaw = getValue('cac:AccountingSupplierParty.cac:Party') || getValue('cac:EmployerParty.cac:Party');
        let customerRaw = getValue('cac:AccountingCustomerParty.cac:Party') || getValue('cac:EmployeeParty.cac:Party');

        const extractParty = (party) => {
            if (!party) return {};
            const nit = getValue('cac:PartyTaxScheme.cbc:CompanyID._', party) ||
                getValue('cac:PartyTaxScheme.cbc:CompanyID', party) ||
                getValue('cac:PartyIdentification.cbc:ID._', party) ||
                getValue('cac:PartyIdentification.cbc:ID', party);
            const name = getValue('cac:PartyName.cbc:Name', party) ||
                getValue('cac:PartyTaxScheme.cbc:RegistrationName', party) ||
                getValue('cac:Person.cbc:FirstName', party) + ' ' + getValue('cac:Person.cbc:FamilyName', party);
            return { nit, name };
        };

        const supplier = extractParty(supplierRaw);
        const customer = extractParty(customerRaw);

        // Extract Totals
        const totalsRaw = getValue('cac:LegalMonetaryTotal') || getValue('cac:RequestedMonetaryTotal');
        const totals = {
            base: parseFloat(getValue('cbc:TaxExclusiveAmount._', totalsRaw) || getValue('cbc:TaxExclusiveAmount', totalsRaw) || 0),
            total: parseFloat(getValue('cbc:PayableAmount._', totalsRaw) || getValue('cbc:PayableAmount', totalsRaw) || 0),
            impuestos: parseFloat(getValue('cac:TaxTotal.cbc:TaxAmount._') || getValue('cac:TaxTotal.cbc:TaxAmount') || 0),
        };

        // Extract Lines
        const linesRaw = getValue('cac:InvoiceLine') || getValue('cac:CreditNoteLine') || getValue('cac:DebitNoteLine') || [];
        const lines = (Array.isArray(linesRaw) ? linesRaw : [linesRaw]).map(line => ({
            id: getValue('cbc:ID', line),
            descripcion: getValue('cac:Item.cbc:Description', line),
            cantidad: parseFloat(getValue('cbc:InvoicedQuantity._', line) || getValue('cbc:InvoicedQuantity', line) || 0),
            precio: parseFloat(getValue('cac:Price.cbc:PriceAmount._', line) || getValue('cac:Price.cbc:PriceAmount', line) || 0),
            baseItem: parseFloat(getValue('cbc:LineExtensionAmount._', line) || getValue('cbc:LineExtensionAmount', line) || 0),
            impuestoItem: parseFloat(getValue('cac:TaxTotal.cbc:TaxAmount._', line) || getValue('cac:TaxTotal.cbc:TaxAmount', line) || 0),
        }));

        return {
            ...header,
            emisorNit: supplier.nit,
            emisorNombre: supplier.name,
            receptorNit: customer.nit,
            receptorNombre: customer.name,
            ...totals,
            items: lines
        };
    } catch (error) {
        console.error('Error parsing XML:', error);
        return null;
    }
};
