/* ═══════════════════════════════════════════════
   EMI Call Agent — Dashboard Logic
   ═══════════════════════════════════════════════ */

const API = window.location.origin;

// ─── Tab Navigation ───
document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(`tab-${btn.dataset.tab}`).classList.add('active');

        // Load data when switching tabs
        const tab = btn.dataset.tab;
        if (tab === 'dashboard') { loadCallHistory(); loadStats(); }
        if (tab === 'customers') loadCustomers();
        if (tab === 'prompt') loadPrompt();
        if (tab === 'tone') loadTones();
    });
});

// ─── Modal ───
function showModal(customerData) {
    const modal = document.getElementById('modal');
    modal.classList.add('show');
    document.getElementById('modalStatus').style.display = 'none';

    // Set default due date
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    document.getElementById('dueDate').valueAsDate = tomorrow;

    // Pre-fill if customer data provided
    if (customerData) {
        document.getElementById('name').value = customerData.name || '';
        document.getElementById('phoneNumber').value = customerData.phone || '';
        document.getElementById('amount').value = customerData.amount || '';
        document.getElementById('daysOverdue').value = customerData.days_overdue || '';
        document.getElementById('loanType').value = customerData.loan_type || 'Personal Loan';
        document.getElementById('bankName').value = customerData.bank_name || 'HDFC Bank';
        if (customerData.due_date) {
            try { document.getElementById('dueDate').value = customerData.due_date; } catch (e) { }
        }
        document.getElementById('saveCustomer').checked = false;
    } else {
        document.getElementById('callForm').reset();
        document.getElementById('saveCustomer').checked = true;
        document.getElementById('bankName').value = 'HDFC Bank';
        document.getElementById('dueDate').valueAsDate = tomorrow;
    }
}

function hideModal(event) {
    if (event && event.target !== event.currentTarget) return;
    document.getElementById('modal').classList.remove('show');
}

// Close on Escape
document.addEventListener('keydown', e => {
    if (e.key === 'Escape') hideModal();
});

