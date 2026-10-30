// ==========================================
// TECHSTORE JAVASCRIPT & AJAX INTERACTIONS
// ==========================================

document.addEventListener('DOMContentLoaded', function () {
    console.log("TechShop JS đã sẵn sàng!");

    // 1. Tự động đóng thông báo flash sau 4 giây
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {
                // Đã bị đóng thủ công
            }
        }, 4000);
    });

    // 2. Hàm hiển thị Toast thông báo nhẹ không tải lại trang
    window.showToast = function (message, type = 'success') {
        const toastEl = document.getElementById('liveToast');
        if (!toastEl) return;

        const toastIcon = document.getElementById('toastIcon');
        const toastMessage = document.getElementById('toastMessage');

        // Reset class màu sắc
        toastEl.className = 'toast align-items-center text-white border-0 shadow-lg';
        let bgClass = 'bg-success';
        let iconClass = 'bi bi-check-circle-fill fs-5';

        if (type === 'danger' || type === 'error') {
            bgClass = 'bg-danger';
            iconClass = 'bi bi-exclamation-triangle-fill fs-5';
        } else if (type === 'warning') {
            bgClass = 'bg-warning text-dark';
            iconClass = 'bi bi-exclamation-circle-fill fs-5';
        } else if (type === 'info') {
            bgClass = 'bg-primary';
            iconClass = 'bi bi-info-circle-fill fs-5';
        }

        toastEl.classList.add(bgClass);
        if (toastIcon) toastIcon.className = iconClass;
        if (toastMessage) toastMessage.textContent = message;

        const toast = bootstrap.Toast.getOrCreateInstance(toastEl, { delay: 3200 });
        toast.show();
    };

    // 3. Hàm cập nhật số lượng badge giỏ hàng trên Navbar
    window.updateCartBadge = function (cartCount) {
        const badge = document.getElementById('cart-badge');
        if (!badge) return;

        const count = parseInt(cartCount, 10) || 0;
        badge.textContent = count;

        if (count > 0) {
            badge.classList.remove('d-none');
            // Hiệu ứng nhấp nháy thu hút sự chú ý
            badge.classList.remove('badge-bounce');
            void badge.offsetWidth; // Force reflow
            badge.classList.add('badge-bounce');
        } else {
            badge.classList.add('d-none');
        }
    };

    // 4. Định dạng tiền tệ VNĐ (ví dụ: 12,500,000 VNĐ)
    window.formatVND = function (amount) {
        return new Intl.NumberFormat('vi-VN').format(amount) + ' VNĐ';
    };

    // ==========================================
    // 5. AJAX THÊM SẢN PHẨM VÀO GIỎ HÀNG
    // ==========================================
    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!form || !form.matches('.ajax-cart-form, form[action*="/cart/add/"]')) {
            return;
        }

        e.preventDefault();
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnHTML = submitBtn ? submitBtn.innerHTML : '';

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Đang thêm...';
        }

        const formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
        .then(function (res) {
            return res.json().then(function (data) {
                return { ok: res.ok, data: data };
            });
        })
        .then(function (result) {
            const data = result.data;
            if (result.ok && data.success) {
                showToast(data.message, 'success');
                updateCartBadge(data.cart_count);
            } else {
                showToast(data.message || 'Không thể thêm sản phẩm vào giỏ!', 'danger');
            }
        })
        .catch(function (err) {
            console.error('Lỗi khi thêm giỏ hàng:', err);
            showToast('Đã xảy ra lỗi mạng. Vui lòng thử lại!', 'danger');
        })
        .finally(function () {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnHTML;
            }
        });
    });

    // ==========================================
    // 6. AJAX CẬP NHẬT SỐ LƯỢNG TRONG GIỎ HÀNG
    // ==========================================
    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!form || !form.matches('.cart-update-form')) {
            return;
        }

        e.preventDefault();
        const productId = form.dataset.productId;
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnHTML = submitBtn ? submitBtn.innerHTML : '';

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span>';
        }

        const formData = new FormData(form);

        fetch(form.action, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
        .then(function (res) {
            return res.json().then(function (data) {
                return { ok: res.ok, data: data };
            });
        })
        .then(function (result) {
            const data = result.data;
            if (result.ok && data.success) {
                showToast(data.message, 'success');
                updateCartBadge(data.cart_count);

                // Cập nhật thành tiền của món hàng
                const subtotalEl = document.getElementById(`item-subtotal-${productId}`);
                if (subtotalEl && data.item_total !== undefined) {
                    subtotalEl.textContent = formatVND(data.item_total);
                }

                // Cập nhật tổng tiền đơn hàng
                const totalEl = document.getElementById('cart-total-price');
                if (totalEl && data.total_price !== undefined) {
                    totalEl.textContent = formatVND(data.total_price);
                }

                // Cập nhật tổng số lượng
                const badgeQtyEl = document.querySelector('.cart-total-quantity-badge');
                if (badgeQtyEl) badgeQtyEl.textContent = data.total_quantity;

                const summaryQtyEl = document.getElementById('cart-summary-quantity');
                if (summaryQtyEl) summaryQtyEl.textContent = data.total_quantity;

                // Nếu số lượng thành 0 (bị xóa)
                if (data.item_quantity === 0) {
                    const row = document.getElementById(`cart-row-${productId}`);
                    if (row) row.remove();
                }

                // Nếu giỏ hàng đã rỗng
                if (data.cart_count === 0) {
                    const cartContent = document.getElementById('cart-content');
                    const cartEmpty = document.getElementById('cart-empty');
                    const cartBadge = document.querySelector('.cart-total-badge');
                    if (cartContent) cartContent.classList.add('d-none');
                    if (cartEmpty) cartEmpty.classList.remove('d-none');
                    if (cartBadge) cartBadge.classList.add('d-none');
                }
            } else {
                showToast(data.message || 'Không thể cập nhật số lượng!', 'warning');
            }
        })
        .catch(function (err) {
            console.error('Lỗi khi cập nhật giỏ hàng:', err);
            showToast('Không thể kết nối đến máy chủ. Vui lòng thử lại!', 'danger');
        })
        .finally(function () {
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnHTML;
            }
        });
    });

    // ==========================================
    // 7. AJAX XÓA 1 SẢN PHẨM KHỎI GIỎ HÀNG
    // ==========================================
    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!form || !form.matches('.cart-remove-form')) {
            return;
        }

        e.preventDefault();
        const productId = form.dataset.productId;
        const row = document.getElementById(`cart-row-${productId}`);

        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
        .then(function (res) {
            return res.json().then(function (data) {
                return { ok: res.ok, data: data };
            });
        })
        .then(function (result) {
            const data = result.data;
            if (result.ok && data.success) {
                showToast(data.message, 'info');
                updateCartBadge(data.cart_count);

                // Xóa dòng với hiệu ứng mờ dần
                if (row) {
                    row.style.transition = 'opacity 0.3s ease';
                    row.style.opacity = '0';
                    setTimeout(function () {
                        row.remove();
                    }, 300);
                }

                // Cập nhật tổng tiền đơn hàng
                const totalEl = document.getElementById('cart-total-price');
                if (totalEl && data.total_price !== undefined) {
                    totalEl.textContent = formatVND(data.total_price);
                }

                // Cập nhật tổng số lượng
                const badgeQtyEl = document.querySelector('.cart-total-quantity-badge');
                if (badgeQtyEl) badgeQtyEl.textContent = data.total_quantity;

                const summaryQtyEl = document.getElementById('cart-summary-quantity');
                if (summaryQtyEl) summaryQtyEl.textContent = data.total_quantity;

                // Nếu giỏ hàng đã rỗng
                if (data.cart_count === 0) {
                    const cartContent = document.getElementById('cart-content');
                    const cartEmpty = document.getElementById('cart-empty');
                    const cartBadge = document.querySelector('.cart-total-badge');
                    if (cartContent) cartContent.classList.add('d-none');
                    if (cartEmpty) cartEmpty.classList.remove('d-none');
                    if (cartBadge) cartBadge.classList.add('d-none');
                }
            } else {
                showToast(data.message || 'Không thể xóa sản phẩm khỏi giỏ!', 'warning');
            }
        })
        .catch(function (err) {
            console.error('Lỗi khi xóa sản phẩm khỏi giỏ hàng:', err);
            showToast('Lỗi mạng khi xóa sản phẩm!', 'danger');
        });
    });

    // ==========================================
    // 8. AJAX XÓA TOÀN BỘ GIỎ HÀNG (CLEAR CART)
    // ==========================================
    document.addEventListener('submit', function (e) {
        const form = e.target;
        if (!form || !form.matches('.cart-clear-form')) {
            return;
        }

        e.preventDefault();

        fetch(form.action, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
        .then(function (res) {
            return res.json().then(function (data) {
                return { ok: res.ok, data: data };
            });
        })
        .then(function (result) {
            const data = result.data;
            if (result.ok && data.success) {
                showToast(data.message, 'info');
                updateCartBadge(0);

                const cartContent = document.getElementById('cart-content');
                const cartEmpty = document.getElementById('cart-empty');
                const cartBadge = document.querySelector('.cart-total-badge');
                if (cartContent) cartContent.classList.add('d-none');
                if (cartEmpty) cartEmpty.classList.remove('d-none');
                if (cartBadge) cartBadge.classList.add('d-none');
            } else {
                showToast(data.message || 'Không thể xóa giỏ hàng!', 'warning');
            }
        })
        .catch(function (err) {
            console.error('Lỗi khi xóa toàn bộ giỏ hàng:', err);
            showToast('Lỗi mạng khi xóa giỏ hàng!', 'danger');
        });
    });
});
