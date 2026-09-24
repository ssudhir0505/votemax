(function () {
    const dataEl = document.getElementById('chart-data');
    if (!dataEl) return;

    const parties = JSON.parse(dataEl.dataset.parties);
    const votes = JSON.parse(dataEl.dataset.votes);
    const ctx = document.getElementById('resultsChart').getContext('2d');

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: parties,
            datasets: [{
                label: 'Votes',
                data: votes,
                backgroundColor: ['#FF9933', '#000080', '#138808'],
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: '#f3f4f6' }
                },
                x: {
                    grid: { display: false }
                }
            }
        }
    });
})();
