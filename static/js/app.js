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

    // Load data on page load
    loadData();

    // Upload form submission
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const file = fileInput.files[0];
        if (!file) {
            showAlert('Please select a file to upload.', 'warning');
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
                showAlert('Document processed successfully!', 'success');
                displayParsedData(result.data);
                loadData(); // Refresh the table
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
    });

    // Load data from server
    async function loadData() {
        try {
            dataTableBody.innerHTML = '<tr><td colspan="10" class="text-center text-muted"><i class="fas fa-spinner fa-spin me-2"></i>Loading data...</td></tr>';
            
            const response = await fetch('/data');
            const result = await response.json();

            if (result.success) {
                displayData(result.data);
            } else {
                dataTableBody.innerHTML = '<tr><td colspan="10" class="text-center text-danger">Error loading data: ' + result.error + '</td></tr>';
            }
        } catch (error) {
            dataTableBody.innerHTML = '<tr><td colspan="10" class="text-center text-danger">Error loading data: ' + error.message + '</td></tr>';
        }
    }

    // Display data in table
    function displayData(data) {
        if (!data || data.length === 0) {
            dataTableBody.innerHTML = '<tr><td colspan="10" class="text-center text-muted">No data available</td></tr>';
            return;
        }

        dataTableBody.innerHTML = data.map(row => `
            <tr>
                <td>${row['File Name'] || ''}</td>
                <td>${row['Patient Name'] || ''}</td>
                <td>${row['Policy Number'] || ''}</td>
                <td>${row['Claim Number'] || ''}</td>
                <td>${row['Date of Service'] || ''}</td>
                <td>${row['Provider Name'] || ''}</td>
                <td>${formatCurrency(row['Total Amount'])}</td>
                <td>${formatCurrency(row['Amount Paid'])}</td>
                <td><span class="status-badge status-${getStatusClass(row['Claim Status'])}">${row['Claim Status'] || 'Unknown'}</span></td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="showDetails('${escapeHtml(JSON.stringify(row))}')">
                        <i class="fas fa-eye"></i>
                    </button>
                </td>
            </tr>
        `).join('');
    }

    // Display parsed data after upload
    function displayParsedData(data) {
        const resultHtml = `
            <div class="alert alert-success">
                <h6><i class="fas fa-check-circle me-2"></i>Document Parsed Successfully</h6>
                <div class="row mt-3">
                    <div class="col-md-6">
                        <strong>Patient:</strong> ${data.patient_name || 'N/A'}<br>
                        <strong>Policy Number:</strong> ${data.policy_number || 'N/A'}<br>
                        <strong>Claim Number:</strong> ${data.claim_number || 'N/A'}<br>
                        <strong>Date of Service:</strong> ${data.date_of_service || 'N/A'}
                    </div>
                    <div class="col-md-6">
                        <strong>Provider:</strong> ${data.provider_name || 'N/A'}<br>
                        <strong>Total Amount:</strong> ${formatCurrency(data.total_amount)}<br>
                        <strong>Amount Paid:</strong> ${formatCurrency(data.amount_paid)}<br>
                        <strong>Status:</strong> ${data.claim_status || 'N/A'}
                    </div>
                </div>
            </div>
        `;
        uploadResult.innerHTML = resultHtml;
    }

    // Show detailed view
    window.showDetails = function(rowData) {
        const data = JSON.parse(rowData);
        const detailsHtml = `
            <div class="row">
                <div class="col-md-6">
                    <h6>Basic Information</h6>
                    <div class="detail-row">
                        <span class="detail-label">File Name:</span>
                        <span class="detail-value">${data['File Name'] || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Patient Name:</span>
                        <span class="detail-value">${data['Patient Name'] || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Policy Number:</span>
                        <span class="detail-value">${data['Policy Number'] || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Claim Number:</span>
                        <span class="detail-value">${data['Claim Number'] || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Date of Service:</span>
                        <span class="detail-value">${data['Date of Service'] || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Provider Name:</span>
                        <span class="detail-value">${data['Provider Name'] || 'N/A'}</span>
                    </div>
                </div>
                <div class="col-md-6">
                    <h6>Financial Information</h6>
                    <div class="detail-row">
                        <span class="detail-label">Total Amount:</span>
                        <span class="detail-value">${formatCurrency(data['Total Amount'])}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Amount Paid:</span>
                        <span class="detail-value">${formatCurrency(data['Amount Paid'])}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Deductible:</span>
                        <span class="detail-value">${formatCurrency(data['Deductible'])}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Copay:</span>
                        <span class="detail-value">${formatCurrency(data['Copay'])}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Coinsurance:</span>
                        <span class="detail-value">${formatCurrency(data['Coinsurance'])}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Insurance Company:</span>
                        <span class="detail-value">${data['Insurance Company'] || 'N/A'}</span>
                    </div>
                </div>
            </div>
            <div class="row mt-3">
                <div class="col-12">
                    <h6>Service Details</h6>
                    <div class="detail-row">
                        <span class="detail-label">Service Description:</span>
                        <span class="detail-value">${data['Service Description'] || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Diagnosis Codes:</span>
                        <span class="detail-value">${data['Diagnosis Codes'] || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Procedure Codes:</span>
                        <span class="detail-value">${data['Procedure Codes'] || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Claim Status:</span>
                        <span class="detail-value">${data['Claim Status'] || 'N/A'}</span>
                    </div>
                    <div class="detail-row">
                        <span class="detail-label">Notes:</span>
                        <span class="detail-value">${data['Notes'] || 'N/A'}</span>
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

    function getStatusClass(status) {
        if (!status) return 'unknown';
        const statusLower = status.toLowerCase();
        if (statusLower.includes('paid') || statusLower.includes('approved')) return 'paid';
        if (statusLower.includes('pending') || statusLower.includes('processing')) return 'pending';
        if (statusLower.includes('denied') || statusLower.includes('rejected')) return 'denied';
        return 'unknown';
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
