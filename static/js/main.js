// static/js/main.js

document.addEventListener('DOMContentLoaded', () => {
    const generateButton = document.getElementById('generateButton');
    const viewJsonButton = document.getElementById('viewJsonButton');
    const logOutput = document.getElementById('logOutput');
    const logContainer = document.getElementById('logContainer');
    const statusMessages = document.getElementById('statusMessages');
    const errorMessages = document.getElementById('errorMessages');
    const buttonSpinner = document.getElementById('buttonSpinner');

    // Conecta ao servidor Socket.IO
    const socket = io();

    let isGenerating = false; // Flag para controlar o estado da geração

    // --- Funções Auxiliares ---
    function addLog(message) {
        logOutput.textContent += message + '\n';
        // Auto-scroll para o final
        logContainer.scrollTop = logContainer.scrollHeight;
    }

    function clearLogs() {
        logOutput.textContent = '';
    }

    function showStatus(message) {
        statusMessages.textContent = message;
        statusMessages.style.display = 'block';
        errorMessages.style.display = 'none'; // Esconde erros ao mostrar status
    }

    function showError(message) {
        errorMessages.textContent = 'Erro: ' + message;
        errorMessages.style.display = 'block';
        statusMessages.style.display = 'none'; // Esconde status ao mostrar erro
    }

    function hideMessages() {
        statusMessages.style.display = 'none';
        errorMessages.style.display = 'none';
    }

    function setGeneratingState(generating) {
        isGenerating = generating;
        generateButton.disabled = generating;
        buttonSpinner.style.display = generating ? 'inline-block' : 'none';
        if (!generating) {
            // Se finalizou, mantém mensagem de sucesso ou erro visível
        }
    }

    // --- Event Listeners ---
    generateButton.addEventListener('click', () => {
        if (isGenerating) return; // Previne múltiplos cliques

        setGeneratingState(true);
        clearLogs();
        hideMessages(); // Limpa mensagens anteriores
        viewJsonButton.style.display = 'none'; // Esconde botão de visualizar JSON
        showStatus('Iniciando geração...');
        socket.emit('start_generation', { message: 'Iniciar processo' });
    });

    viewJsonButton.addEventListener('click', () => {
        // Abre a nova rota /teste
        window.open('/teste', '_blank');
    });

    // --- Socket.IO Event Handlers ---
    socket.on('connect', () => {
        addLog('Conectado ao servidor Socket.IO.');
    });

    socket.on('disconnect', () => {
        addLog('Desconectado do servidor Socket.IO.');
        if (isGenerating) {
            showError('Conexão perdida durante a geração.');
            setGeneratingState(false);
        }
    });

    socket.on('log_message', (msg) => {
        addLog(msg.data);
    });

    socket.on('generation_started', () => {
        // Status já foi definido no clique do botão
    });

    socket.on('generation_complete', (msg) => {
        addLog('--- Geração Concluída com Sucesso ---');
        showStatus('Geração concluída com sucesso!');
        viewJsonButton.style.display = 'inline-block'; // Mostra o botão para visualizar
        setGeneratingState(false);
    });

    socket.on('generation_error', (msg) => {
        addLog('--- ERRO DURANTE A GERAÇÃO ---');
        addLog('Erro: ' + msg.error);
        showError(msg.error);
        setGeneratingState(false);
    });

    socket.on('generation_finished', () => {
        // Sinal de término, pode-se desabilitar spinner
        buttonSpinner.style.display = 'none';
    });
});
