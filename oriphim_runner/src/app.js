/**
 * Oriphim Runner - Desktop UI JavaScript
 * 
 * Handles UI interactions, Tauri API communication, and real-time updates
 */

// Tauri API imports
const { invoke } = window.__TAURI__.tauri;
const { listen } = window.__TAURI__.event;
const { appWindow } = window.__TAURI__.window;

class OriphimRunnerUI {
    constructor() {
        this.isRunning = false;
        this.isPaused = false;
        this.currentJob = null;
        this.connectionStatus = 'disconnected';
        this.brokerStatus = 'disconnected';
        this.updateInterval = null;
        
        // Initialize UI
        this.initializeUI();
        this.bindEvents();
        this.startUpdateLoop();
        
        console.log('Oriphim Runner UI initialized');
    }
    
    initializeUI() {
        // Set initial status
        this.updateStatusIndicator('disconnected');
        this.updateConnectionStatus('cloud-status', 'DISCONNECTED', 'disconnected');
        this.updateConnectionStatus('broker-status', 'DISCONNECTED', 'disconnected');
        this.updateConnectionStatus('trading-mode', 'PAPER', 'paper');
        
        // Add initial log
        this.addLogEntry('Oriphim Runner UI initialized');
        
        // Update timestamp
        this.updateTimestamp();
        
        // Check if setup is needed
        this.checkSetupRequired();
    }
    
    bindEvents() {
        // Control buttons
        document.getElementById('pause-btn').addEventListener('click', () => this.handlePauseToggle());
        document.getElementById('restart-btn').addEventListener('click', () => this.handleRestart());
        document.getElementById('logs-folder-btn').addEventListener('click', () => this.handleOpenLogs());
        
        // Clear logs
        document.getElementById('clear-logs-btn').addEventListener('click', () => this.clearLogs());
        
        // Setup modal
        document.getElementById('setup-save-btn').addEventListener('click', () => this.handleSetupSave());
        document.getElementById('setup-cancel-btn').addEventListener('click', () => this.handleSetupCancel());
        
        // Listen for Tauri events
        this.listenForEvents();
    }
    
    async listenForEvents() {
        try {
            // Listen for Python runner status updates
            await listen('runner-status', (event) => {
                this.handleRunnerStatusUpdate(event.payload);
            });
            
            // Listen for connection updates
            await listen('connection-status', (event) => {
                this.handleConnectionUpdate(event.payload);
            });
            
            // Listen for job updates
            await listen('job-update', (event) => {
                this.handleJobUpdate(event.payload);
            });
            
            // Listen for log updates
            await listen('log-update', (event) => {
                this.handleLogUpdate(event.payload);
            });
            
        } catch (error) {
            console.error('Error setting up event listeners:', error);
        }
    }
    
    startUpdateLoop() {
        // Update every 5 seconds
        this.updateInterval = setInterval(() => {
            this.updateTimestamp();
            this.checkRunnerStatus();
        }, 5000);
    }
    
    async checkSetupRequired() {
        try {
            // Check if API key is configured
            const hasApiKey = await invoke('has_api_key');
            
            if (!hasApiKey) {
                this.showSetupModal();
            }
        } catch (error) {
            console.error('Error checking setup:', error);
            // Show setup modal as fallback
            this.showSetupModal();
        }
    }
    
    async checkRunnerStatus() {
        try {
            const isRunning = await invoke('get_runner_status');
            this.isRunning = isRunning;
            
            // Update status indicator based on runner state
            if (isRunning) {
                if (this.currentJob) {
                    this.updateStatusIndicator('running');
                } else {
                    this.updateStatusIndicator('connected');
                }
            } else {
                this.updateStatusIndicator('disconnected');
            }
            
        } catch (error) {
            console.error('Error checking runner status:', error);
            this.updateStatusIndicator('disconnected');
        }
    }
    
    // UI Update Methods
    updateStatusIndicator(status) {
        const dot = document.getElementById('status-dot');
        const text = document.getElementById('status-text');
        
        dot.className = 'status-dot';
        
        switch (status) {
            case 'connected':
                dot.classList.add('connected');
                text.textContent = 'Connected';
                break;
            case 'running':
                dot.classList.add('running');
                text.textContent = 'Running';
                break;
            case 'disconnected':
            default:
                text.textContent = 'Disconnected';
                break;
        }
    }
    
