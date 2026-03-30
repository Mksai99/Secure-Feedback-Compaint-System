/**
 * Secure Feedback Platform - Client-side Table Manager
 * Handles Filtering and Sorting for Admin and Authority Dashboards.
 */

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('tableSearch');
    const typeFilter = document.getElementById('typeFilter');
    const ratingFilter = document.getElementById('ratingFilter');
    const feedbackTable = document.querySelector('.feedback-table');
    
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
            const typeValue = row.dataset.type || '';
            // Fix: Use data-col="score" selector for finding the score value
            const scoreText = row.querySelector('[data-col="score"]')?.textContent.trim() || '';
            
            const matchesSearch = text.includes(searchTerm);
            const matchesType = selectedType === 'all' || typeValue === selectedType;
            const matchesRating = selectedRating === 'all' || (scoreText.startsWith(selectedRating));

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
            
            // Toggle logic: If it was ASC, it becomes DESC. If it was DESC or none, it becomes ASC.
            const newIsAsc = !isAsc;
            header.classList.add(newIsAsc ? 'sort-asc' : 'sort-desc');

            const sortedRows = rows.sort((a, b) => {
                let aEl = a.querySelector(`[data-col="${column}"]`);
                let bEl = b.querySelector(`[data-col="${column}"]`);
                
                let aVal = aEl?.textContent.trim() || '';
                let bVal = bEl?.textContent.trim() || '';

                // Handle numeric sorting for scores
                if (column === 'score') {
                    aVal = parseFloat(aVal) || 0;
                    bVal = parseFloat(bVal) || 0;
                    return newIsAsc ? aVal - bVal : bVal - aVal;
                }

                // Handle Date sorting
                if (column === 'date') {
                    // Try to parse date strings (e.g. YYYY-MM-DD)
                    let aDate = new Date(aVal);
                    let bDate = new Date(bVal);
                    if (isNaN(aDate.getTime())) aDate = new Date(0);
                    if (isNaN(bDate.getTime())) bDate = new Date(0);
                    return newIsAsc ? aDate - bDate : bDate - aDate;
                }

                // Default string sort
                return newIsAsc 
                    ? aVal.localeCompare(bVal) 
                    : bVal.localeCompare(aVal);
            });

            // Re-append sorted rows
            tableBody.append(...sortedRows);
        });
    });
});
