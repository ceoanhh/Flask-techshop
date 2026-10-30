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
    // 6. TỰ ĐỘNG CẬP NHẬT SỐ LƯỢNG & GIÁ TRONG GIỎ HÀNG (KHÔNG CẦN BẤM NÚT LOAD LẠI)
    // ==========================================
    function updateCartQuantityAjax(productId, newQty, targetUrl) {
        const row = document.getElementById(`cart-row-${productId}`);
        const input = row ? row.querySelector('.cart-qty-input') : null;
        const subtotalEl = document.getElementById(`item-subtotal-${productId}`);

        if (subtotalEl) {
            subtotalEl.style.opacity = '0.5';
        }

        const formData = new FormData();
        formData.append('quantity', newQty);

        fetch(targetUrl, {
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
                // Cập nhật giá trị ô input
                if (input && data.item_quantity !== undefined) {
                    input.value = data.item_quantity;
                }

                // Cập nhật thành tiền của món hàng đó tức thì
                if (subtotalEl && data.item_total !== undefined) {
                    subtotalEl.textContent = formatVND(data.item_total);
                }

                // Cập nhật badge giỏ hàng trên Navbar
                updateCartBadge(data.cart_count);

                // Cập nhật tổng số lượng toàn giỏ hàng trên badge đầu trang
                const badgeQtyEl = document.querySelector('.cart-total-quantity-badge');
                if (badgeQtyEl) badgeQtyEl.textContent = data.total_quantity;

                // Nếu số lượng về 0 (bị xóa)
                if (data.item_quantity === 0) {
                    if (row) row.remove();
                }

                // Tính toán lại tổng tiền và số lượng theo các sản phẩm đang được tích chọn
                recalculateSelectedTotals();

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
            showToast('Không thể kết nối đến máy chủ!', 'danger');
        })
        .finally(function () {
            if (subtotalEl) {
                subtotalEl.style.opacity = '1';
            }
        });
    }

    // Sự kiện bấm nút Trừ [-]
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-cart-minus');
        if (!btn) return;

        e.preventDefault();
        const productId = btn.dataset.productId;
        const row = document.getElementById(`cart-row-${productId}`);
        const input = row ? row.querySelector('.cart-qty-input') : null;
        if (!input) return;

        let currentQty = parseInt(input.value, 10) || 1;
        if (currentQty <= 1) {
            // Mở modal xóa nếu giảm về 0
            const deleteBtn = row.querySelector('.btn-delete-item');
            if (deleteBtn) deleteBtn.click();
            return;
        }

        const newQty = currentQty - 1;
        input.value = newQty;
        updateCartQuantityAjax(productId, newQty, btn.dataset.url);
    });

    // Sự kiện bấm nút Cộng [+]
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-cart-plus');
        if (!btn) return;

        e.preventDefault();
        const productId = btn.dataset.productId;
        const row = document.getElementById(`cart-row-${productId}`);
        const input = row ? row.querySelector('.cart-qty-input') : null;
        if (!input) return;

        let currentQty = parseInt(input.value, 10) || 1;
        let maxStock = parseInt(input.max, 10) || 9999;

        if (currentQty >= maxStock) {
            showToast(`Kho chỉ còn tối đa ${maxStock} sản phẩm!`, 'warning');
            return;
        }

        const newQty = currentQty + 1;
        input.value = newQty;
        updateCartQuantityAjax(productId, newQty, btn.dataset.url);
    });

    // Sự kiện thay đổi trực tiếp ô số lượng (gõ số hoặc phím mũi tên)
    let qtyDebounceTimer = null;
    document.addEventListener('input', function (e) {
        const input = e.target.closest('.cart-qty-input');
        if (!input) return;

        clearTimeout(qtyDebounceTimer);
        qtyDebounceTimer = setTimeout(function () {
            const productId = input.dataset.productId;
            let val = parseInt(input.value, 10);
            let maxStock = parseInt(input.max, 10) || 9999;

            if (isNaN(val) || val < 1) val = 1;
            if (val > maxStock) {
                val = maxStock;
                showToast(`Số lượng vượt quá tồn kho (${maxStock})!`, 'warning');
            }
            input.value = val;
            updateCartQuantityAjax(productId, val, input.dataset.url);
        }, 350);
    });

    // ==========================================
    // 6.5. TÍNH TOÁN LẠI TỔNG TIỀN VÀ SỐ LƯỢNG KHI CHỌN SẢN PHẨM (SELECTIVE CHECKOUT)
    // ==========================================
    let saveSelectionTimer = null;
    function syncSelectionWithServer(selectedIds) {
        clearTimeout(saveSelectionTimer);
        saveSelectionTimer = setTimeout(function () {
            fetch('/cart/save-selection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({ selected: selectedIds })
            }).catch(function (err) {
                console.warn('Lỗi khi đồng bộ trạng thái chọn giỏ hàng lên server:', err);
            });
        }, 150);
    }

    function recalculateSelectedTotals() {
        const itemCheckboxes = document.querySelectorAll('.cart-item-checkbox');
        if (!itemCheckboxes.length) return;

        let totalSelectedQty = 0;
        let totalSelectedPrice = 0.0;
        let selectedCount = 0;
        const selectedIds = [];

        itemCheckboxes.forEach(function (cb) {
            if (cb.checked) {
                selectedCount++;
                const pid = cb.dataset.productId || cb.value;
                selectedIds.push(pid);

                const row = document.getElementById(`cart-row-${pid}`);
                if (row) {
                    const qtyInput = row.querySelector('.cart-qty-input');
                    const qty = qtyInput ? (parseInt(qtyInput.value, 10) || 1) : 1;
                    const price = parseFloat(cb.dataset.price) || 0;

                    totalSelectedQty += qty;
                    totalSelectedPrice += (price * qty);
                }
            }
        });

        // Lưu trạng thái đã chọn vào localStorage và đồng bộ lên session server
        try {
            localStorage.setItem('techshop_selected_cart', JSON.stringify(selectedIds));
        } catch (e) {}
        syncSelectionWithServer(selectedIds);

        // Cập nhật tổng tiền thanh toán
        const totalEl = document.getElementById('cart-total-price');
        if (totalEl) {
            totalEl.textContent = formatVND(totalSelectedPrice);
        }

        // Cập nhật số lượng ở tóm tắt đơn hàng
        const summaryQtyEl = document.getElementById('cart-summary-quantity');
        if (summaryQtyEl) {
            summaryQtyEl.textContent = totalSelectedQty;
        }

        // Cập nhật số lượng ở footer bảng giỏ hàng
        const selectedCountEl = document.getElementById('selected-items-count');
        if (selectedCountEl) {
            selectedCountEl.textContent = totalSelectedQty;
        }

        // Cập nhật số lượng trên nút Tiến hành Đặt hàng
        const btnCheckoutCount = document.getElementById('btn-checkout-count');
        if (btnCheckoutCount) {
            btnCheckoutCount.textContent = totalSelectedQty;
        }

        // Cập nhật trạng thái checkbox "Chọn tất cả"
        const selectAll = document.getElementById('select-all-cart');
        if (selectAll) {
            if (selectedCount === itemCheckboxes.length && itemCheckboxes.length > 0) {
                selectAll.checked = true;
                selectAll.indeterminate = false;
            } else if (selectedCount === 0) {
                selectAll.checked = false;
                selectAll.indeterminate = false;
            } else {
                selectAll.checked = false;
                selectAll.indeterminate = true;
            }
        }

        // Cập nhật link nút Checkout và trạng thái disable
        const btnCheckout = document.getElementById('btn-proceed-checkout');
        if (btnCheckout) {
            if (selectedIds.length > 0) {
                btnCheckout.href = `/cart/checkout?selected=${selectedIds.join(',')}`;
                btnCheckout.classList.remove('disabled', 'opacity-50');
            } else {
                btnCheckout.href = 'javascript:void(0)';
                btnCheckout.classList.add('disabled', 'opacity-50');
            }
        }
    }

    // Sự kiện tích / bỏ tích "Chọn tất cả"
    document.addEventListener('change', function (e) {
        if (e.target && e.target.id === 'select-all-cart') {
            const isChecked = e.target.checked;
            document.querySelectorAll('.cart-item-checkbox').forEach(function (cb) {
                cb.checked = isChecked;
            });
            recalculateSelectedTotals();
        }
    });

    // Sự kiện tích / bỏ tích từng sản phẩm
    document.addEventListener('change', function (e) {
        if (e.target && e.target.classList.contains('cart-item-checkbox')) {
            recalculateSelectedTotals();
        }
    });

    // Chặn đặt hàng nếu chưa chọn sản phẩm nào
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('#btn-proceed-checkout');
        if (!btn) return;

        const selectedCheckboxes = document.querySelectorAll('.cart-item-checkbox:checked');
        if (selectedCheckboxes.length === 0) {
            e.preventDefault();
            showToast('Vui lòng tích chọn ít nhất 1 sản phẩm để tiến hành đặt hàng!', 'warning');
        }
    });

    // Khởi tạo tính toán ban đầu khi tải trang giỏ hàng
    recalculateSelectedTotals();

    // ==========================================
    // 7. XÁC NHẬN XÓA BẰNG MODAL (KHÔNG DÙNG POPUP BROWSER CŨ)
    // ==========================================
    let pendingDelete = {
        url: '',
        productId: null,
        isClear: false
    };

    function getDeleteModalInstance() {
        const modalEl = document.getElementById('deleteConfirmModal');
        if (!modalEl) return null;
        return bootstrap.Modal.getOrCreateInstance(modalEl);
    }

    // Mở modal khi bấm nút xóa 1 sản phẩm
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-delete-item');
        if (!btn) return;

        e.preventDefault();
        pendingDelete = {
            url: btn.dataset.url,
            productId: btn.dataset.productId,
            isClear: false
        };

        const titleEl = document.getElementById('deleteModalTitle');
        const descEl = document.getElementById('deleteModalDescription');
        const prodName = btn.dataset.productName || 'sản phẩm này';

        if (titleEl) titleEl.textContent = `Xóa "${prodName}"?`;
        if (descEl) descEl.textContent = 'Sản phẩm này sẽ được gỡ bỏ khỏi giỏ hàng của bạn.';

        const modal = getDeleteModalInstance();
        if (modal) modal.show();
    });

    // Mở modal khi bấm nút xóa toàn bộ giỏ
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn-clear-cart');
        if (!btn) return;

        e.preventDefault();
        pendingDelete = {
            url: btn.dataset.url,
            productId: null,
            isClear: true
        };

        const titleEl = document.getElementById('deleteModalTitle');
        const descEl = document.getElementById('deleteModalDescription');

        if (titleEl) titleEl.textContent = 'Làm trống toàn bộ giỏ hàng?';
        if (descEl) descEl.textContent = 'Tất cả sản phẩm hiện có trong giỏ hàng sẽ bị xóa hoàn toàn.';

        const modal = getDeleteModalInstance();
        if (modal) modal.show();
    });

    // Xử lý khi người dùng bấm nút "Xác nhận xóa" bên trong Modal
    const btnConfirmAction = document.getElementById('btnConfirmAction');
    if (btnConfirmAction) {
        btnConfirmAction.addEventListener('click', function () {
            if (!pendingDelete.url) return;

            // Đóng modal
            const modal = getDeleteModalInstance();
            if (modal) modal.hide();

            const isClear = pendingDelete.isClear;
            const productId = pendingDelete.productId;
            const targetUrl = pendingDelete.url;

            fetch(targetUrl, {
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

                    if (isClear) {
                        try {
                            localStorage.removeItem('techshop_selected_cart');
                        } catch (e) {}
                        const cartContent = document.getElementById('cart-content');
                        const cartEmpty = document.getElementById('cart-empty');
                        const cartBadge = document.querySelector('.cart-total-badge');
                        if (cartContent) cartContent.classList.add('d-none');
                        if (cartEmpty) cartEmpty.classList.remove('d-none');
                        if (cartBadge) cartBadge.classList.add('d-none');
                    } else {
                        // Xóa dòng tr của sản phẩm
                        const row = document.getElementById(`cart-row-${productId}`);
                        if (row) {
                            row.style.transition = 'opacity 0.25s ease';
                            row.style.opacity = '0';
                            setTimeout(function () {
                                row.remove();
                                recalculateSelectedTotals();
                            }, 250);
                        }

                        // Cập nhật tổng số lượng toàn giỏ trên badge đầu trang
                        const badgeQtyEl = document.querySelector('.cart-total-quantity-badge');
                        if (badgeQtyEl) badgeQtyEl.textContent = data.total_quantity;

                        // Tính lại tổng tiền và số lượng theo các sản phẩm còn lại được chọn
                        recalculateSelectedTotals();

                        // Nếu giỏ hàng đã rỗng
                        if (data.cart_count === 0) {
                            const cartContent = document.getElementById('cart-content');
                            const cartEmpty = document.getElementById('cart-empty');
                            const cartBadge = document.querySelector('.cart-total-badge');
                            if (cartContent) cartContent.classList.add('d-none');
                            if (cartEmpty) cartEmpty.classList.remove('d-none');
                            if (cartBadge) cartBadge.classList.add('d-none');
                        }
                    }
                } else {
                    showToast(data.message || 'Thao tác không thành công!', 'warning');
                }
            })
            .catch(function (err) {
                console.error('Lỗi khi xóa sản phẩm khỏi giỏ:', err);
                showToast('Lỗi mạng khi xóa sản phẩm!', 'danger');
            });
        });
    }

    // ==========================================
    // 8. AJAX LỌC DANH MỤC TRANG CHỦ KHÔNG LOAD LẠI TRANG
    // ==========================================
    function loadProductsAjax(url, pushState = true) {
        const wrapper = document.getElementById('product-ajax-wrapper');
        if (!wrapper) {
            window.location.href = url;
            return;
        }

        wrapper.style.opacity = '0.4';
        wrapper.style.pointerEvents = 'none';

        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(res => res.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const newWrapper = doc.getElementById('product-ajax-wrapper');

            if (newWrapper) {
                wrapper.innerHTML = newWrapper.innerHTML;
                if (pushState) {
                    history.pushState({ url: url }, '', url);
                }
            } else {
                window.location.href = url;
            }
        })
        .catch(err => {
            console.error('Lỗi load danh mục:', err);
            window.location.href = url;
        })
        .finally(() => {
            wrapper.style.opacity = '1';
            wrapper.style.pointerEvents = 'auto';
        });
    }

    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.category-filter-btn');
        if (!btn) return;

        e.preventDefault();
        loadProductsAjax(btn.href);
    });

    window.addEventListener('popstate', function () {
        if (document.getElementById('product-ajax-wrapper')) {
            loadProductsAjax(window.location.href, false);
        }
    });
});
