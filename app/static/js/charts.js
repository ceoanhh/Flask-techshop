// Script vẽ biểu đồ Dashboard Admin (Do Bảo phụ trách)
document.addEventListener('DOMContentLoaded', function () {
    // 1. Biểu đồ Doanh thu (Line / Bar Chart)
    const ctxRevenue = document.getElementById('revenueChart');
    if (ctxRevenue) {
        fetch('/admin/api/stats/monthly-revenue')
            .then(response => response.json())
            .then(data => {
                new Chart(ctxRevenue, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Doanh thu (VNĐ)',
                            data: data.revenues,
                            backgroundColor: 'rgba(13, 110, 253, 0.7)',
                            borderColor: 'rgba(13, 110, 253, 1)',
                            borderWidth: 1,
                            borderRadius: 6
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { display: false }
                        },
                        scales: {
                            y: {
                                beginAtZero: true,
                                ticks: {
                                    callback: function(value) {
                                        return value.toLocaleString('vi-VN') + ' đ';
                                    }
                                }
                            }
                        }
                    }
                });
            })
            .catch(err => console.error("Lỗi tải biểu đồ doanh thu:", err));
    }

    // 2. Biểu đồ Trạng thái đơn hàng (Doughnut Chart)
    const ctxStatus = document.getElementById('orderStatusChart');
    if (ctxStatus) {
        fetch('/admin/api/stats/order-status')
            .then(response => response.json())
            .then(data => {
                new Chart(ctxStatus, {
                    type: 'doughnut',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            data: data.counts,
                            backgroundColor: [
                                '#198754', // Hoàn thành - Xanh lá
                                '#ffc107', // Chờ xử lý - Vàng
                                '#dc3545'  // Đã hủy - Đỏ
                            ]
                        }]
                    },
                    options: {
                        responsive: true
                    }
                });
            })
            .catch(err => console.error("Lỗi tải biểu đồ trạng thái đơn:", err));
    }
});
