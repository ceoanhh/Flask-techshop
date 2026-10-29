document.addEventListener('DOMContentLoaded', function () {
    // 1. Biểu đồ Doanh thu / Đơn hàng / AOV (Tổng + Theo Category)
    initRevenueChart();

    // 2. Biểu đồ Trạng thái đơn hàng (Doughnut Chart)
    initOrderStatusChart();

    // 3. Biểu đồ Top 5 sản phẩm bán chạy (Cột ngang Chart.js)
    initTopProductsChart();

    // 4. Bảng danh sách Top 5 sản phẩm bán chạy (Giao diện bảng thu nhỏ)
    initTopProductsTable();

    // 5. Bảng danh sách sản phẩm sắp hết hàng (Low Stock)
    initLowStockTable();


    initAdvancedAnalytics();


    initPeakHoursChart();
});

// Biến lưu trữ Instance của Chart.js để destroy khi render lại
let revenueChartInstance = null;
let orderStatusChartInstance = null;
let topProductsChartInstance = null;
let peakHoursChartInstance = null;

let globalMainStats = null;
let globalCategoryStats = null;

/**
 * 1. KHỞI TẠO BIỂU ĐỒ DOANH THU & CHỈ SỐ THEO CATEGORY
 */
function initRevenueChart() {
    const ctxRevenue = document.getElementById('revenueChart');
    const metricSelect = document.getElementById('metricSelect');
    if (!ctxRevenue) return;

    // Tải đồng thời dữ liệu Thống kê tổng & Thống kê theo Danh mục
    Promise.all([
        fetch('/admin/api/stats/monthly-revenue').then(res => res.json()),
        fetch('/admin/api/stats/category-revenue').then(res => res.json())
    ])
    .then(([mainData, categoryData]) => {
        globalMainStats = mainData;
        globalCategoryStats = categoryData;

        // Mặc định render Doanh thu
        renderGroupedChart('revenue');

        if (metricSelect) {
            metricSelect.addEventListener('change', function () {
                renderGroupedChart(this.value);
            });
        }
    })
    .catch(err => console.error("Lỗi tải dữ liệu biểu đồ doanh thu:", err));

    function renderGroupedChart(metric) {
        if (!globalMainStats || !globalCategoryStats) return;

        let datasets = [];
        let unit = ' đ';

        if (metric === 'revenue') {
            unit = ' đ';
            // Cột Tổng Doanh thu
            datasets.push({
                label: 'Tổng Doanh Thu',
                data: globalMainStats.revenues,
                backgroundColor: 'rgba(13, 110, 253, 0.85)',
                borderColor: 'rgba(13, 110, 253, 1)',
                borderWidth: 2,
                borderRadius: 6
            });
            // Cột phụ Doanh thu từng Category
            datasets = datasets.concat(globalCategoryStats.category_revenues || []);

        } else if (metric === 'order_counts') {
            unit = ' đơn';
            // Cột Tổng Số đơn
            datasets.push({
                label: 'Tổng số đơn thành công',
                data: globalMainStats.order_counts,
                backgroundColor: 'rgba(25, 135, 84, 0.85)',
                borderColor: 'rgba(25, 135, 84, 1)',
                borderWidth: 2,
                borderRadius: 6
            });
            // Cột phụ Số đơn chứa sản phẩm của từng Category
            datasets = datasets.concat(globalCategoryStats.category_orders || []);

        } else if (metric === 'aov') {
            unit = ' đ/đơn';
            // Cột Tổng AOV
            datasets.push({
                label: 'AOV Trung bình toàn hệ thống',
                data: globalMainStats.aov,
                backgroundColor: 'rgba(255, 193, 7, 0.85)',
                borderColor: 'rgba(255, 193, 7, 1)',
                borderWidth: 2,
                borderRadius: 6
            });
            // Cột phụ AOV của từng Category
            datasets = datasets.concat(globalCategoryStats.category_aov || []);
        }

        if (revenueChartInstance) revenueChartInstance.destroy();

        revenueChartInstance = new Chart(ctxRevenue, {
            type: 'bar',
            data: {
                labels: globalMainStats.labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                let val = context.raw || 0;
                                return ` ${context.dataset.label}: ${val.toLocaleString('vi-VN')}${unit}`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function (value) {
                                return value.toLocaleString('vi-VN') + unit;
                            }
                        }
                    }
                }
            }
        });
    }
}

/**
 * 2. KHỞI TẠO BIỂU ĐỒ DOUGHNUT TRẠNG THÁI ĐƠN HÀNG
 */
