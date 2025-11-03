document.addEventListener('DOMContentLoaded', function() {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.getElementById('uploadBtn');
    const uploadProgress = document.getElementById('uploadProgress');
    const uploadResult = document.getElementById('uploadResult');
    const dataTableBody = document.getElementById('dataTableBody');
    const searchInput = document.getElementById('searchInput');
    const refreshBtn = document.getElementById('refreshBtn');
    const dataModal = new bootstrap.Modal(document.getElementById('dataModal'));
    const modalBody = document.getElementById('modalBody');
    const summaryCards = document.getElementById('summaryCards');

    // Load data on page load
    loadData();
    loadSummary();

    // Upload form submission
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const file = fileInput.files[0];
        if (!file) {
            showAlert('Please select a CSV file to upload.', 'warning');
            return;
        }

        if (!file.name.toLowerCase().endsWith('.csv')) {
            showAlert('Please upload a CSV file.', 'warning');
            return;
        }

        // Show progress
        uploadProgress.style.display = 'block';
        uploadBtn.disabled = true;
        uploadResult.innerHTML = '';

        try {
            const formData = new FormData();
            formData.append('file', file);

            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                showAlert(`CSV processed successfully! ${result.records_added} records added.`, 'success');
                displaySummary(result.summary);
                loadData(); // Refresh the table
                loadSummary(); // Refresh summary
            } else {
                showAlert(result.error || 'Upload failed', 'danger');
            }
        } catch (error) {
            showAlert('Error uploading file: ' + error.message, 'danger');
        } finally {
            uploadProgress.style.display = 'none';
            uploadBtn.disabled = false;
        }
    });

    // Search functionality
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const rows = dataTableBody.querySelectorAll('tr');
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            if (text.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });

    // Refresh button
    refreshBtn.addEventListener('click', function() {
        loadData();
        loadSummary();
    });

    // Load data from server
    async function loadData() {
        try {
            dataTableBody.innerHTML = '<tr><td colspan="9" class="text-center text-muted"><i class="fas fa-spinner fa-spin me-2"></i>Loading data...</td></tr>';
            
            const response = await fetch('/data');
            const result = await response.json();

            if (result.success) {
                displayData(result.data);
            } else {
                dataTableBody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">Error loading data: ' + result.error + '</td></tr>';
            }
        } catch (error) {
            dataTableBody.innerHTML = '<tr><td colspan="9" class="text-center text-danger">Error loading data: ' + error.message + '</td></tr>';
        }
    }

    // Load summary data
    async function loadSummary() {
        try {
            const response = await fetch('/summary');
            const result = await response.json();

            if (result.success) {
                displaySummary(result.summary);
            }
        } catch (error) {
            console.error('Error loading summary:', error);
        }
    }

    // Display data in table
    function displayData(data) {
        if (!data || data.length === 0) {
            dataTableBody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">No data available</td></tr>';
            return;
        }

        dataTableBody.innerHTML = data.map(record => `
            <tr>
                <td>${record.writing_agent || ''}</td>
                <td>${record.insured_name || ''}</td>
                <td>${record.account || ''}</td>
                <td>${formatCurrency(record.payment)}</td>
                <td>${formatCurrency(record.premium)}</td>
                <td>${record.effective_date || ''}</td>
                <td>${record.policy_state || ''}</td>
                <td>${record.market || ''}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="showDetails('${escapeHtml(JSON.stringify(record))}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // Display summary statistics
    function displaySummary(summary) {
        if (!summary || Object.keys(summary).length === 0) {
            summaryCards.style.display = 'none';
            return;
        }

        summaryCards.style.display = 'block';
        document.getElementById('totalRecords').textContent = summary.total_records || 0;
        document.getElementById('totalPayment').textContent = formatCurrency(summary.total_payment || 0);
        document.getElementById('uniqueAgents').textContent = summary.unique_agents || 0;
        document.getElementById('uniqueStates').textContent = summary.unique_states || 0;
    }

    // Show detailed view
    window.showDetails = function(recordData) {
        const record = JSON.parse(recordData);
        const detailsHtml = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Agent Information</h6>
                    <div class="detail-row">
                        <span class="detail-label">Writing Agent:</span>
                        <span class="detail-value">${record.writing_agent || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Writing Agent NPN:</span>
                        <span class="detail-value">${record.writing_agent_npn || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">NPN:</span>
                        <span class="detail-value">${record.npn || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Insured Name:</span>
                        <span class="detail-value">${record.insured_name || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Account:</span>
                        <span class="detail-value">${record.account || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Plan:</span>
                        <span class="detail-value">${record.plan || 'N/A'}</span>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6>Financial Information</h6>
                    <div class="detail-row">
                        <span class="detail-label">Premium:</span>
                        <span class="detail-value">${formatCurrency(record.premium)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Commission Schedule:</span>
                        <span class="detail-value">${record.commission_schedule || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Split:</span>
                        <span class="detail-value">${record.split || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Payment:</span>
                        <span class="detail-value">${formatCurrency(record.payment)}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Payment Type:</span>
                        <span class="detail-value">${record.payment_type || 'N/A'}</span>
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-12">
                    <h6>Policy Details</h6>
                    <div class="detail-row">
                        <span class="detail-label">Effective Date:</span>
                        <span class="detail-value">${record.effective_date || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Coverage Month:</span>
                        <span class="detail-value">${record.coverage_month || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Policy State:</span>
                        <span class="detail-value">${record.policy_state || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Lives:</span>
                        <span class="detail-value">${record.lives || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Year:</span>
                        <span class="detail-value">${record.year || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Market:</span>
                        <span class="detail-value">${record.market || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Memo:</span>
                        <span class="detail-value">${record.memo || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Associated Statement:</span>
                        <span class="detail-value">${record.associated_statement || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `;
        modalBody.innerHTML = detailsHtml;
        dataModal.show();
    };

    // Utility functions
    function formatCurrency(amount) {
        if (!amount || amount === '') return 'N/A';
        const num = parseFloat(amount);
        if (isNaN(num)) return 'N/A';
        return '$' + num.toFixed(2);
    }

    function showAlert(message, type) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        uploadResult.innerHTML = alertHtml;
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});

