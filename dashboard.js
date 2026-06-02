console.log('HTML Loaded - Setting up Dashboard');

const distanceInput = document.getElementById('distance');
const orderHourInput = document.getElementById('orderHour');
const discountHourInput = document.getElementById('discountHour');

function updateSliderDisplay(input, labelId) {
    const value = parseFloat(input.value);
    const label = document.getElementById(labelId);
    const displayText = labelId === 'hourValue' || labelId === 'discountHourValue'
        ? `${String(parseInt(value)).padStart(2, '0')}:00`
        : value.toFixed(1);
    label.textContent = displayText;
    input.style.setProperty('--value', `${(value - input.min) / (input.max - input.min) * 100}%`);
}

if (distanceInput) {
    distanceInput.addEventListener('input', () => updateSliderDisplay(distanceInput, 'distanceValue'));
    updateSliderDisplay(distanceInput, 'distanceValue');
}

if (orderHourInput) {
    orderHourInput.addEventListener('input', () => updateSliderDisplay(orderHourInput, 'hourValue'));
    updateSliderDisplay(orderHourInput, 'hourValue');
}

if (discountHourInput) {
    discountHourInput.addEventListener('input', () => updateSliderDisplay(discountHourInput, 'discountHourValue'));
    updateSliderDisplay(discountHourInput, 'discountHourValue');
}

async function submitForm(url, values) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(values)
    });
    return response.json();
}

function setResult(element, success, html) {
    element.className = `result ${success ? 'success' : 'error'}`;
    element.innerHTML = html;
}

const deliveryForm = document.getElementById('deliveryForm');
if (deliveryForm) {
    deliveryForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const loading = document.getElementById('deliveryLoading');
        const result = document.getElementById('deliveryResult');
        loading.classList.add('show');

        try {
            const data = await submitForm('/api/predict-delivery', {
                distance: parseFloat(document.getElementById('distance').value),
                items_count: parseInt(document.getElementById('itemsCount').value),
                order_hour: parseInt(document.getElementById('orderHour').value),
                company: document.getElementById('company').value,
                city: document.getElementById('city').value
            });
            loading.classList.remove('show');

            if (data.success) {
                const trendText = data.difference === 0
                    ? 'This order is at the average delivery pace.'
                    : data.difference < 0
                        ? `Estimated ${Math.abs(data.difference)} min faster than average.`
                        : `Estimated ${data.difference} min slower than average.`;
                setResult(result, true, `✓ Estimated Delivery Time: <strong>${data.prediction} minutes</strong><br><span style="font-size:0.95em; opacity:0.9;">${trendText} (Average: ${data.avg_delivery} min)</span>`);
            } else {
                setResult(result, false, `✗ Error: ${data.error}`);
            }
        } catch (error) {
            loading.classList.remove('show');
            setResult(result, false, `✗ Error: ${error.message}`);
        }
    });
}

const discountForm = document.getElementById('discountForm');
if (discountForm) {
    discountForm.addEventListener('submit', async function (e) {
        e.preventDefault();

        const loading = document.getElementById('discountLoading');
        const result = document.getElementById('discountResult');
        loading.classList.add('show');

        try {
            const data = await submitForm('/api/predict-discount', {
                items_count: parseInt(document.getElementById('discountItems').value),
                order_hour: parseInt(document.getElementById('discountHour').value),
                city: document.getElementById('discountCity').value,
                company: document.getElementById('discountCompany').value,
                order_day: document.getElementById('discountOrderDay').value
            });
            loading.classList.remove('show');

            if (data.success) {
                if (data.eligible) {
                    setResult(result, true, `✓ Eligible for Discount! <strong>Confidence: ${data.confidence}%</strong>`);
                } else {
                    setResult(result, false, `✗ Not Eligible for Discount <strong>Confidence: ${data.confidence}%</strong>`);
                }
            } else {
                setResult(result, false, `✗ Error: ${data.error}`);
            }
        } catch (error) {
            loading.classList.remove('show');
            setResult(result, false, `✗ Error: ${error.message}`);
        }
    });
}