function initOrderStatusChart() {
    const ctxStatus = document.getElementById('orderStatusChart');
    if (!ctxStatus) return;

    const colorMap = {
        'Hoàn thành': '#198754',
        'Thành công': '#198754',
        'Chờ xử lý': '#ffc107',
        'Đang xử lý': '#0dcaf0',
        'Đang giao': '#0d6efd',
        'Đã hủy': '#dc3545'
    };

    fetch('/admin/api/stats/order-status')
        .then(response => {
            if (!response.ok) throw new Error('Lỗi kết nối API order-status');
            return response.json();
        })
        .then(data => {
            if (orderStatusChartInstance) orderStatusChartInstance.destroy();

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
                        legend: { position: 'bottom' }
                    }
                }
            });
        })
        .catch(err => console.error("Lỗi tải biểu đồ trạng thái đơn:", err));
}

/**
 * 3. KHỞI TẠO BIỂU ĐỒ CỘT NGANG TOP 5 SẢN PHẨM BÁN CHẠY
 */
function initTopProductsChart() {
    const ctxTopProducts = document.getElementById('topProductsChart');
    if (!ctxTopProducts) return;

    fetch('/admin/api/stats/top-products')
        .then(response => {
            if (!response.ok) throw new Error('Lỗi tải API top-products');
            return response.json();
        })
        .then(data => {
            if (topProductsChartInstance) topProductsChartInstance.destroy();

            topProductsChartInstance = new Chart(ctxTopProducts, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Số lượng đã bán',
                        data: data.quantities,
                        backgroundColor: 'rgba(255, 193, 7, 0.85)',
                        borderColor: 'rgba(255, 193, 7, 1)',
                        borderWidth: 1,
                        borderRadius: 6
                    }]
                },
                options: {
                    indexAxis: 'y', // Chuyển sang biểu đồ cột ngang
                    responsive: true,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: function (context) {
                                    let val = context.raw || 0;
                                    return ` Số lượng bán: ${val.toLocaleString('vi-VN')} sản phẩm`;
                                }
                            }
                        }
                    },
                    scales: {
                        x: {
                            beginAtZero: true,
                            ticks: { precision: 0 }
                        },
                        y: { grid: { display: false } }
                    }
                }
            });
        })
        .catch(err => console.error("Lỗi tải biểu đồ Top 5 sản phẩm:", err));
}

/**
 * 4. ĐỔ DỮ LIỆU BẢNG TOP 5 SẢN PHẨM (BẢNG THU NHỎ)
 */
