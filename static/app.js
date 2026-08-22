// VolHedge Pro - Frontend JavaScript Application

// Configuration - reads from window.__VOLHEDGE_CONFIG__ or uses defaults
const VOLHEDGE_CONFIG = window.__VOLHEDGE_CONFIG__ || {
    API_BASE_URL: localStorage.getItem('volhedge_api_url') || 'http://localhost:8000',
    WS_PROTOCOL: window.location.protocol === 'https:' ? 'wss:' : 'ws:'
};

class VolHedgeApp {
    constructor() {
        this.socket = null;
        this.currentSymbol = 'NIFTY';
        this.portfolio = {};
        this.apiBaseUrl = VOLHEDGE_CONFIG.API_BASE_URL;
        this.initializeEventListeners();
        this.loadTabs();
        this.connectWebSocket();
    }

    initializeEventListeners() {
        // Buttons
        document.getElementById('addPositionBtn').addEventListener('click', () => this.openAddPositionModal());
        document.getElementById('optionChainBtn').addEventListener('click', () => this.openOptionChainModal());
        document.getElementById('addScrip').addEventListener('click', () => this.addScripTab());
        document.getElementById('rebalanceBtn').addEventListener('click', () => this.executeRebalance());
        document.getElementById('authBtn').addEventListener('click', () => this.openAuthDialog());
        document.getElementById('settingsBtn').addEventListener('click', () => this.openConfigModal());

        // Modal controls
        document.querySelector('.modal-close').addEventListener('click', (e) => {
            e.target.closest('.modal').classList.add('hidden');
        });

        document.getElementById('closeModal').addEventListener('click', () => {
            document.getElementById('addPositionModal').classList.add('hidden');
        });

        document.getElementById('submitPosition').addEventListener('click', () => this.submitPosition());

        // Table row click for trade history
        document.addEventListener('click', (e) => {
            if (e.target.closest('tbody tr') && !e.target.closest('button')) {
                const row = e.target.closest('tbody tr');
                const posId = row.getAttribute('data-pos-id');
                this.showTradeHistory(posId);
            }
        });

        // Strike count selector
        document.getElementById('strikeCountSelect').addEventListener('change', (e) => {
            this.loadOptionChain(parseInt(e.target.value));
        });
    }

    connectWebSocket() {
        const apiUrl = new URL(this.apiBaseUrl);
        const protocol = apiUrl.protocol === 'https:' ? 'wss:' : 'ws:';
        const ws_url = `${protocol}//${apiUrl.host}/ws`;

        this.socket = new WebSocket(ws_url);

        this.socket.onopen = () => {
            console.log('Connected to WebSocket');
            this.socket.send(JSON.stringify({ type: 'subscribe', symbol: this.currentSymbol }));
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'portfolio_update') {
                this.portfolio[data.symbol] = data;
                if (data.symbol === this.currentSymbol) {
                    this.updateUI(data);
                }
            }
        };

