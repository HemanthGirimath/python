class SettingsManager {
    constructor() {
        this.settings = null;
        this.loadSettings();
        this.setupEventListeners();
    }

    async loadSettings() {
        try {
            const response = await fetch('/settings/load');
            this.settings = await response.json();
            this.applySettings();
        } catch (error) {
            console.error('Error loading settings:', error);
        }
    }

    async saveSettings() {
        try {
            const response = await fetch('/settings/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.settings)
            });
            
            const result = await response.json();
            if (result.status === 'success') {
                showNotification('Settings saved successfully', 'success');
            } else {
                showNotification('Failed to save settings', 'error');
            }
        } catch (error) {
            console.error('Error saving settings:', error);
            showNotification('Error saving settings', 'error');
        }
    }

    applySettings() {
        if (!this.settings) return;

        // Apply theme
        document.body.className = `${this.settings.display.theme}-theme`;
        
        // Update form values
        document.querySelectorAll('[data-setting]').forEach(element => {
            const [category, setting] = element.dataset.setting.split('.');
            if (element.type === 'checkbox') {
                element.checked = this.settings[category][setting];
            } else {
                element.value = this.settings[category][setting];
            }
        });

        // Apply chart settings
        if (window.updateChart) {
            updateChart();
        }
    }

    setupEventListeners() {
        // Save button
        document.getElementById('save-settings').addEventListener('click', () => {
            this.collectFormSettings();
            this.saveSettings();
        });

        // Reset button
        document.getElementById('reset-settings').addEventListener('click', () => {
            if (confirm('Are you sure you want to reset all settings to default?')) {
                this.resetToDefault();
            }
        });

        // Real-time settings updates
        document.querySelectorAll('[data-setting]').forEach(element => {
            element.addEventListener('change', () => {
                this.collectFormSettings();
                this.applySettings();
            });
        });
    }

    collectFormSettings() {
        document.querySelectorAll('[data-setting]').forEach(element => {
            const [category, setting] = element.dataset.setting.split('.');
            this.settings[category][setting] = element.type === 'checkbox' ? 
                element.checked : element.value;
        });
    }

    async resetToDefault() {
        try {
            const response = await fetch('/settings/default');
            this.settings = await response.json();
            this.applySettings();
            this.saveSettings();
            showNotification('Settings reset to default', 'success');
        } catch (error) {
            console.error('Error resetting settings:', error);
            showNotification('Error resetting settings', 'error');
        }
    }
}

// Notification helper
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.classList.add('show');
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }, 100);
}

// Initialize settings manager
document.addEventListener('DOMContentLoaded', () => {
    window.settingsManager = new SettingsManager();
}); 