function initTopProductsTable() {
    const tbody = document.getElementById('topProductsBody');
    if (!tbody) return;

    fetch('/admin/api/stats/top-products-list')
        .then(response => response.json())
        .then(data => {
            if (!data || data.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center py-3 text-muted">Chưa có dữ liệu bán hàng.</td>
                    </tr>`;
                return;
            }

            let html = '';
            data.forEach((item, index) => {
                let rankBadge = `<span class="fw-bold text-muted">${index + 1}</span>`;
                if (index === 0) rankBadge = '<span class="badge bg-warning text-dark">1</span>';
                else if (index === 1) rankBadge = '<span class="badge bg-secondary">2</span>';
                else if (index === 2) rankBadge = '<span class="badge bg-danger">3</span>';

                html += `
                    <tr>
                        <td class="ps-3 py-2">${rankBadge}</td>
                        <td class="fw-bold text-dark py-2 text-truncate" style="max-width: 150px;" title="${item.name}">${item.name}</td>
                        <td class="text-center fw-bold text-primary py-2">${item.total_sold.toLocaleString('vi-VN')}</td>
                        <td class="text-end pe-3 fw-bold text-success py-2">${item.total_revenue.toLocaleString('vi-VN')} đ</td>
                    </tr>
                `;
            });

            tbody.innerHTML = html;
        })
        .catch(err => {
            console.error("Lỗi tải bảng Top 5 sản phẩm:", err);
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="text-center py-3 text-danger">Không thể tải dữ liệu.</td>
                </tr>`;
        });
}

/**
 * 5. ĐỔ DỮ LIỆU BẢNG CẢNH BÁO HẾT HÀNG (LOW STOCK)
 */
function initLowStockTable() {
    const tbody = document.getElementById('lowStockBody');
    if (!tbody) return;

    fetch('/admin/api/stats/low-stock?threshold=10')
        .then(response => {
            if (!response.ok) throw new Error('Lỗi tải dữ liệu kho hàng');
            return response.json();
        })
        .then(data => {
            console.log("Dữ liệu tồn kho nhận từ API:", data);

            if (!data || data.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="6" class="text-center py-3 text-success fw-bold">
                            <i class="bi bi-check-circle me-1"></i> Tồn kho an toàn!
                        </td>
                    </tr>`;
                return;
            }

            let html = '';
            data.forEach(item => {
                let stockBadge = item.stock_quantity === 0
                    ? '<span class="badge bg-danger">Hết (0)</span>'
                    : `<span class="badge bg-warning text-dark">Còn ${item.stock_quantity}</span>`;

                html += `
                    <tr>
                        <td class="ps-3 fw-bold text-muted py-2">#${item.id}</td>
                        <td class="fw-bold text-dark py-2 text-truncate" style="max-width: 160px;" title="${item.name}">${item.name}</td>
                        <td class="py-2"><span class="badge bg-light text-dark border">${item.category}</span></td>
                        <td class="py-2">${item.price.toLocaleString('vi-VN')} đ</td>
                        <td class="text-center py-2">${stockBadge}</td>
                    </tr>
                `;
            });

            tbody.innerHTML = html;
        })
        .catch(err => {
            console.error("Lỗi tải bảng tồn kho thấp:", err);
            tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center py-3 text-danger">Lỗi kết nối dữ liệu kho.</td>
                </tr>`;
        });
}

function initAdvancedAnalytics() {
    fetch('/admin/api/stats/advanced-analytics')
        .then(res => res.json())
        .then(data => {
            // 1. Cập nhật KPI Tỷ lệ hủy đơn
            document.getElementById('cancellationRate').textContent = `${data.cancellation_rate}%`;
            document.getElementById('cancelledOrdersSub').textContent = `${data.cancelled_orders} / ${data.total_orders} đơn`;

            // 2. Phân khúc Khách hàng
            document.getElementById('newCustomersCount').textContent = data.customer_segments.new_customers;
            document.getElementById('returningCustomersCount').textContent = data.customer_segments.returning_customers;

            // 3. Render Top Khách hàng
            const topCustBody = document.getElementById('topCustomersBody');
            if (topCustBody) {
                let html = '';
                data.top_customers.forEach(c => {
                    html += `
                        <tr>
                            <td class="ps-3 py-2">
                                <strong class="text-dark">${c.username}</strong><br>
                                <small class="text-muted">${c.email}</small>
                            </td>
                            <td class="text-center py-2"><span class="badge bg-info text-dark">${c.total_orders} đơn</span></td>
                            <td class="text-end pe-3 py-2 fw-bold text-success">${c.total_spent.toLocaleString('vi-VN')} đ</td>
                        </tr>`;
                });
                topCustBody.innerHTML = html || '<tr><td colspan="3" class="text-center py-2">Chưa có dữ liệu</td></tr>';
            }

            // 4. Render Sản phẩm tồn lâu
            const deadStockBody = document.getElementById('deadStockBody');
            document.getElementById('deadStockCount').textContent = `${data.dead_stock.length} SP`;
            if (deadStockBody) {
                let html = '';
                data.dead_stock.forEach(p => {
                    html += `
                        <tr>
                            <td class="ps-3 py-2 text-truncate" style="max-width: 180px;" title="${p.name}">${p.name}</td>
                            <td class="py-2">${p.price.toLocaleString('vi-VN')} đ</td>
                            <td class="text-center py-2"><span class="badge bg-secondary">Còn ${p.stock_quantity}</span></td>
                        </tr>`;
                });
                deadStockBody.innerHTML = html || '<tr><td colspan="3" class="text-center py-2 text-success">Không có sản phẩm tồn lâu!</td></tr>';
            }
        })
        .catch(err => console.error("Lỗi tải phân tích nâng cao:", err));
}

function initPeakHoursChart() {
    const ctx = document.getElementById('peakHoursChart');
    if (!ctx) return;

    fetch('/admin/api/stats/peak-hours')
        .then(res => res.json())
        .then(data => {
            if (peakHoursChartInstance) peakHoursChartInstance.destroy();

            peakHoursChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Số lượng đơn hàng',
                        data: data.counts,
                        borderColor: '#0d6efd',
                        backgroundColor: 'rgba(13, 110, 253, 0.1)',
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    responsive: true,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, ticks: { precision: 0 } }
                    }
                }
            });
        })
        .catch(err => console.error("Lỗi tải biểu đồ khung giờ cao điểm:", err));
}