        this.socket.onerror = (error) => console.error('WebSocket error:', error);
        this.socket.onclose = () => {
            console.log('WebSocket closed, reconnecting in 3s...');
            setTimeout(() => this.connectWebSocket(), 3000);
        };
    }

    async loadTabs() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/tabs`);
            const data = await response.json();
            const tabs = data.tabs || ['NIFTY', 'BANKNIFTY', 'FINNIFTY'];

            const tabsList = document.getElementById('tabsList');
            tabsList.innerHTML = '';

            tabs.forEach(symbol => {
                const tab = document.createElement('button');
                tab.className = `tab ${symbol === this.currentSymbol ? 'active' : ''}`;
                tab.innerHTML = `
                    <span>${symbol}</span>
                    <button class="close-btn" onclick="event.stopPropagation();">&times;</button>
                `;

                tab.addEventListener('click', () => this.switchTab(symbol));
                tab.querySelector('.close-btn').addEventListener('click', () => this.removeTab(symbol));

                tabsList.appendChild(tab);
            });
        } catch (error) {
            console.error('Error loading tabs:', error);
        }
    }

    switchTab(symbol) {
        this.currentSymbol = symbol;
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        event.target.closest('.tab').classList.add('active');

        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            this.socket.send(JSON.stringify({ type: 'subscribe', symbol }));
        }

        this.loadPortfolioData();
    }

    async loadPortfolioData() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/portfolio`);
            const data = await response.json();
            this.portfolio = data;

            if (data[this.currentSymbol]) {
                this.updateUI(data[this.currentSymbol]);
            }
        } catch (error) {
            console.error('Error loading portfolio:', error);
        }
    }

    updateUI(data) {
        if (!data || !data.summary) return;

        const summary = data.summary;
        const positions = data.positions || [];

        // Update metrics bar
        document.getElementById('mtm').textContent = '₹' + (summary.gross_mtm || 0).toFixed(2);
        document.getElementById('netDelta').textContent = (summary.total_delta || 0).toFixed(2);
        document.getElementById('netGamma').textContent = (summary.total_gamma || 0).toFixed(4);
        document.getElementById('netVega').textContent = (summary.total_vega || 0).toFixed(2);
        document.getElementById('netTheta').textContent = (summary.total_theta || 0).toFixed(2);
        document.getElementById('marginReq').textContent = '₹' + (summary.total_margin || 0).toFixed(2);

        // Update delta alert
        const alertBanner = document.getElementById('deltaAlertBanner');
        if (summary.rebalance_needed) {
            alertBanner.classList.remove('hidden');
            document.getElementById('deltaRecommendation').textContent = summary.rebalance_recommendation;
        } else {
            alertBanner.classList.add('hidden');
        }

        // Update positions table
        this.renderPositionsTable(positions);
    }

    renderPositionsTable(positions) {
        const tbody = document.getElementById('positionsBody');
        const emptyState = document.getElementById('emptyState');

        if (!positions || positions.length === 0) {
            tbody.innerHTML = '';
            emptyState.style.display = 'block';
            return;
        }

        emptyState.style.display = 'none';
        tbody.innerHTML = positions.map(pos => `
            <tr data-pos-id="${pos.id}">
                <td>${pos.strike}</td>
                <td>${pos.opt_type}</td>
                <td>${pos.qty}</td>
                <td>₹${(pos.entry_price || 0).toFixed(2)}</td>
                <td>₹${(pos.current_price || 0).toFixed(2)}</td>
                <td class="${pos.mtm >= 0 ? 'positive' : 'negative'}">₹${(pos.mtm || 0).toFixed(2)}</td>
                <td>${(pos.iv || 0).toFixed(2)}</td>
                <td>${(pos.unit_delta || 0).toFixed(4)}</td>
                <td>${(pos.unit_gamma || 0).toFixed(6)}</td>
                <td>${(pos.unit_vega || 0).toFixed(2)}</td>
                <td>${(pos.unit_theta || 0).toFixed(4)}</td>
                <td>
                    <button class="btn btn-small btn-danger" onclick="app.deletePosition('${pos.id}')">Delete</button>
                </td>
            </tr>
        `).join('');
    }

    openAddPositionModal() {
        document.getElementById('addPositionModal').classList.remove('hidden');
    }

    async submitPosition() {
        const instType = document.getElementById('instType').value;
        const strike = parseFloat(document.getElementById('strikeInput').value);
        const expiry = document.getElementById('expiryInput').value;
        const qty = parseInt(document.getElementById('qtyInput').value);
        const price = parseFloat(document.getElementById('priceInput').value);
        const tag = document.getElementById('tagInput').value;

        if (!strike || !expiry || !qty || !price) {
            alert('Please fill all fields');
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/positions/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: this.currentSymbol,
                    opt_type: instType,
                    strike,
                    expiry,
                    qty,
                    entry_price: price,
                    tag
                })
            });

            const result = await response.json();
            if (result.success) {
                document.getElementById('addPositionModal').classList.add('hidden');
                this.clearPositionForm();
                this.loadPortfolioData();
            }
        } catch (error) {
            console.error('Error adding position:', error);
            alert('Failed to add position');
        }
    }

    clearPositionForm() {
        document.getElementById('strikeInput').value = '';
        document.getElementById('expiryInput').value = '';
        document.getElementById('qtyInput').value = '';
        document.getElementById('priceInput').value = '';
        document.getElementById('tagInput').value = '';
    }

    async deletePosition(posId) {
        if (!confirm('Delete this position?')) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/positions/${this.currentSymbol}/${posId}`, {
                method: 'DELETE'
            });

            const result = await response.json();
            if (result.success) {
                this.loadPortfolioData();
            }
        } catch (error) {
            console.error('Error deleting position:', error);
        }
    }

    async openOptionChainModal() {
        document.getElementById('optionChainModal').classList.remove('hidden');
        await this.loadOptionChain(50);
    }

    async loadOptionChain(strikeCount = 50) {
        const loader = document.getElementById('optionChainLoader');
        const table = document.getElementById('chainTable');
        loader.classList.remove('hidden');
        table.classList.add('hidden');

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/option_chain/${this.currentSymbol}?strike_count=${strikeCount}`);
            const chain = await response.json();

            if (!chain.strikes) {
                loader.textContent = 'No data available';
                return;
            }

            const tbody = document.getElementById('chainBody');
            tbody.innerHTML = chain.strikes.map(strike => `
                <tr>
                    <td>${(strike.ce_iv || 0).toFixed(2)}</td>
                    <td>₹${(strike.ce_ltp || 0).toFixed(2)}</td>
                    <td>${(strike.ce_delta || 0).toFixed(4)}</td>
                    <td><button class="btn btn-small btn-success" onclick="app.quickAddPosition(${strike.strike}, 'CE', ${strike.ce_ltp})">+ Add</button></td>
                    <td style="text-align:center; font-weight:bold;">${strike.strike}</td>
                    <td>${(strike.pe_iv || 0).toFixed(2)}</td>
                    <td>₹${(strike.pe_ltp || 0).toFixed(2)}</td>
                    <td>${(strike.pe_delta || 0).toFixed(4)}</td>
                    <td><button class="btn btn-small btn-danger" onclick="app.quickAddPosition(${strike.strike}, 'PE', ${strike.pe_ltp})">+ Add</button></td>
                </tr>
            `).join('');

            loader.classList.add('hidden');
            table.classList.remove('hidden');
        } catch (error) {
            console.error('Error loading option chain:', error);
            loader.textContent = 'Error loading option chain';
        }
    }

    quickAddPosition(strike, type, ltp) {
        document.getElementById('strikeInput').value = strike;
        document.getElementById('instType').value = type;
        document.getElementById('priceInput').value = ltp.toFixed(2);
        document.getElementById('qtyInput').focus();
        document.getElementById('optionChainModal').classList.add('hidden');
        document.getElementById('addPositionModal').classList.remove('hidden');
    }

    async addScripTab() {
        const symbol = document.getElementById('symbolSearch').value.toUpperCase().trim();
        if (!symbol) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/symbols/add_tab`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ symbol })
            });

            if (response.ok) {
                document.getElementById('symbolSearch').value = '';
                this.loadTabs();
            }
        } catch (error) {
            console.error('Error adding tab:', error);
        }
    }

    async removeTab(symbol) {
        if (!confirm(`Remove ${symbol} tab?`)) return;

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/symbols/remove_tab/${symbol}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                this.loadTabs();
                if (symbol === this.currentSymbol) {
                    this.currentSymbol = 'NIFTY';
                    this.loadPortfolioData();
                }
            }
        } catch (error) {
            console.error('Error removing tab:', error);
        }
    }

    async executeRebalance() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/rebalance/${this.currentSymbol}`);
            const rec = await response.json();

            alert(`Rebalance Recommendation:\n${rec.recommendation}\n\n(In live mode, this would execute via Fyers API)`);
        } catch (error) {
            console.error('Error:', error);
        }
    }

    showTradeHistory(posId) {
        const positions = this.portfolio[this.currentSymbol]?.positions || [];
        const position = positions.find(p => p.id === posId);

        if (!position) return;

        const modal = document.getElementById('tradeHistoryModal');
        const tbody = document.getElementById('tradeHistoryBody');

        const trades = position.trades || [];
        tbody.innerHTML = trades.map(trade => `
            <tr>
                <td>${trade.date}</td>
                <td>${trade.time}</td>
                <td>${trade.action}</td>
                <td>${trade.qty}</td>
                <td>₹${(trade.price || 0).toFixed(2)}</td>
                <td>₹${((trade.qty * trade.price) || 0).toFixed(2)}</td>
                <td>${trade.tag || '-'}</td>
            </tr>
        `).join('');

        modal.classList.remove('hidden');

        modal.querySelector('.modal-close').onclick = () => {
            modal.classList.add('hidden');
        };
    }

    openAuthDialog() {
        const appId = prompt('Enter Fyers App ID:');
        if (!appId) return;

        const secretKey = prompt('Enter Fyers Secret Key:');
        if (!secretKey) return;

        alert('To complete OAuth:\n1. Click OK\n2. Browser will open Fyers login\n3. Authorize the application\n4. Copy the redirect URL\n5. Paste it in the terminal prompt');
    }

    openConfigModal() {
        const modal = document.getElementById('configModal');
        const input = document.getElementById('apiUrlInput');
        input.value = localStorage.getItem('volhedge_api_url') || '';

        modal.classList.remove('hidden');

        document.getElementById('saveConfigBtn').onclick = () => this.saveConfig();
        document.getElementById('closeConfigModal').onclick = () => {
            modal.classList.add('hidden');
        };
        modal.querySelector('.modal-close').onclick = () => {
            modal.classList.add('hidden');
        };
    }

    saveConfig() {
        const input = document.getElementById('apiUrlInput');
        const url = input.value.trim();

        if (url) {
            localStorage.setItem('volhedge_api_url', url);
            this.apiBaseUrl = url;
            alert('✓ Backend URL saved! Page will reload...');
        } else {
            localStorage.removeItem('volhedge_api_url');
            this.apiBaseUrl = 'http://localhost:8000';
            alert('✓ Reset to localhost');
        }

        document.getElementById('configModal').classList.add('hidden');
        location.reload();
    }
}

// Initialize app when DOM is ready
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new VolHedgeApp();
    app.loadPortfolioData();

    // Auto-refresh every 3 seconds
    setInterval(() => {
        if (app) app.loadPortfolioData();
    }, 3000);
});
