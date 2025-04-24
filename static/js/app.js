// Chart.js initialization
let expiryChart = null;

async function updateExpiryChart() {
    try {
        const response = await fetch('/api/expiring_soon');
        const data = await response.json();
        
        const ctx = document.getElementById('expiryChart').getContext('2d');
        
        if (expiryChart) {
            expiryChart.destroy();
        }
        
        expiryChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(item => item.name),
                datasets: [{
                    label: 'Days until expiry',
                    data: data.map(item => item.days_left),
                    backgroundColor: data.map(item => {
                        const days = item.days_left;
                        return days <= 1 ? '#dc3545' : 
                               days <= 3 ? '#ffc107' : '#28a745';
                    })
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Days Remaining'
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error updating chart:', error);
    }
}

// Modal form handling
function setupModalForms() {
    const editButtons = document.querySelectorAll('.edit-item-btn');
    editButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            const itemData = JSON.parse(e.target.dataset.item);
            const form = document.querySelector('#editItemModal form');
            form.elements.name.value = itemData.name;
            form.elements.quantity.value = itemData.quantity;
            form.elements.category.value = itemData.category;
            form.elements.expiry_date.value = itemData.expiry_date;
            form.action = `/update_item/${itemData.id}`;
        });
    });
}

// Dark mode functionality
function setupDarkMode() {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const body = document.body;

    // Function to set dark mode
    function setDarkMode(enabled) {
        if (enabled) {
            body.classList.add('dark-mode');
            localStorage.setItem('darkMode', 'enabled');
        } else {
            body.classList.remove('dark-mode');
            localStorage.setItem('darkMode', 'disabled');
        }
    }

    // Initialize dark mode from localStorage
    if (localStorage.getItem('darkMode') === 'enabled') {
        setDarkMode(true);
        if (darkModeToggle) darkModeToggle.checked = true;
    }

    // Dark mode toggle event listener
    if (darkModeToggle) {
        darkModeToggle.addEventListener('change', (e) => {
            setDarkMode(e.target.checked);
            
            // Send dark mode preference to server
            fetch('/update_dark_mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    dark_mode: e.target.checked
                })
            });
        });
    }
}

// View toggle functionality
function setupViewToggle() {
    const toggleBtn = document.getElementById('toggleView');
    const itemsContainer = document.getElementById('itemsContainer');
    
    if (toggleBtn && itemsContainer) {
        toggleBtn.addEventListener('click', () => {
            itemsContainer.classList.toggle('table-view');
            itemsContainer.classList.toggle('card-view');
            localStorage.setItem('viewPreference', 
                itemsContainer.classList.contains('card-view') ? 'card' : 'table');
        });
        
        // Apply saved preference
        const savedView = localStorage.getItem('viewPreference') || 'table';
        if (savedView === 'card') {
            itemsContainer.classList.remove('table-view');
            itemsContainer.classList.add('card-view');
        }
    }
}

// Print list functionality
function setupPrintList() {
    const printButton = document.getElementById('printList');
    if (printButton) {
        printButton.addEventListener('click', () => {
            const printWindow = window.open('', '_blank');
            const itemsContainer = document.getElementById('itemsContainer').cloneNode(true);
            
            // Remove action buttons from print view
            const actionButtons = itemsContainer.querySelectorAll('.btn-group');
            actionButtons.forEach(button => button.remove());
            
            printWindow.document.write(`
                <html>
                    <head>
                        <title>Grocery List</title>
                        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
                        <style>
                            body { padding: 20px; }
                            .card { margin-bottom: 10px; }
                            @media print {
                                .no-print { display: none; }
                            }
                        </style>
                    </head>
                    <body>
                        <h1>My Grocery List</h1>
                        <div class="container">
                            ${itemsContainer.innerHTML}
                        </div>
                        <script>
                            window.onload = function() {
                                window.print();
                                window.close();
                            }
                        </script>
                    </body>
                </html>
            `);
        });
    }
}

// Share list functionality
function setupShareList() {
    const shareButton = document.getElementById('shareList');
    if (shareButton) {
        shareButton.addEventListener('click', async () => {
            try {
                const response = await fetch('/share_list/{{ session.user_id }}');
                const data = await response.json();
                
                if (data.success) {
                    // Create modal for sharing
                    const modal = document.createElement('div');
                    modal.className = 'modal fade';
                    modal.innerHTML = `
                        <div class="modal-dialog">
                            <div class="modal-content">
                                <div class="modal-header">
                                    <h5 class="modal-title">Share Your List</h5>
                                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body text-center">
                                    <img src="data:image/png;base64,${data.qr_code}" alt="QR Code" class="img-fluid mb-3">
                                    <p>Scan this QR code to view your list</p>
                                    <div class="input-group mb-3">
                                        <input type="text" class="form-control" id="shareUrl" value="${window.location.origin}" readonly>
                                        <button class="btn btn-outline-secondary" type="button" id="copyShareUrl">
                                            <i class="bi bi-clipboard"></i>
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                    
                    document.body.appendChild(modal);
                    const modalInstance = new bootstrap.Modal(modal);
                    modalInstance.show();
                    
                    // Copy URL functionality
                    document.getElementById('copyShareUrl').addEventListener('click', function() {
                        const shareUrl = document.getElementById('shareUrl');
                        shareUrl.select();
                        document.execCommand('copy');
                        this.innerHTML = '<i class="bi bi-check"></i>';
                        setTimeout(() => {
                            this.innerHTML = '<i class="bi bi-clipboard"></i>';
                        }, 2000);
                    });
                    
                    // Clean up modal on close
                    modal.addEventListener('hidden.bs.modal', function() {
                        document.body.removeChild(modal);
                    });
                }
            } catch (error) {
                console.error('Error sharing list:', error);
                alert('Error sharing list. Please try again.');
            }
        });
    }
}

// Notification functionality
function setupNotifications() {
    const notificationButton = document.getElementById('notificationButton');
    const notificationBadge = document.getElementById('notificationBadge');
    const notificationList = document.getElementById('notificationList');
    
    async function checkNotifications() {
        try {
            const response = await fetch('/notifications');
            const data = await response.json();
            
            if (data.success && data.notifications.length > 0) {
                notificationBadge.textContent = data.notifications.length;
                notificationBadge.classList.remove('d-none');
                
                notificationList.innerHTML = data.notifications.map(notification => `
                    <div class="dropdown-item-text">
                        <div class="d-flex align-items-center">
                            <i class="bi bi-exclamation-triangle-fill text-warning me-2"></i>
                            <div>
                                <div class="fw-bold">${notification.message}</div>
                                <div class="small text-muted">
                                    ${notification.items.map(item => 
                                        `${item.name} (${item.expiry_date})`
                                    ).join(', ')}
                                </div>
                            </div>
                        </div>
                    </div>
                `).join('');
            } else {
                notificationBadge.classList.add('d-none');
                notificationList.innerHTML = `
                    <div class="text-center text-muted">
                        <small>No new notifications</small>
                    </div>
                `;
            }
        } catch (error) {
            console.error('Error checking notifications:', error);
        }
    }
    
    // Check notifications every minute
    setInterval(checkNotifications, 60000);
    // Initial check
    checkNotifications();
}

// Initialize all features
document.addEventListener('DOMContentLoaded', () => {
    updateExpiryChart();
    setupModalForms();
    setupDarkMode();
    setupViewToggle();
    setupPrintList();
    setupShareList();
    setupNotifications();
    
    // Update chart periodically
    setInterval(updateExpiryChart, 300000); // Every 5 minutes
}); 