import React, { useState, useEffect } from 'react';
import { FolderOpen, Download, Settings, FileText, Check, ChevronRight, LayoutGrid, List } from 'lucide-react';
import { parseDIANXml } from './utils/xmlParser';
import { exportToExcel } from './utils/excelExporter';

const DEFAULT_COLUMNS = [
    { key: 'tipoDoc', label: 'Tipo Documento', enabled: true },
    { key: 'numero', label: 'Número', enabled: true },
    { key: 'fecha', label: 'Fecha', enabled: true },
    { key: 'emisorNit', label: 'NIT Emisor', enabled: true },
    { key: 'emisorNombre', label: 'Nombre Emisor', enabled: true },
    { key: 'receptorNit', label: 'NIT Receptor', enabled: true },
    { key: 'receptorNombre', label: 'Nombre Receptor', enabled: true },
    { key: 'base', label: 'Subtotal/Base', enabled: true },
    { key: 'impuestos', label: 'Impuestos', enabled: true },
    { key: 'total', label: 'Total', enabled: true },
    { key: 'cufe', label: 'CUFE/CUNE', enabled: true },
    { key: 'descripcion', label: 'Ítem: Descripción', enabled: true },
    { key: 'cantidad', label: 'Ítem: Cantidad', enabled: true },
    { key: 'precio', label: 'Ítem: Precio Unit', enabled: true },
    { key: 'baseItem', label: 'Ítem: Base', enabled: true },
];

function App() {
    const [folderPath, setFolderPath] = useState('');
    const [documents, setDocuments] = useState([]);
    const [loading, setLoading] = useState(false);
    const [detailLevel, setDetailLevel] = useState('summary'); // 'summary' or 'items'
    const [groupByType, setGroupByType] = useState(false);
    const [columns, setColumns] = useState(DEFAULT_COLUMNS);

    const handleSelectFolder = async () => {
        const path = await window.electronAPI.selectFolder();
        if (path) {
            setFolderPath(path);
            loadFiles(path);
        }
    };

    const loadFiles = async (path) => {
        setLoading(true);
        try {
            const files = await window.electronAPI.readFiles(path);
            const parsedDocs = [];
            for (const file of files) {
                const parsed = await parseDIANXml(file.content);
                if (parsed) {
                    parsedDocs.push({ ...parsed, fileName: file.name });
                }
            }
            setDocuments(parsedDocs);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async () => {
        if (documents.length === 0) return;

        const buffer = await exportToExcel(documents, {
            detailLevel,
            groupByType,
            columns
        });

        const success = await window.electronAPI.saveExcel({
            buffer,
            filename: `Consolidado_DIAN_${new Date().toISOString().split('T')[0]}.xlsx`
        });

        if (success) {
            alert('¡Exportación exitosa!');
        }
    };

    const toggleColumn = (key) => {
        setColumns(cols => cols.map(c =>
            c.key === key ? { ...c, enabled: !c.enabled } : c
        ));
    };

    return (
        <div className="app-container">
            <header>
                <div className="logo">SuperFacturas</div>
                <div className="header-actions">
                    <button className="btn btn-outline" onClick={handleSelectFolder}>
                        <FolderOpen size={18} />
                        {folderPath ? 'Cambiar Carpeta' : 'Seleccionar Carpeta'}
                    </button>
                </div>
            </header>

            <main>
                {documents.length === 0 && !loading ? (
                    <div className="hero">
                        <h1>Consolidador DIAN</h1>
                        <p>Lee todos tus XML de facturación, notas y nómina en segundos. 100% Privado y Local.</p>
                        <button className="btn btn-primary" onClick={handleSelectFolder}>
                            <FolderOpen size={20} />
                            Empezar Seleccionando Carpeta
                        </button>
                    </div>
                ) : (
                    <div className="dashboard">
                        <aside className="sidebar">
                            <div className="config-section">
                                <h3><Settings size={14} style={{ verticalAlign: 'middle', marginRight: '4px' }} /> Configuración</h3>
                                <div className="option-group">
                                    <label className="option-item">
                                        <input
                                            type="radio"
                                            name="detail"
                                            checked={detailLevel === 'summary'}
                                            onChange={() => setDetailLevel('summary')}
                                        />
                                        <span>Resumen (Totales)</span>
                                    </label>
                                    <label className="option-item">
                                        <input
                                            type="radio"
                                            name="detail"
                                            checked={detailLevel === 'items'}
                                            onChange={() => setDetailLevel('items')}
                                        />
                                        <span>Detalle (Por Ítem)</span>
                                    </label>
                                </div>
                            </div>

                            <div className="config-section">
                                <h3>Opciones de Excel</h3>
                                <div className="option-group">
                                    <label className="option-item">
                                        <input
                                            type="checkbox"
                                            checked={groupByType}
                                            onChange={(e) => setGroupByType(e.target.checked)}
                                        />
                                        <span>Separar por pestañas (Tipo Doc)</span>
                                    </label>
                                </div>
                            </div>

                            <div className="config-section">
                                <h3>Columnas Visibles</h3>
                                <div className="column-list">
                                    {columns.map(col => (
                                        <label key={col.key} className="column-item">
                                            <span>{col.label}</span>
                                            <input
                                                type="checkbox"
                                                checked={col.enabled}
                                                onChange={() => toggleColumn(col.key)}
                                            />
                                        </label>
                                    ))}
                                </div>
                            </div>

                            <button className="btn btn-primary" style={{ width: '100%' }} onClick={handleExport}>
                                <Download size={18} />
                                Exportar Excel
                            </button>
                        </aside>

                        <section className="data-preview">
                            <div className="preview-header">
                                <h2>Vista Previa ({documents.length} documentos)</h2>
                                {loading && <div className="loader"></div>}
                            </div>

                            <div className="table-container">
                                <table>
                                    <thead>
                                        <tr>
                                            {columns.filter(c => c.enabled).map(col => (
                                                <th key={col.key}>{col.label}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {documents.slice(0, 50).map((doc, idx) => (
                                            <React.Fragment key={idx}>
                                                {detailLevel === 'summary' ? (
                                                    <tr>
                                                        {columns.filter(c => c.enabled).map(col => (
                                                            <td key={col.key}>
                                                                {col.key === 'tipoDoc' ? (
                                                                    <span className={`badge badge-${doc.tipoDoc.toLowerCase().replace(' ', '-')}`}>
                                                                        {doc[col.key]}
                                                                    </span>
                                                                ) : doc[col.key]}
                                                            </td>
                                                        ))}
                                                    </tr>
                                                ) : (
                                                    doc.items.map((item, iIdx) => (
                                                        <tr key={`${idx}-${iIdx}`}>
                                                            {columns.filter(c => c.enabled).map(col => (
                                                                <td key={col.key}>
                                                                    {item.hasOwnProperty(col.key) ? item[col.key] : doc[col.key]}
                                                                </td>
                                                            ))}
                                                        </tr>
                                                    ))
                                                )}
                                            </React.Fragment>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </section>
                    </div>
                )}
            </main>
        </div>
    );
}

export default App;
