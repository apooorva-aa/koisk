function loadStats() {
    document.getElementById('total-users').textContent = '47';
    document.getElementById('text-chats').textContent = '89';
    document.getElementById('voice-chats').textContent = '56';
    document.getElementById('place-searches').textContent = '34';

    drawUsageChart();
    drawFeatureChart();
}

function drawUsageChart() {
    const canvas = document.getElementById('usage-chart');
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    ctx.fillStyle = '#2a2a2a';
    ctx.fillRect(0, 0, width, height);

    const data = [25, 35, 28, 42, 38, 47, 52];
    const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const max = Math.max(...data);
    const barWidth = width / data.length - 20;
    const padding = 40;

    ctx.strokeStyle = '#444';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
        const y = height - padding - (height - 2 * padding) * (i / 5);
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
    }

    ctx.fillStyle = '#4CAF50';
    data.forEach((value, index) => {
        const barHeight = ((height - 2 * padding) * value) / max;
        const x = padding + index * (width - 2 * padding) / data.length + 10;
        const y = height - padding - barHeight;

        ctx.fillRect(x, y, barWidth, barHeight);

        ctx.fillStyle = '#fff';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';
        ctx.fillText(labels[index], x + barWidth / 2, height - padding + 20);
        ctx.fillStyle = '#4CAF50';
    });
}

function drawFeatureChart() {
    const canvas = document.getElementById('feature-chart');
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;

    ctx.fillStyle = '#2a2a2a';
    ctx.fillRect(0, 0, width, height);

    const data = [
        { label: 'Text Chat', value: 89, color: '#4CAF50' },
        { label: 'Voice Chat', value: 56, color: '#2196F3' },
        { label: 'Place Search', value: 34, color: '#FF9800' },
        { label: 'Contact Info', value: 21, color: '#9C27B0' }
    ];

    const total = data.reduce((sum, item) => sum + item.value, 0);
    let currentAngle = -Math.PI / 2;
    const centerX = width / 2 - 80;
    const centerY = height / 2;
    const radius = Math.min(width, height) / 3;

    data.forEach((item, index) => {
        const sliceAngle = (item.value / total) * 2 * Math.PI;

        ctx.beginPath();
        ctx.fillStyle = item.color;
        ctx.moveTo(centerX, centerY);
        ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
        ctx.closePath();
        ctx.fill();

        currentAngle += sliceAngle;
    });

    let legendY = 60;
    data.forEach((item) => {
        ctx.fillStyle = item.color;
        ctx.fillRect(width - 180, legendY, 20, 20);

        ctx.fillStyle = '#fff';
        ctx.font = '14px Arial';
        ctx.textAlign = 'left';
        ctx.fillText(`${item.label}: ${item.value}`, width - 150, legendY + 15);

        legendY += 40;
    });
}
