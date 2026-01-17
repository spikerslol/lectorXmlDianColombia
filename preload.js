const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
    selectFolder: () => ipcRenderer.invoke('select-folder'),
    readFiles: (folderPath) => ipcRenderer.invoke('read-files', folderPath),
    saveExcel: (data) => ipcRenderer.invoke('save-excel', data),
});
