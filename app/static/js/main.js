// JS tương tác chung cho TechShop (Do Dần phát triển thêm)
document.addEventListener('DOMContentLoaded', function () {
    console.log("TechShop JS đã sẵn sàng!");

    // Tự động đóng thông báo flash sau 4 giây
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 4000);
    });
});
