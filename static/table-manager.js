/**
 * Secure Feedback Platform - Client-side Table Manager
 * Handles Filtering and Sorting for Admin and Authority Dashboards.
 */

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('tableSearch');
    const typeFilter = document.getElementById('typeFilter');
    const ratingFilter = document.getElementById('ratingFilter');
    const feedbackTable = document.querySelector('.table-hover');
    
    if (!feedbackTable) return;

    const tableBody = feedbackTable.querySelector('tbody');
    const rows = Array.from(tableBody.querySelectorAll('tr'));
    const headers = feedbackTable.querySelectorAll('.sort-header');

    // --- Filtering Logic ---
    function performFilter() {
        const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
        const selectedType = typeFilter ? typeFilter.value.toLowerCase() : 'all';
        const selectedRating = ratingFilter ? ratingFilter.value : 'all';

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            const typeText = row.querySelector('.badge-fixed-width')?.textContent.toLowerCase() || '';
            const scoreText = row.querySelector('.col-score .fw-bold')?.textContent || '';
            
            const matchesSearch = text.includes(searchTerm);
            const matchesType = selectedType === 'all' || typeText.includes(selectedType);
            const matchesRating = selectedRating === 'all' || (scoreText.trim() === selectedRating);

            if (matchesSearch && matchesType && matchesRating) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    if (searchInput) searchInput.addEventListener('input', performFilter);
    if (typeFilter) typeFilter.addEventListener('change', performFilter);
    if (ratingFilter) ratingFilter.addEventListener('change', performFilter);

    // --- Sorting Logic ---
    headers.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.dataset.sort;
            const isAsc = header.classList.contains('sort-asc');
            
            // Reset all headers
            headers.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
            
            // Set new state
            header.classList.toggle('sort-asc', !isAsc);
            header.classList.toggle('sort-desc', isAsc);

            const sortedRows = rows.sort((a, b) => {
                let aVal = a.querySelector(`[data-col="${column}"]`)?.textContent.trim() || '';
                let bVal = b.querySelector(`[data-col="${column}"]`)?.textContent.trim() || '';

                // Handle numeric sorting for scores
                if (column === 'score') {
                    aVal = parseFloat(aVal) || 0;
                    bVal = parseFloat(bVal) || 0;
                    return isAsc ? bVal - aVal : aVal - bVal;
                }

                // Handle Date sorting
                if (column === 'date') {
                    return isAsc ? new Date(bVal) - new Date(aVal) : new Date(aVal) - new Date(bVal);
                }

                // Default string sort
                return isAsc 
                    ? bVal.localeCompare(aVal) 
                    : aVal.localeCompare(bVal);
            });

            // Re-append sorted rows
            tableBody.append(...sortedRows);
        });
    });
});
