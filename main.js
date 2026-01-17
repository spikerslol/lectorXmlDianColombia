const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const isDev = require('electron-is-dev');
const fs = require('fs');

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    title: 'SuperFacturas - Consolidador DIAN',
    autoHideMenuBar: true,
  });

  win.loadURL(
    isDev
      ? 'http://localhost:5173'
      : `file://${path.join(__dirname, 'dist/index.html')}`
  );
}

app.whenReady().then(() => {
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});

// IPC Handlers
ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openDirectory'],
  });
  return result.filePaths[0];
});

ipcMain.handle('read-files', async (event, folderPath) => {
  try {
    const files = fs.readdirSync(folderPath);
    const xmlFiles = files.filter(f => f.toLowerCase().endsWith('.xml'));
    
    const results = xmlFiles.map(file => {
      const fullPath = path.join(folderPath, file);
      const content = fs.readFileSync(fullPath, 'utf8');
      return { name: file, content };
    });
    
    return results;
  } catch (error) {
    console.error('Error reading files:', error);
    throw error;
  }
});

ipcMain.handle('save-excel', async (event, { buffer, filename }) => {
  const result = await dialog.showSaveDialog({
    defaultPath: filename,
    filters: [{ name: 'Excel Files', extensions: ['xlsx'] }]
  });

  if (!result.canceled && result.filePath) {
    fs.writeFileSync(result.filePath, Buffer.from(buffer));
    return true;
  }
  return false;
});
