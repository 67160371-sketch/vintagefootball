// Vintage Football Shirts Cart Management (Client Storage)
const CART_STORAGE_KEY = 'vintage_football_cart';

const Cart = {
    getItems: function() {
        const stored = localStorage.getItem(CART_STORAGE_KEY);
        try {
            return stored ? JSON.parse(stored) : [];
        } catch (e) {
            console.error('Error parsing cart from storage:', e);
            return [];
        }
    },

    saveItems: function(items) {
        localStorage.setItem(CART_STORAGE_KEY, JSON.stringify(items));
        this.updateBadge();
    },

    addItem: function(product) {
        const items = this.getItems();
        const existing = items.find(item => item.id === product.id);

        if (existing) {
            if (existing.quantity + 1 > product.stock_quantity) {
                this.showToast(`เสื้อตัวนี้มีสต็อกคงเหลือ ${product.stock_quantity} ตัวเท่านั้น`, 'warning');
                return false;
            }
            existing.quantity += 1;
        } else {
            if (product.stock_quantity < 1) {
                this.showToast('สินค้าชิ้นนี้หมดแล้ว (Sold Out)', 'danger');
                return false;
            }
            items.push({
                id: product.id,
                team_name: product.team_name,
                season: product.season,
                size: product.size,
                condition: product.condition,
                price: parseFloat(product.price),
                stock_quantity: parseInt(product.stock_quantity),
                image_url: product.image_url,
                quantity: 1
            });
        }

        this.saveItems(items);
        this.showToast(`เพิ่ม '${product.team_name} (${product.season})' ลงในตะกร้าแล้ว! ⚽`, 'success');
        return true;
    },

    removeItem: function(productId) {
        let items = this.getItems();
        items = items.filter(item => item.id !== productId);
        this.saveItems(items);
        this.renderCartPage();
        this.showToast('ลบรายการสินค้าออกจากตะกร้าแล้ว', 'info');
    },

    updateQuantity: function(productId, delta) {
        const items = this.getItems();
        const item = items.find(i => i.id === productId);
        if (!item) return;

        const newQty = item.quantity + delta;
        if (newQty <= 0) {
            this.removeItem(productId);
            return;
        }

        if (newQty > item.stock_quantity) {
            this.showToast(`ไม่สามารถเพิ่มได้ สต็อกคงเหลือเพียง ${item.stock_quantity} ตัว`, 'warning');
            return;
        }

        item.quantity = newQty;
        this.saveItems(items);
        this.renderCartPage();
    },

    clear: function() {
        localStorage.removeItem(CART_STORAGE_KEY);
        this.updateBadge();
    },

    getTotalQuantity: function() {
        const items = this.getItems();
        return items.reduce((sum, item) => sum + item.quantity, 0);
    },

    getTotalAmount: function() {
        const items = this.getItems();
        return items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    },

    updateBadge: function() {
        const badge = document.getElementById('cart-badge');
        const count = this.getTotalQuantity();
        if (badge) {
            badge.innerText = count;
            badge.style.display = count > 0 ? 'inline-flex' : 'none';
        }
    },

    renderCartPage: function() {
        const container = document.getElementById('cart-items-container');
        const emptyState = document.getElementById('cart-empty-state');
        const summaryBox = document.getElementById('cart-summary-box');
        const checkoutBtn = document.getElementById('checkout-btn');

        if (!container) return; // Not on cart page

        const items = this.getItems();

        if (items.length === 0) {
            container.innerHTML = '';
            if (emptyState) emptyState.classList.remove('hidden');
            if (summaryBox) summaryBox.classList.add('hidden');
            if (checkoutBtn) checkoutBtn.disabled = true;
            return;
        }

        if (emptyState) emptyState.classList.add('hidden');
        if (summaryBox) summaryBox.classList.remove('hidden');
        if (checkoutBtn) checkoutBtn.disabled = false;

        let html = '';
        let total = 0;

        items.forEach(item => {
            const subtotal = item.price * item.quantity;
            total += subtotal;
            html += `
            <div class="flex flex-col sm:flex-row items-center justify-between p-4 bg-emerald-950/40 border border-emerald-800/40 rounded-xl gap-4 hover:border-emerald-600/50 transition">
                <div class="flex items-center gap-4 w-full sm:w-auto">
                    <img src="${item.image_url}" alt="${item.team_name}" class="w-20 h-20 object-cover rounded-lg border border-emerald-700/50 shadow" onerror="this.src='https://images.unsplash.com/photo-1577223625816-7546f13df25d?w=800'">
                    <div>
                        <div class="flex items-center gap-2">
                            <h3 class="font-bold text-white text-base">${item.team_name}</h3>
                            <span class="px-2 py-0.5 text-xs font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40 rounded">ไซส์ ${item.size}</span>
                        </div>
                        <p class="text-xs text-emerald-300/80 mt-0.5">${item.season}</p>
                        <p class="text-xs text-slate-400 mt-1"><i class="fa-solid fa-certificate text-emerald-400 mr-1"></i>${item.condition}</p>
                        <p class="text-emerald-400 font-bold mt-1 text-sm font-sports">฿${item.price.toLocaleString()} / ตัว</p>
                    </div>
                </div>

                <div class="flex items-center justify-between w-full sm:w-auto gap-6">
                    <!-- Quantity Stepper -->
                    <div class="flex items-center bg-slate-900 border border-emerald-800 rounded-lg p-1">
                        <button onclick="Cart.updateQuantity(${item.id}, -1)" class="w-8 h-8 rounded bg-slate-800 hover:bg-emerald-700 text-white font-bold flex items-center justify-center transition">
                            <i class="fa-solid fa-minus text-xs"></i>
                        </button>
                        <span class="w-10 text-center font-bold text-white font-sports">${item.quantity}</span>
                        <button onclick="Cart.updateQuantity(${item.id}, 1)" class="w-8 h-8 rounded bg-slate-800 hover:bg-emerald-700 text-white font-bold flex items-center justify-center transition" ${item.quantity >= item.stock_quantity ? 'disabled opacity-50' : ''}>
                            <i class="fa-solid fa-plus text-xs"></i>
                        </button>
                    </div>

                    <!-- Subtotal -->
                    <div class="text-right min-w-[90px]">
                        <p class="text-xs text-slate-400">รวม</p>
                        <p class="font-bold text-white text-base font-sports">฿${subtotal.toLocaleString()}</p>
                    </div>

                    <!-- Remove -->
                    <button onclick="Cart.removeItem(${item.id})" class="text-red-400 hover:text-red-300 p-2 hover:bg-red-500/10 rounded-lg transition" title="ลบออกจากตะกร้า">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            </div>
            `;
        });

        container.innerHTML = html;

        // Update Summary
        const summaryTotal = document.getElementById('summary-total');
        const summaryItemsCount = document.getElementById('summary-items-count');
        if (summaryTotal) summaryTotal.innerText = `฿${total.toLocaleString()}`;
        if (summaryItemsCount) summaryItemsCount.innerText = `${this.getTotalQuantity()} ตัว`;
    },

    submitCheckout: async function(event) {
        event.preventDefault();
        const items = this.getItems();
        if (items.length === 0) {
            this.showToast('ไม่มีสินค้าในตะกร้า กรุณาเลือกเสื้อฟุตบอลก่อน', 'warning');
            return;
        }

        const form = document.getElementById('checkout-form');
        const shippingAddress = document.getElementById('shipping_address').value.trim();
        const recipientName = document.getElementById('recipient_name') ? document.getElementById('recipient_name').value.trim() : '';
        const recipientEmail = document.getElementById('recipient_email') ? document.getElementById('recipient_email').value.trim() : '';

        if (!shippingAddress) {
            this.showToast('กรุณาระบุที่อยู่จัดส่งให้ชัดเจน', 'danger');
            document.getElementById('shipping_address').focus();
            return;
        }

        const btn = document.getElementById('checkout-btn');
        btn.disabled = true;
        btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-2"></i> กำลังบันทึกคำสั่งซื้อและตัดสต็อก...`;

        try {
            const response = await fetch('/api/checkout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    items: items.map(i => ({ id: i.id, quantity: i.quantity })),
                    shipping_address: shippingAddress,
                    name: recipientName,
                    email: recipientEmail
                })
            });

            const result = await response.json();

            if (result.success) {
                // Clear cart immediately
                this.clear();
                this.showToast('สั่งซื้อสำเร็จ! กำลังพาไปหน้าสรุปคำสั่งซื้อ...', 'success');
                setTimeout(() => {
                    window.location.href = `/order-success/${result.order_id}`;
                }, 800);
            } else {
                btn.disabled = false;
                btn.innerHTML = `<i class="fa-solid fa-check mr-2"></i> ยืนยันการสั่งซื้อ (Confirm Order)`;
                this.showToast(result.message || 'เกิดข้อผิดพลาดในการสั่งซื้อ', 'danger');
            }
        } catch (error) {
            btn.disabled = false;
            btn.innerHTML = `<i class="fa-solid fa-check mr-2"></i> ยืนยันการสั่งซื้อ (Confirm Order)`;
            this.showToast('เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์', 'danger');
            console.error(error);
        }
    },

    showToast: function(message, type = 'success') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'fixed bottom-5 right-5 z-50 flex flex-col gap-2 max-w-sm pointer-events-none';
            document.body.appendChild(container);
        }

        const toast = document.createElement('div');
        const colorClasses = {
            success: 'bg-emerald-900 border-emerald-500 text-white',
            warning: 'bg-amber-900 border-amber-500 text-amber-100',
            danger: 'bg-red-950 border-red-500 text-white',
            info: 'bg-sky-950 border-sky-500 text-sky-100'
        }[type] || 'bg-slate-900 border-slate-600 text-white';

        const iconClass = {
            success: 'fa-circle-check text-emerald-400',
            warning: 'fa-triangle-exclamation text-amber-400',
            danger: 'fa-circle-exclamation text-red-400',
            info: 'fa-circle-info text-sky-400'
        }[type] || 'fa-info';

        toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl border shadow-2xl ${colorClasses} pointer-events-auto transform transition-all duration-300 translate-y-2 opacity-0`;
        toast.innerHTML = `
            <i class="fa-solid ${iconClass} text-lg"></i>
            <span class="text-sm font-medium flex-1">${message}</span>
        `;

        container.appendChild(toast);

        // Animate in
        setTimeout(() => {
            toast.classList.remove('translate-y-2', 'opacity-0');
        }, 10);

        // Animate out & remove
        setTimeout(() => {
            toast.classList.add('opacity-0', 'translate-x-full');
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }
};

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', () => {
    Cart.updateBadge();
    Cart.renderCartPage();
});