async function loadCharts() {
    try {
        console.log('Starting chart load...');
        const response = await fetch('/api/get-charts');
        const chartData = await response.json();
        console.log('Chart data received:', chartData);

        const chartOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: 'rgba(255, 255, 255, 0.8)',
                        font: { size: 12, weight: 'bold' }
                    }
                }
            },
            scales: {
                y: {
                    ticks: { color: 'rgba(255, 255, 255, 0.7)', font: { size: 11 } },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                x: {
                    ticks: { color: 'rgba(255, 255, 255, 0.7)', font: { size: 11 } },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            }
        };

        const companyPalette = ['#4cacff', '#ffb3e6', '#a78bfa', '#67d7b4', '#f6ad55', '#90cdf4', '#f687b3', '#a0aec0'];

        function buildChart(id, config) {
            const ctx = document.getElementById(id);
            if (ctx) new Chart(ctx.getContext('2d'), config);
        }

        buildChart('peakHoursChart', {
            type: 'line',
            data: {
                labels: chartData.delivery_by_hour.labels,
                datasets: [{
                    label: 'Avg Delivery Time (min)',
                    data: chartData.delivery_by_hour.data,
                    borderColor: '#4cacff',
                    backgroundColor: 'rgba(76, 202, 255, 0.15)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3,
                    pointRadius: 5,
                    pointBackgroundColor: '#ffb3e6',
                    pointBorderColor: 'white',
                    pointBorderWidth: 2
                }]
            },
            options: { ...chartOptions, plugins: { ...chartOptions.plugins, legend: { display: true, position: 'top' } }, interaction: { mode: 'index', intersect: false } }
        });

        buildChart('deliveryEfficiencyChart', {
            type: 'scatter',
            data: {
                datasets: [{
                    label: 'Delivery Efficiency',
                    data: chartData.delivery_efficiency.distances.map((d, i) => ({ x: d, y: chartData.delivery_efficiency.delivery_times[i] })),
                    borderColor: '#ffb3e6',
                    backgroundColor: 'rgba(255, 179, 230, 0.6)',
                    pointRadius: 8,
                    pointBorderWidth: 2,
                    pointBorderColor: 'white'
                }]
            },
            options: { ...chartOptions, scales: { x: { title: { display: true, text: 'Distance (km)', color: 'rgba(255, 255, 255, 0.8)' }, ...chartOptions.scales.x }, y: { title: { display: true, text: 'Delivery Time (min)', color: 'rgba(255, 255, 255, 0.8)' }, ...chartOptions.scales.y } }, plugins: { ...chartOptions.plugins, legend: { display: true } } }
        });

        buildChart('companyRevenueChart', {
            type: 'bar',
            data: {
                labels: chartData.company_revenue.labels,
                datasets: [{
                    label: 'Revenue (₹)',
                    data: chartData.company_revenue.revenue,
                    backgroundColor: 'rgba(76, 202, 255, 0.8)',
                    borderColor: '#4cacff',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: { ...chartOptions, indexAxis: 'y', plugins: { ...chartOptions.plugins, legend: { display: false } } }
        });

        buildChart('darkStoreChart', {
            type: 'line',
            data: {
                labels: chartData.dark_stores.labels,
                datasets: [{
                    label: 'Avg Delivery Time (min)',
                    data: chartData.dark_stores.delivery_time,
                    borderColor: '#a78bfa',
                    backgroundColor: 'rgba(167, 139, 250, 0.1)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3,
                    pointRadius: 7,
                    pointBackgroundColor: '#ffb3e6',
                    pointBorderColor: 'white',
                    pointBorderWidth: 2
                }]
            },
            options: { ...chartOptions, plugins: { ...chartOptions.plugins, legend: { display: true } } }
        });

        buildChart('cityPerformanceChart', {
            type: 'bar',
            data: {
                labels: chartData.city_performance.labels,
                datasets: [{
                    label: 'Orders',
                    data: chartData.city_performance.orders,
                    backgroundColor: 'rgba(76, 202, 255, 0.7)',
                    borderColor: '#4cacff',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: { ...chartOptions, plugins: { ...chartOptions.plugins, legend: { display: false } } }
        });

        buildChart('customerRatingChart', {
            type: 'bar',
            data: {
                labels: chartData.rating_by_company.labels,
                datasets: [{
                    label: 'Avg Customer Rating',
                    data: chartData.rating_by_company.ratings,
                    backgroundColor: 'rgba(255, 179, 230, 0.8)',
                    borderColor: '#ffb3e6',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: { ...chartOptions, plugins: { ...chartOptions.plugins, legend: { display: false } }, scales: { ...chartOptions.scales, y: { ...chartOptions.scales.y, suggestedMin: 0, suggestedMax: 5 } } }
        });

        buildChart('overloadedRegionsChart', {
            type: 'bar',
            data: {
                labels: chartData.overloaded_darkstore_regions.labels,
                datasets: [{
                    label: 'Demand per Store',
                    data: chartData.overloaded_darkstore_regions.demand_per_store,
                    backgroundColor: 'rgba(167, 139, 250, 0.85)',
                    borderColor: '#a78bfa',
                    borderWidth: 2,
                    borderRadius: 8
                }]
            },
            options: { ...chartOptions, indexAxis: 'y', plugins: { ...chartOptions.plugins, legend: { display: false } }, scales: { x: { ...chartOptions.scales.x, title: { display: true, text: 'Demand per Store', color: 'rgba(255,255,255,0.8)' } }, y: { ...chartOptions.scales.y, title: { display: true, text: 'Region', color: 'rgba(255,255,255,0.8)' } } } }
        });

        const loadEfficiencyPoints = chartData.operational_load_efficiency.points;
        const loadEfficiencyDatasets = Array.from(
            loadEfficiencyPoints.reduce((map, point) => {
                if (!map.has(point.company)) {
                    map.set(point.company, []);
                }
                map.get(point.company).push(point);
                return map;
            }, new Map())
        ).map(([company, points], idx) => ({
            label: company,
            data: points.map(p => ({ x: p.demand_per_store, y: p.avg_delivery_time, r: Math.max(5, Math.sqrt(p.total_orders) * 0.8) })),
            backgroundColor: companyPalette[idx % companyPalette.length],
            borderColor: 'rgba(255,255,255,0.8)',
            borderWidth: 1
        }));

        buildChart('loadEfficiencyChart', {
            type: 'bubble',
            data: {
                datasets: loadEfficiencyDatasets
            },
            options: {
                ...chartOptions,
                scales: {
                    x: { ...chartOptions.scales.x, title: { display: true, text: 'Demand per Store', color: 'rgba(255,255,255,0.8)' } },
                    y: { ...chartOptions.scales.y, title: { display: true, text: 'Avg Delivery Time (min)', color: 'rgba(255,255,255,0.8)' } }
                },
                plugins: { ...chartOptions.plugins, legend: { display: true, position: 'bottom' } }
            }
        });

        buildChart('valueRatingChart', {
            type: 'line',
            data: {
                labels: chartData.value_rating.labels,
                datasets: [{
                    label: 'Avg Order Value (₹)',
                    data: chartData.value_rating.values,
                    borderColor: '#ffb3e6',
                    backgroundColor: 'rgba(255, 179, 230, 0.1)',
                    tension: 0.4,
                    fill: true,
                    borderWidth: 3,
                    pointRadius: 6,
                    pointBackgroundColor: '#4cacff',
                    pointBorderColor: 'white',
                    pointBorderWidth: 2
                }]
            },
            options: { ...chartOptions, plugins: { ...chartOptions.plugins, legend: { display: true } } }
        });
    } catch (error) {
        console.error('Error loading charts:', error);
        const chartsSection = document.querySelector('.charts-grid');
        if (chartsSection) {
            chartsSection.innerHTML = '<div style="color: #ffb3e6; padding: 20px; text-align: center;"><strong>Error loading charts. Open console for details.</strong><br/>' + error.message + '</div>';
        }
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', loadCharts);
} else {
    loadCharts();
}