    updateConnectionStatus(elementId, text, statusClass) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
            element.className = `status-value ${statusClass}`;
        }
    }
    
    updateCurrentJob(job) {
        const jobElement = document.getElementById('current-job');
        const detailsElement = document.getElementById('job-details');
        
        if (job && job.strategy) {
            this.currentJob = job;
            jobElement.textContent = `${job.strategy} - ${job.symbol || 'Unknown'}`;
            
            // Update job details
            document.getElementById('job-strategy').textContent = job.strategy || '-';
            document.getElementById('job-symbol').textContent = job.symbol || '-';
            document.getElementById('job-started').textContent = 
                job.started ? new Date(job.started).toLocaleTimeString() : '-';
            
            detailsElement.classList.remove('hidden');
        } else {
            this.currentJob = null;
            jobElement.textContent = 'None';
            detailsElement.classList.add('hidden');
        }
    }
    
    addLogEntry(message, level = 'info', timestamp = null) {
        const logsContent = document.getElementById('logs-content');
        const logEntry = document.createElement('div');
        
        if (!timestamp) {
            timestamp = new Date();
        }
        
        const timeStr = timestamp.toLocaleTimeString();
        
        logEntry.className = `log-entry ${level}`;
        logEntry.innerHTML = `
            <span class="log-time">[${timeStr}]</span>
            <span class="log-message">${message}</span>
        `;
        
        logsContent.appendChild(logEntry);
        
        // Auto-scroll to bottom
        logsContent.scrollTop = logsContent.scrollHeight;
        
        // Limit log entries (keep last 100)
        const entries = logsContent.children;
        if (entries.length > 100) {
            logsContent.removeChild(entries[0]);
        }
    }
    
    clearLogs() {
        const logsContent = document.getElementById('logs-content');
        logsContent.innerHTML = '';
        this.addLogEntry('Logs cleared');
    }
    
    updateTimestamp() {
        const timestamp = document.getElementById('last-update');
        if (timestamp) {
            timestamp.textContent = new Date().toLocaleTimeString();
        }
    }
    
    showToast(message, type = 'info', duration = 3000) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        // Auto-remove after duration
        setTimeout(() => {
            if (container.contains(toast)) {
                container.removeChild(toast);
            }
        }, duration);
    }
    
    // Modal Methods
    showSetupModal() {
        const modal = document.getElementById('setup-modal');
        modal.classList.remove('hidden');
        
        // Focus on input
        const input = document.getElementById('api-key-input');
        if (input) {
            input.focus();
        }
    }
    
    hideSetupModal() {
        const modal = document.getElementById('setup-modal');
        modal.classList.add('hidden');
        
        // Clear input
        const input = document.getElementById('api-key-input');
        if (input) {
            input.value = '';
        }
    }
    
    // Event Handlers
    async handlePauseToggle() {
        try {
            const button = document.getElementById('pause-btn');
            const icon = button.querySelector('.btn-icon');
            
            if (this.isPaused) {
                // Resume
                await invoke('resume_runner');
                button.innerHTML = '<span class="btn-icon">⏸</span>Pause Runner';
                this.isPaused = false;
                this.addLogEntry('Runner resumed', 'success');
                this.showToast('Runner resumed', 'success');
            } else {
                // Pause
                await invoke('pause_runner');
                button.innerHTML = '<span class="btn-icon">▶</span>Resume Runner';
                this.isPaused = true;
                this.addLogEntry('Runner paused', 'warning');
                this.showToast('Runner paused', 'warning');
            }
        } catch (error) {
            console.error('Error toggling pause:', error);
            this.addLogEntry(`Error: ${error}`, 'error');
            this.showToast('Failed to toggle pause', 'error');
        }
    }
    
    async handleRestart() {
        if (!confirm('Are you sure you want to restart the Runner? This will stop any active trades.')) {
            return;
        }
        
        try {
            this.addLogEntry('Restarting runner...', 'warning');
            this.showToast('Restarting runner...', 'info');
            
            // Stop current runner
            await invoke('stop_python_runner');
            
            // Wait a moment
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            // Start new runner
            await invoke('start_python_runner');
            
            this.addLogEntry('Runner restarted successfully', 'success');
            this.showToast('Runner restarted', 'success');
            
            // Reset UI state
            this.isPaused = false;
            this.updateCurrentJob(null);
            
            const pauseBtn = document.getElementById('pause-btn');
            pauseBtn.innerHTML = '<span class="btn-icon">⏸</span>Pause Runner';
            
        } catch (error) {
            console.error('Error restarting:', error);
            this.addLogEntry(`Restart error: ${error}`, 'error');
            this.showToast('Failed to restart runner', 'error');
        }
    }
    
    async handleOpenLogs() {
        try {
            await invoke('open_logs_folder');
            this.addLogEntry('Opened logs folder');
        } catch (error) {
            console.error('Error opening logs:', error);
            this.addLogEntry(`Error opening logs: ${error}`, 'error');
            this.showToast('Failed to open logs folder', 'error');
        }
    }
    
    async handleSetupSave() {
        const input = document.getElementById('api-key-input');
        const apiKey = input.value.trim();
        
        if (!apiKey) {
            this.showToast('Please enter a valid API key', 'error');
            return;
        }
        
        try {
            await invoke('save_api_key', { apiKey });
            
            this.hideSetupModal();
            this.addLogEntry('API key saved successfully', 'success');
            this.showToast('API key saved! Connecting...', 'success');
            
            // Restart runner with new API key
            await this.handleRestart();
            
        } catch (error) {
            console.error('Error saving API key:', error);
            this.showToast('Failed to save API key', 'error');
        }
    }
    
    handleSetupCancel() {
        this.hideSetupModal();
        this.addLogEntry('Setup cancelled');
    }
    
    // Event Update Handlers
    handleRunnerStatusUpdate(payload) {
        this.isRunning = payload.running;
        this.isPaused = payload.paused || false;
        
        this.addLogEntry(`Runner status: ${payload.running ? 'Running' : 'Stopped'}`, 
                        payload.running ? 'success' : 'warning');
        
        // Update pause button
        const pauseBtn = document.getElementById('pause-btn');
        if (this.isPaused) {
            pauseBtn.innerHTML = '<span class="btn-icon">▶</span>Resume Runner';
        } else {
            pauseBtn.innerHTML = '<span class="btn-icon">⏸</span>Pause Runner';
        }
    }
    
    handleConnectionUpdate(payload) {
        if (payload.type === 'cloud') {
            this.connectionStatus = payload.status;
            const text = payload.status === 'connected' ? 'CONNECTED' : 'DISCONNECTED';
            this.updateConnectionStatus('cloud-status', text, payload.status);
            this.addLogEntry(`Cloud connection: ${payload.status}`, 
                           payload.status === 'connected' ? 'success' : 'error');
        } else if (payload.type === 'broker') {
            this.brokerStatus = payload.status;
            let text = payload.status === 'connected' ? 'CONNECTED' : 'DISCONNECTED';
            
            if (payload.status === 'connected' && payload.account) {
                text = `IBKR ${payload.mode || 'Paper'} (${payload.account})`;
            }
            
            this.updateConnectionStatus('broker-status', text, payload.status);
            this.addLogEntry(`Broker connection: ${payload.status}`, 
                           payload.status === 'connected' ? 'success' : 'error');
            
            // Update trading mode
            if (payload.mode) {
                this.updateConnectionStatus('trading-mode', payload.mode.toUpperCase(), 
                                          payload.mode.toLowerCase());
            }
        }
    }
    
    handleJobUpdate(payload) {
        if (payload.job) {
            this.updateCurrentJob(payload.job);
            this.addLogEntry(`Job started: ${payload.job.strategy} ${payload.job.symbol}`, 'info');
        } else {
            this.updateCurrentJob(null);
            this.addLogEntry('Job completed', 'success');
        }
    }
    
    handleLogUpdate(payload) {
        if (payload.entries && Array.isArray(payload.entries)) {
            payload.entries.forEach(entry => {
                const timestamp = entry.timestamp ? new Date(entry.timestamp) : null;
                this.addLogEntry(entry.message, entry.level || 'info', timestamp);
            });
        }
    }
    
    // Cleanup
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Initialize UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Check if we're running in Tauri
    if (window.__TAURI__) {
        window.oriphimUI = new OriphimRunnerUI();
    } else {
        console.error('Tauri API not available - running in browser mode');
        
        // Add fallback message for browser testing
        document.body.innerHTML = `
            <div style="padding: 20px; text-align: center; font-family: Arial, sans-serif;">
                <h1>Oriphim Runner</h1>
                <p>This application requires the Tauri desktop environment.</p>
                <p>Please run using <code>tauri dev</code> or the compiled desktop application.</p>
            </div>
        `;
    }
});

// Handle window close
window.addEventListener('beforeunload', () => {
    if (window.oriphimUI) {
        window.oriphimUI.destroy();
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (event) => {
    if (event.ctrlKey || event.metaKey) {
        switch (event.key) {
            case 'r':
                event.preventDefault();
                if (window.oriphimUI) {
                    window.oriphimUI.handleRestart();
                }
                break;
            case 'p':
                event.preventDefault();
                if (window.oriphimUI) {
                    window.oriphimUI.handlePauseToggle();
                }
                break;
            case 'l':
                event.preventDefault();
                if (window.oriphimUI) {
                    window.oriphimUI.clearLogs();
                }
                break;
        }
    }
});