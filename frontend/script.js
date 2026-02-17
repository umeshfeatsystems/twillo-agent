const API_BASE = window.location.origin;

const callForm = document.getElementById('callForm');
const statusCard = document.getElementById('statusCard');
const statusContent = document.getElementById('statusContent');
const callBtn = document.getElementById('callBtn');
const btnText = callBtn.querySelector('.btn-text');
const btnIcon = callBtn.querySelector('.btn-icon');

callForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const formData = new FormData(callForm);
    const phoneNumber = formData.get('phoneNumber');
    const callType = formData.get('callType');
    const languageMode = formData.get('languageMode');

    const callDetails = {
        name: formData.get('name'),
        amount: formData.get('amount'),
        days_overdue: formData.get('daysOverdue'),
        loan_type: formData.get('loanType') || 'Personal Loan',
        due_date: formData.get('dueDate') || 'today',
        bank_name: 'HDFC Bank'
    };

    // Show loading state
    callBtn.disabled = true;
    btnText.textContent = 'Initiating...';
    btnIcon.innerHTML = '<span class="loading"></span>';
    statusCard.style.display = 'none';

    try {
        const response = await fetch(`${API_BASE}/api/call/initiate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                phone_number: phoneNumber,
                call_type: callType,
                language_mode: languageMode,
                call_details: callDetails
            })
        });

        const result = await response.json();

        // Show status card
        statusCard.style.display = 'block';

        if (result.success) {
            statusContent.innerHTML = `
                <div class="status-item status-success">
                    <div class="status-label">✅ Call Initiated Successfully</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Session ID</div>
                    <div class="status-value">${result.session_id}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Call SID</div>
                    <div class="status-value">${result.call_sid}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Phone Number</div>
                    <div class="status-value">${phoneNumber}</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Call Type</div>
                    <div class="status-value">${result.call_type}</div>
                </div>
            `;

            // Reset form
            callForm.reset();

        } else {
            statusContent.innerHTML = `
                <div class="status-item status-error">
                    <div class="status-label">❌ Call Failed</div>
                    <div class="status-value">${result.error || 'Unknown error'}</div>
                </div>
            `;
        }

    } catch (error) {
        statusCard.style.display = 'block';
        statusContent.innerHTML = `
            <div class="status-item status-error">
                <div class="status-label">❌ Network Error</div>
                <div class="status-value">${error.message}</div>
            </div>
        `;
    } finally {
        // Reset button
        callBtn.disabled = false;
        btnText.textContent = 'Initiate Call';
        btnIcon.textContent = '📞';
    }
});

// Set default due date to tomorrow
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);
document.getElementById('dueDate').valueAsDate = tomorrow;
