console.log("DEBUG SCRIPT LOADED SUCCESSFULLY");
window.app = {
    initErrorHandler: () => console.log("Error handler stub"),
    showScreen: () => alert("Estamos en modo diagnóstico. El script principal se ha desactivado para aislar el error."),
};
console.log("DEBUG: window.app attached");
