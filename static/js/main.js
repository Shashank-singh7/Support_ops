document.addEventListener('DOMContentLoaded', () => {
    fetchStats();
    fetchDiagnostics();
    fetchModelMetrics();

    document.getElementById('train-btn').addEventListener('click', async () => {
        const btn = document.getElementById('train-btn');
        btn.disabled = true;
        btn.innerText = 'Training...';
        try {
            const resp = await fetch('/train', { method: 'POST' });
            const data = await resp.json();
            alert(`Model trained!`);
            updateMetricsUI(data.metrics);
        } catch (e) {
            alert('Training failed.');
        } finally {
            btn.disabled = false;
            btn.innerText = 'Train Model';
        }
    });

    document.getElementById('reingest-btn').addEventListener('click', async () => {
        const btn = document.getElementById('reingest-btn');
        btn.disabled = true;
        btn.innerText = 'Processing...';
        try {
            const resp = await fetch('/reingest', { method: 'POST' });
            const data = await resp.json();
            if (data.error) throw new Error(data.error);
            alert(`Success! Ingested ${data.diagnostics.tickets_ingested} tickets.`);
            fetchStats(); // Refresh dashboard
            fetchDiagnostics(); // Refresh diagnostics
        } catch (e) {
            alert('Ingestion failed: ' + e.message);
        } finally {
            btn.disabled = false;
            btn.innerText = 'Re-run Ingestion';
        }
    });

    document.getElementById('predict-form').addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const jsonData = Object.fromEntries(formData.entries());

        // Ensure numeric fields are numbers
        jsonData.tenure_months = parseInt(jsonData.tenure_months);
        jsonData.employees = parseInt(jsonData.employees);

        const resultDiv = document.getElementById('prediction-result');
        resultDiv.style.display = 'block';
        resultDiv.innerText = 'Predicting...';
        resultDiv.style.background = 'rgba(255,255,255,0.1)';

        try {
            const resp = await fetch('/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(jsonData)
            });
            const data = await resp.json();
            if (data.error) {
                resultDiv.innerText = data.error;
                resultDiv.style.background = '#ef444422';
            } else {
                const prob = (data.probability * 100).toFixed(1);
                resultDiv.innerHTML = `Probability of Breach: <strong>${prob}%</strong><br>
                                       Result: <strong>${data.label === 1 ? 'WILL BREACH' : 'SAFE'}</strong>`;
                resultDiv.style.background = data.label === 1 ? '#ef444422' : '#10b98122';
            }
        } catch (err) {
            resultDiv.innerText = 'Prediction failed.';
        }
    });
});

async function fetchStats() {
    try {
        const resp = await fetch('/stats/overview');
        const data = await resp.json();

        document.getElementById('breach-rate').innerText = data.sla_breach_rate.toFixed(1) + '%';
        document.getElementById('median-res').innerText = data.median_resolution_time.toFixed(1) + 'h';
        document.getElementById('p95-res').innerText = data.p95_resolution_time.toFixed(1) + 'h';

        const total = Object.values(data.daily_volume).reduce((a, b) => a + b, 0);
        document.getElementById('total-tickets').innerText = total;

        // Problems table
        const custBody = document.querySelector('#customer-table tbody');
        custBody.innerHTML = data.problem_customers.map(c => `
            <tr>
                <td>${c.customer_id}</td>
                <td style="color: var(--danger)">${c.breach_rate.toFixed(1)}%</td>
                <td>${c.total_tickets}</td>
            </tr>
        `).join('');

        // Categories table
        const catBody = document.querySelector('#category-table tbody');
        catBody.innerHTML = data.top_categories.map(c => `
            <tr>
                <td>${c[0]}</td>
                <td>${c[1]}</td>
            </tr>
        `).join('');

    } catch (e) {
        console.error('Failed to fetch stats', e);
    }
}

async function fetchDiagnostics() {
    try {
        const resp = await fetch('/diagnostics');
        const data = await resp.json();

        document.getElementById('diag-tickets').innerText = data.ticket_count;
        document.getElementById('diag-dirty').innerText = data.dirty_count;

        const issueList = document.getElementById('issue-list');
        if (data.issues.length === 0) {
            issueList.innerHTML = '<li style="color: #10b981;">No data quality issues found!</li>';
        } else {
            issueList.innerHTML = data.issues.map(issue => `<li>• ${issue}</li>`).join('');
            if (data.dirty_count > 50) {
                issueList.innerHTML += `<li style="margin-top: 0.5rem; color: #6366f1;">... and ${data.dirty_count - 50} more issues.</li>`;
            }
        }
    } catch (e) {
        console.error('Failed to fetch diagnostics', e);
    }
}

async function fetchModelMetrics() {
    try {
        const resp = await fetch('/model/metrics');
        if (resp.ok) {
            const data = await resp.json();
            updateMetricsUI(data);
        }
    } catch (e) {
        console.error('Failed to fetch model metrics', e);
    }
}

function updateMetricsUI(metrics) {
    if (!metrics) return;

    document.getElementById('auc-value').innerText = metrics.auc.toFixed(3);
    document.getElementById('f1-value').innerText = metrics.f1.toFixed(3);

    const cm = metrics.confusion_matrix;
    if (cm) {
        document.getElementById('cm-00').innerText = cm[0][0];
        document.getElementById('cm-01').innerText = cm[0][1];
        document.getElementById('cm-10').innerText = cm[1][0];
        document.getElementById('cm-11').innerText = cm[1][1];
    }
}
