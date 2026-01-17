import * as XLSX from 'xlsx';

export const exportToExcel = async (data, config) => {
    const workbook = XLSX.utils.book_new();

    if (config.groupByType) {
        const types = [...new Set(data.map(d => d.tipoDoc))];
        types.forEach(type => {
            const typeData = data.filter(d => d.tipoDoc === type);
            const rows = prepareRows(typeData, config);
            const worksheet = XLSX.utils.json_to_sheet(rows);
            XLSX.utils.book_append_sheet(workbook, worksheet, type.substring(0, 31));
        });
    } else {
        const rows = prepareRows(data, config);
        const worksheet = XLSX.utils.json_to_sheet(rows);
        XLSX.utils.book_append_sheet(workbook, worksheet, "Consolidado");
    }

    const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' });
    return excelBuffer;
};

const prepareRows = (data, config) => {
    const rows = [];

    data.forEach(doc => {
        if (config.detailLevel === 'items') {
            doc.items.forEach(item => {
                const row = {};
                config.columns.forEach(col => {
                    if (col.enabled) {
                        // Map header properties or item properties
                        if (item.hasOwnProperty(col.key)) {
                            row[col.label] = item[col.key];
                        } else {
                            row[col.label] = doc[col.key];
                        }
                    }
                });
                rows.push(row);
            });
        } else {
            const row = {};
            config.columns.forEach(col => {
                if (col.enabled && !['descripcion', 'cantidad', 'precio', 'baseItem', 'impuestoItem'].includes(col.key)) {
                    row[col.label] = doc[col.key];
                }
            });
            rows.push(row);
        }
    });

    return rows;
};
