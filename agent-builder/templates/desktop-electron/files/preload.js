// The only bridge between the web UI (renderer) and the main process.
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("api", {
  getInfo: () => ipcRenderer.invoke("app:info"),
  saveText: (defaultName, content) => ipcRenderer.invoke("file:save-text", { defaultName, content }),
});
