// Script vẽ biểu đồ Dashboard Admin (Do Bảo phụ trách)
document.addEventListener('DOMContentLoaded', function () {
    // 1. Biểu đồ Doanh thu (Bar Chart)
    initRevenueChart();

    // 2. Biểu đồ Trạng thái đơn hàng (Doughnut Chart)
    initOrderStatusChart();

});

// Biến lưu instance chart để tái sử dụng hoặc destroy nếu cần
let revenueChartInstance = null;
let orderStatusChartInstance = null;
let rawStatsData = null;

function initRevenueChart() {
    const ctxRevenue = document.getElementById('revenueChart');
    const metricSelect = document.getElementById('metricSelect');
    if (!ctxRevenue) return;

    fetch('/admin/api/stats/monthly-revenue')
        .then(response => {
            if (!response.ok) throw new Error('Lỗi kết nối API');
            return response.json();
        })
        .then(data => {
            rawStatsData = data; // Lưu dữ liệu vào biến toàn cục

            // Vẽ biểu đồ ban đầu (mặc định là Doanh thu)
            renderChart('revenue');

            // Lắng nghe sự kiện thay đổi tùy chọn chỉ số
            if (metricSelect) {
                metricSelect.addEventListener('change', function () {
                    renderChart(this.value);
                });
            }
        })
        .catch(err => console.error("Lỗi tải biểu đồ:", err));

    function renderChart(metric) {
        if (!rawStatsData) return;

        // Cấu hình nhãn, màu sắc và định dạng số theo từng chỉ số
        const configs = {
            'revenue': {
                label: 'Doanh thu',
                data: rawStatsData.revenues,
                color: 'rgba(13, 110, 253, 0.7)',
                borderColor: 'rgba(13, 110, 253, 1)',
                unit: ' đ'
            },
            'order_counts': {
                label: 'Số đơn thành công',
                data: rawStatsData.order_counts,
                color: 'rgba(25, 135, 84, 0.7)',
                borderColor: 'rgba(25, 135, 84, 1)',
                unit: ' đơn'
            },
            'aov': {
                label: 'Giá trị trung bình/đơn (AOV)',
                data: rawStatsData.aov,
                color: 'rgba(255, 193, 7, 0.7)',
                borderColor: 'rgba(255, 193, 7, 1)',
                unit: ' đ/đơn'
            }
        };

        const config = configs[metric];

        if (revenueChartInstance) revenueChartInstance.destroy();

        revenueChartInstance = new Chart(ctxRevenue, {
            type: 'bar',
            data: {
                labels: rawStatsData.labels,
                datasets: [{
                    label: config.label,
                    data: config.data,
                    backgroundColor: config.color,
                    borderColor: config.borderColor,
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                let val = context.raw || 0;
                                return ` ${config.label}: ${val.toLocaleString('vi-VN')}${config.unit}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (value) {
                                return value.toLocaleString('vi-VN') + config.unit;
                            }
                        }
                    }
                }
            }
        });
    }
}

function initOrderStatusChart() {
    const ctxStatus = document.getElementById('orderStatusChart');
    if (!ctxStatus) return;

    // Bảng màu cố định theo từng tên trạng thái phổ biến
    const colorMap = {
        'Hoàn thành': '#198754', // Xanh lá
        'Thành công': '#198754',
        'Chờ xử lý': '#ffc107',  // Vàng
        'Đang xử lý': '#0dcaf0',  // Xanh nhạt
        'Đang giao': '#0d6efd',   // Xanh dương
        'Đã hủy': '#dc3545'      // Đỏ
    };

    fetch('/admin/api/stats/order-status')
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            if (orderStatusChartInstance) orderStatusChartInstance.destroy();

            // Gán màu tương ứng theo label trả về từ API (nếu không có thì lấy màu xám mặc định)
            const backgroundColors = data.labels.map(label => colorMap[label] || '#6c757d');

            orderStatusChartInstance = new Chart(ctxStatus, {
                type: 'doughnut',
                data: {
                    labels: data.labels,
                    datasets: [{
                        data: data.counts,
                        backgroundColor: backgroundColors
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom' // Đặt chú thích xuống dưới cho gọn card 4 cột
                        }
                    }
                }
            });
        })
        .catch(err => console.error("Lỗi tải biểu đồ trạng thái đơn:", err));
}