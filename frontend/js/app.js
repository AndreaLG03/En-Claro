/**
 * Autidictionary - Frontend Logic
 */

const app = {
    // Determine Backend Base URL
    // If running on localhost but NOT port 8000, assume backend is on 8000
    getBackendUrl: () => {
        const hostname = window.location.hostname;
        const port = window.location.port;

        // Production (Render, etc) or Local Backend Server
        // If we are serving from the backend directly, use relative path (empty string)
        // This allows the browser to resolve /api relative to current origin
        if (port === '8000' || (!['localhost', '127.0.0.1'].includes(hostname) && hostname !== '')) {
            return window.location.origin;
        }

        // Local Development (Frontend separate from Backend)
        // If we are on localhost but NOT port 8000 (e.g. Live Server port 5500 or file://)
        if (['localhost', '127.0.0.1'].includes(hostname)) {
            return `http://127.0.0.1:8000`;
        }

        // Fallback
        return window.location.origin;
    },

    // API URL dynamically resolved
    get apiUrl() {
        const url = `${this.getBackendUrl()}/api`;
        console.log('DEBUG: API URL:', url);
        return url;
    },

    // Base URL for connectivity checks
    get baseUrl() {
        return this.getBackendUrl();
    },

    // Localization State
    currentLanguage: 'es',

    translations: {
        es: {
            title: 'En Claro',
            subtitle: 'Inspirada en la experiencia neurodivergente',
            welcome: '¡Bienvenido a En Claro!',
            onboarding_title: 'Bienvenido a En Claro',
            onboarding_slogan: 'Tu apoyo para navegar el mundo social con claridad.',
            btn_start: 'Comenzar ahora',
            btn_home: 'Volver al inicio',
            nav_message: 'Entender un mensaje',
            nav_audio: 'Analizar audio',
            nav_glossary: 'Explicar una frase',
            nav_response: 'Ayuda para responder',
            nav_routine: 'Organizar mi día',
            nav_roleplay: 'Simulador Social',
            nav_history: 'Historial',
            settings_welcome: 'Bienvenido a En Claro',
            settings_lang: 'English (Change)',
            settings_account: 'Mi Cuenta',
            profile_title: 'Mi Cuenta',
            profile_desc: 'Personaliza tu experiencia en En Claro.',
            profile_name: 'Nombre:',
            profile_surname: 'Apellidos:',
            profile_email: 'Email:',
            profile_save: 'Guardar Cambios',
            profile_cancel: 'Cancelar',
            google_connect: 'Conectar con Google'
        },
        en: {
            title: 'In Plain Sight',
            subtitle: 'Inspired by the neurodivergent experience',
            welcome: 'Welcome to En Claro!',
            onboarding_title: 'Welcome to En Claro',
            onboarding_slogan: 'Your support to navigate the social world with clarity.',
            btn_start: 'Start now',
            btn_home: 'Go back home',
            nav_message: 'Understand a message',
            nav_audio: 'Analyze audio',
            nav_glossary: 'Explain a phrase',
            nav_response: 'Help to respond',
            nav_routine: 'Organize my day',
            nav_roleplay: 'Social Simulator',
            nav_history: 'History',
            settings_welcome: 'Welcome to En Claro',
            settings_lang: 'Español (Cambiar)',
            settings_account: 'My Account',
            profile_title: 'My Account',
            profile_desc: 'Customize your En Claro experience.',
            profile_name: 'First Name:',
            profile_surname: 'Last Name:',
            profile_email: 'Email:',
            profile_save: 'Save Changes',
            profile_cancel: 'Cancel',
            google_connect: 'Connect with Google'
        }
    },

    /**
     * Navigation: Hide all screens and show the requested one
     */
    showScreen: (screenId) => {
        // Stop any ongoing speech when switching screens
        if (window.speechSynthesis) {
            window.speechSynthesis.cancel();
        }

        // Hide settings menu if open
        const menu = document.getElementById('settings-menu');
        if (menu) menu.style.display = 'none';

        document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
        const target = document.getElementById(`screen-${screenId}`);
        if (target) {
            target.classList.add('active');
            window.scrollTo(0, 0);

            // Special logic for history screen
            if (screenId === 'history') {
                app.loadHistory();
            }

            // Re-initialize Lucide icons for the new screen
            if (window.lucide) {
                lucide.createIcons();
            }
        }
    },

    /**
     * Check if backend is alive
     */
    checkBackendStatus: async () => {
        const dot = document.getElementById('status-dot');
        const text = document.getElementById('status-text');

        if (window.location.protocol === 'file:') {
            dot.style.background = 'var(--warning-color)';
            text.textContent = 'Abre la app vía URL (no archivo local)';
            console.error('App opened as local file. Backend access will fail.');
            return;
        }

        try {
            const resp = await fetch(app.baseUrl);
            if (resp.ok) {
                dot.style.background = 'var(--success-color)';
                text.textContent = 'Conectado';
            } else {
                throw new Error(`Server returned ${resp.status}`);
            }
        } catch (e) {
            dot.style.background = 'var(--error-color)';
            text.textContent = 'Desconectado';
            console.error('Connection failed:', e);
        }
    },

    /**
     * Show a temporary notification (Toast)
     */
    showToast: (message, type = 'info') => {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.position = 'fixed';
            container.style.bottom = '20px';
            container.style.left = '50%';
            container.style.transform = 'translateX(-50%)';
            container.style.zIndex = '1000';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.padding = '12px 24px';
        toast.style.borderRadius = '30px';
        toast.style.color = 'white';
        toast.style.marginBottom = '10px';
        toast.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        toast.style.animation = 'scaleIn 0.3s ease-out';
        toast.style.fontWeight = '600';
        toast.style.background = type === 'error' ? 'var(--error-color)' : 'var(--primary-gradient)';

        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transition = 'all 0.4s ease';
            setTimeout(() => toast.remove(), 400);
        }, 3000);
    },

    /**
     * Generic analysis caller with enhanced error handling
     */
    analyze: async (module, forcedInputId = null) => {
        const inputId = forcedInputId || `${module}-input`;
        const inputEl = document.getElementById(inputId);
        const text = inputEl ? inputEl.value : '';

        if (!navigator.onLine) {
            app.showToast('No tienes conexión a internet. Por favor, comprueba tu red.', 'error');
            return;
        }

        if (!text.trim()) {
            app.showToast('Por favor, escribe algo para analizar.', 'error');
            return;
        }

        let finalText = text;
        if (module === 'routine') {
            const battery = document.getElementById('social-battery-value').value;
            finalText = `[Batería Social: ${battery}%]\n${text}`;
        }

        app.showScreen('loading');

        // Show skeleton in result card if it's already visible or about to be
        const skeleton = document.getElementById('result-skeleton');
        const resultContent = document.getElementById('result-text');
        if (skeleton) skeleton.style.display = 'block';
        if (resultContent) resultContent.style.display = 'none';

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 90000); // 90 seconds

            const response = await fetch(`${app.apiUrl}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    text: finalText,
                    module: module
                }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!response.ok) {
                let errorDetails = `Error ${response.status}`;
                try {
                    const contentType = response.headers.get("content-type");
                    if (contentType && contentType.includes("application/json")) {
                        const errData = await response.json();
                        errorDetails = errData.detail || errorDetails;
                    } else {
                        const textError = await response.text();
                        errorDetails = textError.substring(0, 150) || errorDetails;
                    }
                } catch (pe) {
                    console.error('Error parsing error response:', pe);
                }
                throw new Error(errorDetails);
            }

            const data = await response.json();
            if (!data || !data.result) {
                throw new Error("El servidor devolvió una respuesta vacía.");
            }

            // Save to history before displaying
            app.saveToHistory(module, text, data.result);

            // Small delay to ensure loading screen is visible enough
            setTimeout(() => {
                app.displayResult(data.result, module);
            }, 300);
        } catch (error) {
            console.error('Analysis failed:', error);
            let displayMsg = error.message;
            if (error.name === 'AbortError') {
                displayMsg = "La solicitud tardó demasiado tiempo. Por favor, intenta de nuevo.";
            } else if (error.message.includes('Failed to fetch')) {
                displayMsg = "No se pudo conectar con el servidor. ¿Está el backend encendido?";
            }

            document.getElementById('error-message').textContent = displayMsg;
            app.showScreen('error');
        }
    },

    /**
     * History Management
     */
    saveToHistory: (module, input, result) => {
        try {
            const history = JSON.parse(localStorage.getItem('enclaro_history') || '[]');
            const newItem = {
                id: Date.now(),
                module,
                input,
                result,
                date: new Date().toLocaleString()
            };
            history.unshift(newItem);
            localStorage.setItem('enclaro_history', JSON.stringify(history.slice(0, 20)));
        } catch (e) {
            console.error('Failed to save history:', e);
        }
    },

    loadHistory: () => {
        const historyList = document.getElementById('history-list');
        if (!historyList) return;

        const history = JSON.parse(localStorage.getItem('enclaro_history') || '[]');

        if (history.length === 0) {
            historyList.innerHTML = '<div class="card" style="text-align:center;"><p>No tienes análisis guardados todavía.</p></div>';
            return;
        }

        historyList.innerHTML = history.map(item => `
            <div class="card history-item" style="cursor:pointer;" onclick="app.displayResult('${item.result.replace(/'/g, "\\'").replace(/\n/g, "\\n").replace(/\r/g, "")}', '${item.module}')">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <span class="badge" style="background:var(--grad-${item.module}); color:white; padding:2px 8px; border-radius:12px; font-size:0.75rem; font-weight:700;">${app.getModuleLabel(item.module)}</span>
                    <small style="color:var(--text-muted);">${item.date}</small>
                </div>
                <p style="font-size:0.9rem; color:var(--text-color); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">
                    "${item.input.substring(0, 60)}${item.input.length > 60 ? '...' : ''}"
                </p>
            </div>
        `).join('');

        if (window.lucide) lucide.createIcons();
    },

    getModuleLabel: (module) => {
        const labels = {
            message: 'Mensaje',
            audio: 'Audio',
            glossary: 'Frase',
            response: 'Respuesta',
            routine: 'Rutina',
            decoder: 'Subtexto',
            roleplay: 'Simulacro',
            translator: 'Traducción'
        };
        return labels[module] || module;
    },

    clearHistory: () => {
        if (confirm('¿Estás seguro de que quieres borrar todo el historial?')) {
            localStorage.removeItem('enclaro_history');
            app.loadHistory();
        }
    },

    /**
     * Transcription Logic
     */
    recognition: null,
    isRecording: false,

    toggleRecording: (context = 'audio') => {
        const btnId = `btn-record${context === 'routine' ? '-routine' : ''}`;
        const statusId = `transcription-status${context === 'routine' ? '-routine' : ''}`;
        const inputId = `${context}-input`;

        const btn = document.getElementById(btnId);
        const status = document.getElementById(statusId);
        const input = document.getElementById(inputId);

        if (!app.recognition) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            if (!SpeechRecognition) {
                app.showToast('Tu navegador no soporta transcripción de voz.', 'error');
                return;
            }
            app.recognition = new SpeechRecognition();
            app.recognition.lang = 'es-ES';
            app.recognition.continuous = true;
            app.recognition.interimResults = true;

            app.recognition.onresult = (event) => {
                let finalTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    }
                }
                // We need to ensure we use the current input element
                const currentInput = document.getElementById(app.recognition.targetInputId);
                if (finalTranscript && currentInput) {
                    currentInput.value += (currentInput.value ? ' ' : '') + finalTranscript;
                }
            };

            app.recognition.onend = () => {
                app.isRecording = false;
                const activeBtn = document.getElementById(app.recognition.targetBtnId);
                const activeStatus = document.getElementById(app.recognition.targetStatusId);

                if (activeBtn) {
                    activeBtn.innerHTML = `<i data-lucide="mic"></i> Grabar Voz`;
                    activeBtn.classList.remove('btn-primary');
                }
                if (activeStatus) activeStatus.style.display = 'none';
                app.stopWaveform();
                if (window.lucide) lucide.createIcons();
            };

            app.recognition.onerror = (e) => {
                console.error('Speech Recognition Error:', e);
                app.showToast('Error en la grabación.', 'error');
            };
        }

        if (app.isRecording) {
            app.recognition.stop();
        } else {
            app.recognition.targetInputId = inputId;
            app.recognition.targetBtnId = btnId;
            app.recognition.targetStatusId = statusId;

            app.recognition.start();
            app.isRecording = true;
            btn.innerHTML = '🛑 Detener';
            btn.classList.add('btn-primary');
            status.style.display = 'block';
            app.startWaveform();
        }
    },

    startWaveform: () => {
        const status = document.getElementById('transcription-status');
        const container = document.createElement('div');
        container.id = 'waveform-container';
        container.style.display = 'flex';
        container.style.justifyContent = 'center';
        container.style.alignItems = 'flex-end';
        container.style.gap = '3px';
        container.style.height = '30px';
        container.style.margin = '10px 0';

        for (let i = 0; i < 15; i++) {
            const bar = document.createElement('div');
            bar.className = 'waveform-bar';
            bar.style.width = '4px';
            bar.style.background = 'var(--primary-color)';
            bar.style.borderRadius = '2px';
            bar.style.height = '5px';
            bar.style.animation = `wave-grow ${0.5 + Math.random()}s ease-in-out infinite alternate`;
            container.appendChild(bar);
        }

        // Remove old if exists
        const old = document.getElementById('waveform-container');
        if (old) old.remove();

        status.parentNode.insertBefore(container, status.nextSibling);
    },

    stopWaveform: () => {
        const container = document.getElementById('waveform-container');
        if (container) container.remove();
    },

    handleAudioUpload: (input, context = 'audio') => {
        const file = input.files[0];
        if (!file) return;

        app.showToast('Transcribiendo archivo localmente...', 'info');

        const inputId = `${context}-input`;
        const statusId = `transcription-status${context === 'routine' ? '-routine' : ''}`;

        const audio = new Audio(URL.createObjectURL(file));
        const status = document.getElementById(statusId);
        const textInput = document.getElementById(inputId);

        if (status) {
            status.style.display = 'block';
            status.innerHTML = '<span class="pulse"></span> Transcribiendo archivo...';
        }
        app.startWaveform();

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            app.showToast('Tu navegador no soporta transcripción de voz.', 'error');
            return;
        }

        const fileRec = new SpeechRecognition();
        fileRec.lang = 'es-ES';
        fileRec.onresult = (event) => {
            if (textInput) textInput.value += (textInput.value ? ' ' : '') + event.results[0][0].transcript;
        };

        fileRec.onend = () => {
            if (status) status.style.display = 'none';
            app.stopWaveform();
        };

        audio.onplay = () => fileRec.start();
        audio.onended = () => setTimeout(() => fileRec.stop(), 500);
        audio.play();
    },

    /**
     * Minimal Markdown Parser for AI responses
     */
    renderMarkdown: (text) => {
        if (!text) return '';

        // Preserve code blocks (if any)
        text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');

        // Bold
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

        // Italics
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Inline code
        text = text.replace(/`(.*?)`/g, '<code>$1</code>');

        // Headers (### Header)
        text = text.replace(/^###### (.*$)/gm, '<h6>$1</h6>');
        text = text.replace(/^##### (.*$)/gm, '<h5>$1</h5>');
        text = text.replace(/^#### (.*$)/gm, '<h4>$1</h4>');
        text = text.replace(/^### (.*$)/gm, '<h3>$1</h3>');
        text = text.replace(/^## (.*$)/gm, '<h2>$1</h2>');
        text = text.replace(/^# (.*$)/gm, '<h1>$1</h1>');

        // Unordered lists
        // Handle lines starting with - or *
        const lines = text.split('\n');
        let inList = false;
        const resultLines = [];

        for (let line of lines) {
            const trimmedLine = line.trim();
            if (trimmedLine.startsWith('- ') || trimmedLine.startsWith('* ')) {
                if (!inList) {
                    resultLines.push('<ul>');
                    inList = true;
                }
                resultLines.push(`<li>${trimmedLine.substring(2)}</li>`);
            } else {
                if (inList) {
                    resultLines.push('</ul>');
                    inList = false;
                }
                resultLines.push(line);
            }
        }
        if (inList) resultLines.push('</ul>');

        return resultLines.join('\n').replace(/\n/g, '<br>');
    },

    /**
     * Parse Markdown Tables to HTML (More robust)
     */
    parseMarkdownTable: (text) => {
        const lines = text.trim().split('\n');

        // Find where the table actually starts
        let tableStartIndex = -1;
        for (let i = 0; i < lines.length - 1; i++) {
            if (lines[i].includes('|') && lines[i + 1].includes('|') && lines[i + 1].includes('-')) {
                tableStartIndex = i;
                break;
            }
        }

        if (tableStartIndex === -1) return app.renderMarkdown(text);

        const introText = lines.slice(0, tableStartIndex).join('\n').trim();
        const tableLines = lines.slice(tableStartIndex);

        const html = [];
        if (introText) {
            html.push(app.renderMarkdown(introText));
        }

        html.push('<table>');

        // Header
        const headers = tableLines[0].split('|').filter(c => c.trim() !== '').map(c => `<th>${app.renderMarkdown(c.trim())}</th>`);
        html.push(`<thead><tr>${headers.join('')}</tr></thead>`);

        // Body
        html.push('<tbody>');
        for (let i = 2; i < tableLines.length; i++) {
            if (!tableLines[i].includes('|')) {
                // If the table ends, render the rest as markdown
                if (tableLines[i].trim() !== '') {
                    html.push('</tbody></table>');
                    html.push(app.renderMarkdown(tableLines.slice(i).join('\n')));
                    return html.join('');
                }
                continue;
            }
            const cells = tableLines[i].split('|').filter(c => c.trim() !== '').map(c => `<td>${app.renderMarkdown(c.trim())}</td>`);
            html.push(`<tr>${cells.join('')}</tr>`);
        }
        html.push('</tbody></table>');

        return html.join('');
    },

    /**
     * Parse and display the structured AI response with animations
     */
    displayResult: (rawText, module) => {
        const resultText = document.getElementById('result-text');
        const skeleton = document.getElementById('result-skeleton');

        if (skeleton) skeleton.style.display = 'none';
        if (resultText) {
            resultText.style.display = 'block';
            resultText.innerHTML = '';
        }

        // Robust splitting by numbered sections
        const sections = rawText.split(/\n(?=\d\.)|^(?=\d\.)/gm).filter(s => s.trim() !== '');

        sections.forEach((section, index) => {
            const sectionDiv = document.createElement('div');
            sectionDiv.className = 'result-section';
            sectionDiv.style.opacity = '0';
            sectionDiv.style.transform = 'translateY(10px)';

            const lines = section.trim().split('\n');
            // Strip numbering and any leading hashes from title
            const titleText = lines[0].replace(/^\d+\.\s+/, '').replace(/^#+\s+/, '').trim();

            const title = document.createElement('h3');
            title.textContent = titleText;
            sectionDiv.appendChild(title);

            let bodyContent = lines.slice(1).join('\n').trim();

            // Render table if present and module is routine
            if (module === 'routine' && bodyContent.includes('|')) {
                bodyContent = app.parseMarkdownTable(bodyContent);
            } else {
                // Apply Markdown rendering
                bodyContent = app.renderMarkdown(bodyContent);
            }

            const body = document.createElement('div');
            body.innerHTML = bodyContent;
            sectionDiv.appendChild(body);

            if (resultText) resultText.appendChild(sectionDiv);

            // Copy button for responses
            if (module === 'response' && index >= 2) {
                const copyBtn = document.createElement('button');
                copyBtn.className = 'btn btn-secondary';
                copyBtn.style.marginTop = '12px';
                copyBtn.style.width = 'auto';
                copyBtn.innerHTML = '📋 Copiar respuesta';
                const textToCopy = bodyContent.replace(/<[^>]*>/g, '\n').trim();
                copyBtn.onclick = () => app.copyToClipboard(textToCopy, copyBtn);
                sectionDiv.appendChild(copyBtn);
            }

            setTimeout(() => {
                sectionDiv.style.opacity = '1';
                sectionDiv.style.transform = 'translateY(0)';
            }, index * 100);
        });

        // Contextual buttons
        const actionBtn = document.getElementById('btn-result-action');
        if (module === 'message' || module === 'audio') {
            actionBtn.innerHTML = '<i data-lucide="send"></i> Ayúdame a responder';
            actionBtn.style.display = 'flex';
            actionBtn.onclick = () => {
                document.getElementById('response-input').value = document.getElementById(`${module}-input`).value;
                app.showScreen('response');
            };
        } else {
            actionBtn.style.display = 'none';
        }

        // Re-initialize Lucide icons in results
        if (window.lucide) {
            lucide.createIcons();
        }

        app.showScreen('result');
    },

    copyToClipboard: (text, btn) => {
        navigator.clipboard.writeText(text).then(() => {
            const oldHtml = btn.innerHTML;
            btn.innerHTML = '✅ ¡Copiado!';
            btn.classList.add('copied-feedback');
            setTimeout(() => {
                btn.innerHTML = oldHtml;
                btn.classList.remove('copied-feedback');
            }, 2000);
        });
    },

    /**
     * Roleplay AI Logic
     */
    roleplayHistory: [],
    currentScenario: '',

    startRoleplay: (scenario) => {
        app.currentScenario = scenario;
        app.roleplayHistory = [
            { role: 'system', content: `Escenario: ${scenario}` }
        ];

        document.getElementById('roleplay-selector').style.display = 'none';
        document.getElementById('roleplay-session').style.display = 'block';
        document.getElementById('chat-container').innerHTML = '';
        document.getElementById('roleplay-input').value = '';

        app.showToast(`Iniciando simulación: ${scenario}`, 'info');

        // Trigger AI to start the conversation
        app.sendRoleplayMessage("INICIAR_SESION");
    },

    sendRoleplayMessage: async (customMsg = null) => {
        const input = document.getElementById('roleplay-input');
        const text = customMsg || input.value;

        if (!text.trim()) return;

        if (!customMsg) {
            app.addChatMessage(text, 'user');
            input.value = '';
            app.roleplayHistory.push({ role: 'user', content: text });
        }

        try {
            const response = await fetch(`${app.apiUrl}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: JSON.stringify(app.roleplayHistory),
                    module: 'roleplay'
                })
            });

            if (!response.ok) throw new Error('Error en el simulador');

            const data = await response.json();
            app.addChatMessage(data.result, 'ai');
            app.roleplayHistory.push({ role: 'assistant', content: data.result });

        } catch (error) {
            app.showToast('No se pudo conectar con el simulador.', 'error');
        }
    },

    addChatMessage: (text, sender) => {
        const container = document.getElementById('chat-container');
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble bubble-${sender}`;
        bubble.textContent = text;
        container.appendChild(bubble);
        container.scrollTop = container.scrollHeight;

        // Speak if it's the AI
        if (sender === 'ai') {
            app.speak(text);
        }
    },

    /**
     * Text-to-Speech Helper with Natural Voice Selection
     */
    speak: (text) => {
        if (!window.speechSynthesis) return;

        // Stop any current speech
        window.speechSynthesis.cancel();

        const utterance = new SpeechSynthesisUtterance(text);

        // Match language to app setting
        const langCode = app.currentLanguage === 'es' ? 'es-ES' : 'en-US';
        utterance.lang = langCode;

        // Natural prosody adjustments
        utterance.rate = 0.95; // Slightly slower for better clarity
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        // Intelligent voice selection
        const voices = window.speechSynthesis.getVoices();

        // Filter voices for the current language
        const availableVoices = voices.filter(v => v.lang.startsWith(app.currentLanguage));

        // Prefer "Natural", "Google", or "Microsoft" high-quality voices
        let bestVoice = availableVoices.find(v => v.name.includes('Natural')) ||
            availableVoices.find(v => v.name.includes('Google')) ||
            availableVoices.find(v => v.name.includes('Microsoft')) ||
            availableVoices[0]; // Fallback to first available for that lang

        if (bestVoice) {
            utterance.voice = bestVoice;
        }

        window.speechSynthesis.speak(utterance);
    },

    endRoleplay: async () => {
        app.showScreen('loading');
        document.getElementById('loading-text').textContent = 'Generando feedback constructivo...';

        try {
            const transcript = app.roleplayHistory
                .filter(m => m.role !== 'system')
                .map(m => `${m.role === 'user' ? 'Tú' : 'IA'}: ${m.content}`)
                .join('\n');

            const response = await fetch(`${app.apiUrl}/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: transcript,
                    module: 'roleplay_feedback'
                })
            });

            if (!response.ok) throw new Error('Error feedback');

            const data = await response.json();
            app.displayResult(data.result, 'roleplay');

            // Re-show selector for next time
            document.getElementById('roleplay-selector').style.display = 'block';
            document.getElementById('roleplay-session').style.display = 'none';

        } catch (e) {
            app.showScreen('dashboard');
            app.showToast('Error al generar feedback.', 'error');
            document.getElementById('roleplay-selector').style.display = 'block';
            document.getElementById('roleplay-session').style.display = 'none';
        }
    },

    setSocialBattery: (value) => {
        const input = document.getElementById('social-battery-value');
        if (input) input.value = value;

        // Update UI classes
        const options = document.querySelectorAll('.battery-option');
        options.forEach(opt => {
            if (parseInt(opt.getAttribute('data-value')) === value) {
                opt.classList.add('active');
            } else {
                opt.classList.remove('active');
            }
        });

        app.showToast(`Energía ajustada al ${value}%`, 'info');
    },

    completeOnboarding: () => {
        localStorage.setItem('enclaro_onboarding_complete', 'true');
        app.showScreen('dashboard');
        app.showToast('¡Bienvenido a En Claro!', 'success');
    },

    resetOnboarding: () => {
        localStorage.removeItem('enclaro_onboarding_complete');
        app.showScreen('onboarding');
        app.showToast('Bienvenida reiniciada.', 'info');
        if (document.getElementById('settings-menu')) {
            document.getElementById('settings-menu').style.display = 'none';
        }
    },

    toggleSettings: () => {
        const menu = document.getElementById('settings-menu');
        if (menu) {
            menu.style.display = menu.style.display === 'none' ? 'flex' : 'none';
        }
    },

    toggleLanguage: () => {
        app.currentLanguage = app.currentLanguage === 'es' ? 'en' : 'es';
        localStorage.setItem('enclaro_lang', app.currentLanguage);
        app.updateUI();
        app.showToast(app.currentLanguage === 'es' ? 'Lenguaje cambiado a Español' : 'Language changed to English', 'success');
        app.toggleSettings();
    },

    updateUI: () => {
        const t = app.translations[app.currentLanguage];

        // Comprehensive map of all i18n IDs to translation keys
        const elements = {
            'i18n-title': 'title',
            'i18n-subtitle': 'subtitle',
            'i18n-onboarding-title': 'onboarding_title',
            'i18n-onboarding-slogan': 'onboarding_slogan',
            'i18n-btn-start': 'btn_start',
            'i18n-nav-message': 'nav_message',
            'i18n-nav-audio': 'nav_audio',
            'i18n-nav-glossary': 'nav_glossary',
            'i18n-nav-response': 'nav_response',
            'i18n-nav-routine': 'nav_routine',
            'i18n-nav-roleplay': 'nav_roleplay',
            'i18n-nav-history': 'nav_history',
            'lang-toggle-text': 'settings_lang'
        };

        for (const [id, key] of Object.entries(elements)) {
            const el = document.getElementById(id);
            if (el) {
                // If the element is a button that might contain an icon
                if (el.tagName === 'BUTTON') {
                    // Try to find the icon (either <i> or <svg> from Lucide)
                    const icon = el.querySelector('i, svg');
                    const text = t[key] || '';

                    // Clear the button but preserve the icon if it exists
                    if (icon) {
                        // Keep a reference to the icon element
                        const iconClone = icon.cloneNode(true);
                        el.innerHTML = '';
                        el.textContent = text + ' ';
                        el.appendChild(iconClone);
                    } else {
                        el.textContent = text;
                    }
                } else {
                    // Standard text element
                    el.textContent = t[key] || '';
                }
            }
        }

        // Handle profile labels specifically
        const profTitle = document.querySelector('#screen-profile h1');
        if (profTitle) profTitle.textContent = t.profile_title;

        const profDesc = document.querySelector('#screen-profile header p');
        if (profDesc) profDesc.textContent = t.profile_desc;

        // Finalize icons (one single call)
        if (window.lucide) {
            lucide.createIcons();
        }
    },

    toggleAvatarPicker: () => {
        const picker = document.getElementById('avatar-picker');
        if (picker) {
            picker.style.display = picker.style.display === 'none' ? 'grid' : 'none';
        }
    },

    selectAvatar: (emoji) => {
        const avatarDisplay = document.getElementById('current-avatar');
        if (avatarDisplay) {
            avatarDisplay.textContent = emoji;
        }
        app.toggleAvatarPicker();
    },

    connectGoogle: () => {
        // Redirect to backend auth endpoint
        window.location.href = `${app.apiUrl.replace('/api', '')}/auth/login`;
    },

    saveProfile: () => {
        const name = document.getElementById('profile-name').value;
        const surname = document.getElementById('profile-surname').value;
        const email = document.getElementById('profile-email').value;
        const avatar = document.getElementById('current-avatar').textContent;

        const profile = { name, surname, email, avatar };
        localStorage.setItem('enclaro_profile', JSON.stringify(profile));

        app.showToast(app.currentLanguage === 'es' ? 'Perfil guardado con éxito' : 'Profile saved successfully', 'success');
        app.showScreen('dashboard');
    },

    loadProfile: () => {
        // Load Language
        const savedLang = localStorage.getItem('enclaro_lang');
        if (savedLang) {
            app.currentLanguage = savedLang;
            app.updateUI();
        }

        // Load Profile
        const savedProfile = localStorage.getItem('enclaro_profile');
        if (savedProfile) {
            const profile = JSON.parse(savedProfile);
            if (document.getElementById('profile-name')) document.getElementById('profile-name').value = profile.name || '';
            if (document.getElementById('profile-surname')) document.getElementById('profile-surname').value = profile.surname || '';
            if (document.getElementById('profile-email')) document.getElementById('profile-email').value = profile.email || '';
            if (document.getElementById('current-avatar')) document.getElementById('current-avatar').textContent = profile.avatar || '👤';
        }
    },

    checkAuth: async () => {
        try {
            const response = await fetch(`${app.apiUrl.replace('/api', '')}/auth/me`);
            if (response.ok) {
                const user = await response.json();
                if (user) {
                    // Update profile UI
                    if (document.getElementById('profile-name')) document.getElementById('profile-name').value = user.name || '';
                    if (document.getElementById('profile-email')) document.getElementById('profile-email').value = user.email || '';
                    if (document.getElementById('current-avatar')) document.getElementById('current-avatar').textContent = user.picture ? '🖼️' : '👤'; // Simple indicator

                    // Specific logic for Google Avatar if available
                    if (user.picture) {
                        const avatarEl = document.getElementById('current-avatar');
                        if (avatarEl) {
                            avatarEl.innerHTML = `<img src="${user.picture}" style="width:100%; height:100%; object-fit:cover; border-radius:50%;">`;
                        }
                    }

                    // Save to local storage for persistence handling in UI
                    localStorage.setItem('enclaro_profile', JSON.stringify({
                        name: user.name,
                        email: user.email,
                        avatar: user.picture || '👤'
                    }));
                }
            }
        } catch (e) {
            console.log('Not logged in or auth check failed', e);
        }
    },

    currentRegAvatar: '👤',

    selectRegAvatar: (avatar) => {
        app.currentRegAvatar = avatar;
        document.getElementById('reg-avatar-display').textContent = avatar;
    },

    completeRegistration: () => {
        const name = document.getElementById('reg-name').value.trim();
        const surname = document.getElementById('reg-surname').value.trim();
        const gender = document.getElementById('reg-gender').value;

        if (!name || !gender) {
            app.showToast('Por favor, introduce tu nombre y selecciona un género.', 'error');
            return;
        }

        const profile = {
            name: name,
            surname: surname,
            gender: gender,
            avatar: app.currentRegAvatar
        };

        localStorage.setItem('enclaro_profile', JSON.stringify(profile));
        app.updatePersonalizedText(profile);
        app.showScreen('onboarding');
        app.showToast('¡Perfil creado con éxito!', 'success');
    },

    updatePersonalizedText: (profile) => {
        if (!profile) return;

        // Welcome Text Logic
        let welcomeWord = 'Bienvenido';
        if (profile.gender === 'femenino') welcomeWord = 'Bienvenida';
        else if (profile.gender === 'nobinario' || profile.gender === 'otro') welcomeWord = 'Bienvenide';

        const welcomeText = `${welcomeWord} a En Claro`;

        // Update Dashboard Welcome (Settings Menu)
        // Note: The settings menu button text might need an ID or strictly targeting
        const settingsWelcome = document.querySelector('#settings-menu button:first-child span');
        if (settingsWelcome) settingsWelcome.textContent = welcomeText;

        // Update Onboarding Title
        const onboardingTitle = document.getElementById('i18n-onboarding-title');
        if (onboardingTitle) onboardingTitle.textContent = welcomeText;

        // Update Dashboard Prompt
        // "Qué quieres hacer ahora, [Nombre]?"
        // We need to target the paragraph element in dashboard header. 
        // It currently has no ID, let's add logic to find it or standardise it.
        // The Prompt is the 3rd child of header: h1, p (subtitle), p (prompt)
        const dashboardHeader = document.querySelector('#screen-dashboard header');
        if (dashboardHeader) {
            const promptPara = dashboardHeader.querySelectorAll('p')[1]; // 2nd paragraph
            if (promptPara) {
                promptPara.textContent = `¿Qué quieres hacer ahora, ${profile.name}?`;
            }
        }
    },

    // ... existing functions ...
};

document.addEventListener('DOMContentLoaded', () => {
    // ... existing URL param logic ...

    const profileData = localStorage.getItem('enclaro_profile');
    if (profileData) {
        const profile = JSON.parse(profileData);
        app.updatePersonalizedText(profile);
        // Always show onboarding as requested previously
        app.showScreen('onboarding');
    } else {
        // No profile, show registration
        app.showScreen('registration');
    }

    app.loadProfile();
    app.checkAuth();
    app.checkBackendStatus();
});