// ─── Initiate Call ───
document.getElementById('callForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const btn = document.getElementById('callBtn');
    const btnText = btn.querySelector('.btn-text');
    const statusEl = document.getElementById('modalStatus');

    const formData = new FormData(e.target);
    const name = formData.get('name');
    const phone = formData.get('phoneNumber');
    const amount = formData.get('amount');
    const daysOverdue = formData.get('daysOverdue');
    const loanType = formData.get('loanType') || 'Personal Loan';
    const dueDate = formData.get('dueDate') || 'today';
    const bankName = formData.get('bankName') || 'HDFC Bank';
    const languageMode = formData.get('languageMode');
    const saveCustomer = document.getElementById('saveCustomer').checked;

    // Loading
    btn.disabled = true;
    btnText.textContent = '⏳ Initiating...';

    try {
        // Save customer if checked
        if (saveCustomer) {
            await fetch(`${API}/api/customers`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, phone, amount: parseFloat(amount), loan_type: loanType, due_date: dueDate, days_overdue: parseInt(daysOverdue), bank_name: bankName })
            });
        }

        // Initiate call
        const res = await fetch(`${API}/api/call/initiate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                phone_number: phone,
                call_type: 'emi_reminder',
                language_mode: languageMode,
                call_details: { name, amount, days_overdue: daysOverdue, loan_type: loanType, due_date: dueDate, bank_name: bankName }
            })
        });

        const result = await res.json();
        statusEl.style.display = 'block';

        if (result.success) {
            statusEl.className = 'success';
            statusEl.innerHTML = `✅ <strong>Call initiated!</strong> Session: <code>${result.session_id?.substring(0, 8)}...</code>`;

            // Refresh dashboard
            setTimeout(() => {
                loadCallHistory();
                loadCustomers();
                loadStats();
            }, 1000);
        } else {
            statusEl.className = 'error';
            statusEl.innerHTML = `❌ ${result.error || 'Call failed'}`;
        }
    } catch (err) {
        statusEl.style.display = 'block';
        statusEl.className = 'error';
        statusEl.innerHTML = `❌ Network error: ${err.message}`;
    } finally {
        btn.disabled = false;
        btnText.textContent = '📞 Initiate Call';
    }
});

// ─── Load Call History ───
async function loadCallHistory() {
    try {
        const res = await fetch(`${API}/api/customers/call-history`);
        const data = await res.json();
        const tbody = document.getElementById('callHistoryBody');

        if (!data.history || data.history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-msg">No calls yet — click <strong>+ New Call</strong> to get started</td></tr>';
            return;
        }

        tbody.innerHTML = data.history.map(h => {
            const details = h.call_details || {};
            const name = details.name || 'Unknown';
            const phone = h.phone || '—';
            const amount = details.amount ? `₹${Number(details.amount).toLocaleString()}` : '—';
            const overdue = details.days_overdue ? `${details.days_overdue}d` : '—';
            const time = h.created_at ? timeAgo(new Date(h.created_at)) : '—';
            const status = h.call_sid ? '<span class="badge badge-success">Completed</span>' : '<span class="badge badge-pending">Pending</span>';

            return `<tr>
                <td style="color:var(--text);font-weight:500">${name}</td>
                <td>${phone}</td>
                <td>${amount}</td>
                <td>${overdue}</td>
                <td>${time}</td>
                <td>${status}</td>
                <td>
                    <button class="btn-call" onclick='showModal(${JSON.stringify({ name, phone, amount: details.amount, days_overdue: details.days_overdue, loan_type: details.loan_type, bank_name: details.bank_name })})'>
                        📞 Re-call
                    </button>
                </td>
            </tr>`;
        }).join('');

        // Update stats
        document.getElementById('statTotalCalls').textContent = data.history.length;
        const today = new Date().toDateString();
        const todayCount = data.history.filter(h => h.created_at && new Date(h.created_at).toDateString() === today).length;
        document.getElementById('statToday').textContent = todayCount;
    } catch (err) {
        console.error('Failed to load call history:', err);
    }
}

// ─── Load Customers ───
async function loadCustomers() {
    try {
        const res = await fetch(`${API}/api/customers`);
        const data = await res.json();
        const tbody = document.getElementById('customersBody');

        if (!data.customers || data.customers.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="empty-msg">No customers added yet</td></tr>';
            document.getElementById('statCustomers').textContent = '0';
            return;
        }

        document.getElementById('statCustomers').textContent = data.customers.length;

        tbody.innerHTML = data.customers.map(c => {
            const lastCalled = c.last_called ? timeAgo(new Date(c.last_called)) : 'Never';
            return `<tr>
                <td style="color:var(--text);font-weight:500">${c.name}</td>
                <td>${c.phone}</td>
                <td>₹${Number(c.amount).toLocaleString()}</td>
                <td>${c.loan_type}</td>
                <td>${c.days_overdue}d</td>
                <td>${lastCalled}</td>
                <td>
                    <div style="display:flex;gap:0.35rem">
                        <button class="btn-call" onclick='showModal(${JSON.stringify(c)})'>📞 Call</button>
                        <button class="btn-delete" onclick="deleteCustomer('${c._id}')">✕</button>
                    </div>
                </td>
            </tr>`;
        }).join('');
    } catch (err) {
        console.error('Failed to load customers:', err);
    }
}

async function deleteCustomer(id) {
    if (!confirm('Remove this customer?')) return;
    try {
        await fetch(`${API}/api/customers/${id}`, { method: 'DELETE' });
        loadCustomers();
        loadStats();
    } catch (err) {
        alert('Failed to delete: ' + err.message);
    }
}

// ─── Load Stats ───
async function loadStats() {
    try {
        const [histRes, custRes] = await Promise.all([
            fetch(`${API}/api/customers/call-history`),
            fetch(`${API}/api/customers`)
        ]);
        const hist = await histRes.json();
        const cust = await custRes.json();

        document.getElementById('statTotalCalls').textContent = hist.history?.length || 0;
        document.getElementById('statCustomers').textContent = cust.customers?.length || 0;

        const today = new Date().toDateString();
        const todayCount = (hist.history || []).filter(h => h.created_at && new Date(h.created_at).toDateString() === today).length;
        document.getElementById('statToday').textContent = todayCount;
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

// ─── Prompt Editor ───
async function loadPrompt() {
    try {
        const res = await fetch(`${API}/api/prompts/emi`);
        const data = await res.json();
        if (data.prompt) {
            document.getElementById('systemPrompt').value = data.prompt.system_prompt || '';
            document.getElementById('initialGreeting').value = data.prompt.initial_greeting || '';
        }
    } catch (err) {
        console.error('Failed to load prompt:', err);
    }
}

document.getElementById('savePromptBtn')?.addEventListener('click', async () => {
    const statusEl = document.getElementById('promptStatus');
    try {
        const res = await fetch(`${API}/api/prompts/emi`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                system_prompt: document.getElementById('systemPrompt').value,
                initial_greeting: document.getElementById('initialGreeting').value,
                tone: document.querySelector('.tone-card.active')?.dataset.tone || 'professional'
            })
        });
        const data = await res.json();
        statusEl.style.display = 'block';
        statusEl.className = 'prompt-status success';
        statusEl.textContent = '✅ Prompt saved successfully!';
        setTimeout(() => statusEl.style.display = 'none', 3000);
    } catch (err) {
        statusEl.style.display = 'block';
        statusEl.className = 'prompt-status error';
        statusEl.textContent = '❌ Failed to save: ' + err.message;
    }
});

document.getElementById('resetPromptBtn')?.addEventListener('click', async () => {
    if (!confirm('Reset prompt to default? This cannot be undone.')) return;
    try {
        await fetch(`${API}/api/prompts/emi`, { method: 'DELETE' });
        loadPrompt();
        const statusEl = document.getElementById('promptStatus');
        statusEl.style.display = 'block';
        statusEl.className = 'prompt-status success';
        statusEl.textContent = '✅ Prompt reset to default!';
        setTimeout(() => statusEl.style.display = 'none', 3000);
    } catch (err) {
        alert('Failed to reset: ' + err.message);
    }
});

// ─── Tone Presets ───
async function loadTones() {
    try {
        const res = await fetch(`${API}/api/prompts/tones`);
        const data = await res.json();
        const grid = document.getElementById('toneGrid');

        const icons = { professional: '💼', friendly: '😊', empathetic: '💙', firm: '⚡', gentle: '🌸' };

        grid.innerHTML = Object.entries(data.tones).map(([key, tone]) => `
            <div class="tone-card ${key === 'professional' ? 'active' : ''}" data-tone="${key}" onclick="selectTone('${key}')">
                <h4>${icons[key] || '🎯'} ${tone.name}</h4>
                <p>${tone.description}</p>
            </div>
        `).join('');
    } catch (err) {
        console.error('Failed to load tones:', err);
    }
}

function selectTone(toneKey) {
    document.querySelectorAll('.tone-card').forEach(c => c.classList.remove('active'));
    document.querySelector(`.tone-card[data-tone="${toneKey}"]`)?.classList.add('active');
}

// ─── Utility ───
function timeAgo(date) {
    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return 'Just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days}d ago`;
    return date.toLocaleDateString();
}

// ─── Init ───
loadCallHistory();
loadStats();
