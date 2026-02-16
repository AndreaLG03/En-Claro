const app = {
    // ... Mock properties from earlier lines to make it valid ...
    recognition: null,
    isRecording: false,
    googleClientId: '106097643504-j883o1a4k5ad28smia4o3sj215k1lqdc.apps.googleusercontent.com',
    tokenClient: null,
    showToast: (msg, type) => console.log(msg, type),

    // Start of the part we are checking (approx line 1330 onwards, but simplified for syntax check)
    // We only care about matching braces from the part we edited.
    // So I will paste the content from my last edit attempt and previous context.

    // ... Context from 1300 ...
    // ...
    // ...

    // Pasting the END of the file from what I see in view_file 424 and 425
    // ...

    // Let's assume lines 1900 onwards are what matters for the syntax error I introduced.

    toggleSettings: () => {
        const menu = document.getElementById('settings-menu');
        if (menu) menu.style.display = menu.style.display === 'none' ? 'flex' : 'none';
    },

    toggleAvatarPicker: () => {
        const picker = document.getElementById('avatar-picker');
        if (picker) picker.style.display = picker.style.display === 'none' ? 'grid' : 'none';
    },

    selectAvatar: (avatar) => {
        const display = document.getElementById('current-avatar');
        if (display) display.textContent = avatar;
        app.tempProfileAvatar = avatar;
        app.toggleAvatarPicker();
    },

    saveProfile: () => {
        const name = document.getElementById('profile-name').value;
        const surname = document.getElementById('profile-surname').value;
        const gender = document.getElementById('profile-gender').value;
        const email = document.getElementById('profile-email').value;

        const display = document.getElementById('current-avatar');
        const avatar = app.tempProfileAvatar || (display ? display.textContent : '🤖');

        const profile = { name, surname, gender, email, avatar };
        localStorage.setItem('enclaro_profile', JSON.stringify(profile));

        app.updatePersonalizedText(profile);
        app.showToast('Perfil actualizado', 'success');
    },

    loadProfile: () => {
        const profile = JSON.parse(localStorage.getItem('enclaro_profile') || '{}');
        if (profile.name) document.getElementById('profile-name').value = profile.name;
        if (profile.surname) document.getElementById('profile-surname').value = profile.surname;
        if (profile.gender) document.getElementById('profile-gender').value = profile.gender;
        if (profile.email) document.getElementById('profile-email').value = profile.email;

        if (profile.avatar) {
            const display = document.getElementById('current-avatar');
            if (display) display.textContent = profile.avatar;
            app.tempProfileAvatar = profile.avatar;
        }

        if (profile.googleLinked) {
            const btnGoogle = document.querySelector('button[onclick="app.connectGoogle()"]');
            if (btnGoogle) {
                const emailDisplay = profile.email || 'Conectado';
                btnGoogle.innerHTML = `<i data-lucide="check"></i> <span>${emailDisplay}</span>`;
                btnGoogle.className = 'btn btn-secondary';
                btnGoogle.onclick = app.disconnectGoogle;
            }
        }
    },

    // Google OAuth Configuration
    googleClientId: '106097643504-j883o1a4k5ad28smia4o3sj215k1lqdc.apps.googleusercontent.com',
    tokenClient: null,

    initGoogleClient: () => {
        if (window.google) {
            app.tokenClient = google.accounts.oauth2.initTokenClient({
                client_id: app.googleClientId,
                scope: 'https://www.googleapis.com/auth/userinfo.profile https://www.googleapis.com/auth/userinfo.email',
                callback: app.handleGoogleResponse
            });
        } else {
            // Retry if script not loaded yet
            setTimeout(app.initGoogleClient, 500);
        }
    },

    handleGoogleResponse: async (tokenResponse) => {
        if (tokenResponse.access_token) {
            try {
                const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v3/userinfo', {
                    headers: {
                        'Authorization': `Bearer ${tokenResponse.access_token}`
                    }
                });
                const userInfo = await userInfoResponse.json();

                // Update Profile
                const profile = JSON.parse(localStorage.getItem('enclaro_profile') || '{}');
                profile.googleLinked = true;
                profile.email = userInfo.email;
                profile.name = userInfo.given_name || profile.name;
                profile.surname = userInfo.family_name || profile.surname;
                if (userInfo.picture) profile.avatarUrl = userInfo.picture; // Store URL if needed

                localStorage.setItem('enclaro_profile', JSON.stringify(profile));

                app.loadProfile();
                app.showToast(`Conectado como ${userInfo.name}`, 'success');

                // Restore button state
                const btn = document.querySelector('button[onclick*="app.connectGoogle"]'); // Search by onclick
                if (btn && btn.innerHTML.includes('spin')) {
                    // Will be handled by loadProfile, but ensuring just in case
                }

            } catch (error) {
                console.error("Error fetching Google user info:", error);
                app.showToast('Error obteniendo datos de Google', 'error');
                const btn = document.querySelector('button[onclick="app.connectGoogle()"]');
                if (btn) btn.innerHTML = '<i data-lucide="log-in"></i> <span>Conectar con Google</span>';
            }
        }
    },

    connectGoogle: () => {
        const btn = document.querySelector('button[onclick="app.connectGoogle()"]');
        if (btn) btn.innerHTML = '<i data-lucide="loader-2" class="spin"></i> Conectando...';

        if (!app.tokenClient) {
            app.initGoogleClient();
        }

        if (app.tokenClient) {
            // Use requestAccessToken to trigger the popup flow
            app.tokenClient.requestAccessToken();
        } else {
            app.showToast('Iniciando servicios de Google, intenta de nuevo en un segundo...', 'info');
            if (btn) btn.innerHTML = '<i data-lucide="log-in"></i> <span>Conectar con Google</span>';
            if (window.lucide) lucide.createIcons();
        }
    },

    disconnectGoogle: () => {
        const profile = JSON.parse(localStorage.getItem('enclaro_profile') || '{}');
        delete profile.googleLinked;
        // Optional: Clear email if you want, but maybe keep it
        // delete profile.email; 
        localStorage.setItem('enclaro_profile', JSON.stringify(profile));

        const btn = document.querySelector('button[onclick*="app.disconnectGoogle"]');
        if (btn) {
            btn.innerHTML = '<i data-lucide="log-in"></i> <span>Conectar con Google</span>';
            btn.className = 'btn btn-secondary';
            btn.setAttribute('onclick', 'app.connectGoogle()');
        }

        // Revoke token if we had one stored (we don't store access token persistently here for simplicity)
        if (window.google && profile.email) {
            google.accounts.id.revoke(profile.email, done => {
                console.log('Consent revoked');
            });
        }

        app.showToast('Cuenta desvinculada', 'info');
        if (window.lucide) lucide.createIcons();
    },

    updatePersonalizedText: (profile) => {
        if (!profile) profile = JSON.parse(localStorage.getItem('enclaro_profile') || '{}');
        if (!profile.name) return;

        let welcomeWord = 'Bienvenido';
        if (profile.gender === 'femenino') welcomeWord = 'Bienvenida';
        else if (profile.gender === 'nobinario' || profile.gender === 'otro') welcomeWord = 'Bienvenide';

        const settingsWelcome = document.getElementById('settings-welcome-text');
        if (settingsWelcome) {
            settingsWelcome.innerHTML = `${welcomeWord} a En Claro<br><span style="font-size:0.8em; opacity:0.8">${profile.name}</span>`;
        }

        // Update Onboarding Title
        const onboardingTitle = document.getElementById('i18n-onboarding-title');
        if (onboardingTitle) {
            onboardingTitle.textContent = `${welcomeWord} a En Claro`;
        }

        const introQuestion = document.getElementById('intro-question');
        if (introQuestion) {
            introQuestion.textContent = `¿Qué quieres hacer ahora, ${profile.name}?`;
        }
    },

    checkAuth: async () => {
        // Placeholder
    }
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    // We use app.init() if it exists, or duplicate the logic here if init was lost.
    if (app.init) {
        app.init();
    } else {
        console.error("Critical Error: app.init is missing! Defining fallback init.");
        const savedProfile = JSON.parse(localStorage.getItem('enclaro_profile') || '{}');
        if (localStorage.getItem('enclaro_onboarding_complete')) {
            app.showScreen('dashboard');
            if (savedProfile.name) app.updatePersonalizedText(savedProfile);
        } else {
            app.showScreen('legal-welcome');
        }

        if (window.lucide) lucide.createIcons();
    }
});
