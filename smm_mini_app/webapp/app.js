const tg = window.Telegram.WebApp;
tg.expand();
tg.ready();

const API_BASE = "https://sizning-api-serveringiz.com"; // O'ZGARTIRING!

let STATE = { user: null, categories: [], currentCategory: null, services: [], selectedService: null, method: 'Click', cards: {} };

async function init() {
    tg.setHeaderColor('#ffffff');
    tg.setBackgroundColor('#ffffff');
    try {
        const res = await apiCall('/api/user', { initData: tg.initData });
        STATE.user = res.user;
        STATE.categories = res.categories;
        STATE.cards = res.cards;
        document.getElementById('userName').textContent = STATE.user.first_name || 'User';
        document.getElementById('userId').textContent = STATE.user.user_id;
        document.getElementById('userAvatar').textContent = (STATE.user.first_name || 'U')[0].toUpperCase();
        renderUserData(); renderCategories(); renderMethods(); renderRecentOrders(res.recent_orders || []);
        showScreen('home');
    } catch (e) { console.error(e); toast('Xatolik: ' + e.message, 'error'); }
}

async function apiCall(path, body = {}) {
    const res = await fetch(API_BASE + path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...body, initData: tg.initData }) });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || 'Server error');
    return data;
}

function showScreen(name) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    const el = document.getElementById(name);
    if (el) el.classList.add('active');
    window.scrollTo(0, 0);
}

function renderUserData() {
    document.getElementById('balance').textContent = fmt(STATE.user.balance);
    document.getElementById('totalOrders').textContent = STATE.user.total_orders || 0;
    document.getElementById('totalSpent').textContent = fmt(STATE.user.total_spent);
    document.getElementById('referrals').textContent = STATE.user.referrals || 0;
    document.getElementById('refBalance').textContent = fmt(STATE.user.referral_balance);
    document.getElementById('refLink').textContent = STATE.user.ref_link;
    document.getElementById('orderBalance').textContent = fmt(STATE.user.balance);
}

function renderCategories() {
    const grid = document.getElementById('categoriesGrid');
    const emojis = { 'Instagram': '📱', 'Telegram': '✈️', 'YouTube': '▶️', 'TikTok': '🎵', 'Facebook': '👤', 'Twitter': '🐦' };
    grid.innerHTML = STATE.categories.map(cat => `<div class="category-card" onclick="openCategory('${cat}')"><div class="cat-emoji">${emojis[cat] || '📦'}</div><div class="cat-name">${cat}</div></div>`).join('');
}

async function openCategory(cat) {
    STATE.currentCategory = cat;
    document.getElementById('categoryTitle').textContent = cat + ' xizmatlari';
    showScreen('services');
    const res = await apiCall('/api/services', { category: cat });
    STATE.services = res.services;
    const list = document.getElementById('servicesList');
    if (!res.services.length) { list.innerHTML = '<div class="empty">Xizmatlar topilmadi</div>'; return; }
    list.innerHTML = res.services.map(s => `<div class="service-card" onclick="openService(${s.id})"><div class="service-name">${s.name}</div><div class="service-price">${fmt(s.price_per_1000)} so'm / 1000</div><div class="service-desc">${s.description || ''} · Min: ${fmt(s.min_order)} · Max: ${fmt(s.max_order)}</div></div>`).join('');
}

function openService(id) {
    STATE.selectedService = STATE.services.find(s => s.id === id);
    if (!STATE.selectedService) return;
    const s = STATE.selectedService;
    document.getElementById('serviceInfo').innerHTML = `<div class="service-name">${s.name}</div><div class="service-price">${fmt(s.price_per_1000)} so'm / 1000</div>`;
    document.getElementById('qtyHint').textContent = `Min: ${fmt(s.min_order)} | Max: ${fmt(s.max_order)}`;
    document.getElementById('orderLink').value = '';
    document.getElementById('orderQty').value = '';
    document.getElementById('orderPrice').textContent = '0';
    document.getElementById('orderLink').oninput = updatePrice;
    document.getElementById('orderQty').oninput = updatePrice;
    showScreen('orderForm');
}

function updatePrice() {
    const s = STATE.selectedService;
    const qty = parseInt(document.getElementById('orderQty').value) || 0;
    document.getElementById('orderPrice').textContent = fmt((qty / 1000) * s.price_per_1000);
}

async function submitOrder() {
    const s = STATE.selectedService;
    const link = document.getElementById('orderLink').value.trim();
    const qty = parseInt(document.getElementById('orderQty').value) || 0;
    if (!link || !link.startsWith('http')) return toast("To'g'ri link kiriting", 'error');
    if (qty < s.min_order || qty > s.max_order) return toast(`Miqdor ${fmt(s.min_order)} - ${fmt(s.max_order)} orasida bo'lishi kerak`, 'error');
    const total = (qty / 1000) * s.price_per_1000;
    if (total > STATE.user.balance) return toast('Balans yetarli emas!', 'error');
    try {
        const res = await apiCall('/api/order/create', { service_id: s.id, link, quantity: qty });
        toast(`✅ Buyurtma qabul qilindi: ${res.order_number}`, 'success');
        STATE.user.balance -= total;
        renderUserData();
        setTimeout(() => { showScreen('home'); refreshData(); }, 1500);
    } catch (e) { toast(e.message, 'error'); }
}

function renderMethods() {
    const methods = [{ id: 'Click', emoji: '💙', name: 'Click' }, { id: 'Payme', emoji: '🟣', name: 'Payme' }, { id: 'Uzcard', emoji: '💚', name: 'Uzcard' }, { id: 'Humo', emoji: '💜', name: 'Humo' }];
    document.getElementById('methodsGrid').innerHTML = methods.map(m => `<div class="method-card ${m.id === STATE.method ? 'selected' : ''}" onclick="selectMethod('${m.id}')" data-method="${m.id}"><div class="method-emoji">${m.emoji}</div><div class="method-name">${m.name}</div></div>`).join('');
    updateCardInfo();
}

function selectMethod(m) {
    STATE.method = m;
    document.querySelectorAll('.method-card').forEach(el => el.classList.toggle('selected', el.dataset.method === m));
    updateCardInfo();
}

function updateCardInfo() {
    const card = STATE.cards[STATE.method];
    const info = document.getElementById('cardInfo');
    if (card) {
        info.innerHTML = `<div>Karta raqami:</div><div class="card-number">${card}</div><div style="font-size:12px;color:var(--hint);margin-top:8px">To'lovdan so'ng "To'lov qilish" tugmasini bosing</div>`;
        info.classList.add('show');
    } else { info.classList.remove('show'); }
}

function setAmount(a) { document.getElementById('topupAmount').value = a; }

async function submitPayment() {
    const amount = parseInt(document.getElementById('topupAmount').value) || 0;
    if (amount < 5000) return toast("Minimal to'lov: 5,000 so'm", 'error');
    try {
        const res = await apiCall('/api/payment/create', { amount, method: STATE.method });
        toast(`✅ To'lov qabul qilindi: ${res.payment_id}`, 'success');
        setTimeout(() => showScreen('home'), 1500);
    } catch (e) { toast(e.message, 'error'); }
}

async function loadOrders() {
    try {
        const res = await apiCall('/api/orders');
        renderOrders(res.orders);
    } catch (e) { toast(e.message, 'error'); }
}

function renderOrders(orders) {
    const el = document.getElementById('ordersList');
    if (!orders.length) return el.innerHTML = '<div class="empty">Buyurtmalar yo\'q</div>';
    el.innerHTML = orders.map(o => `<div class="order-card"><div class="order-header"><span class="order-id">${o.order_number}</span><span class="order-status status-${o.status}">${statusLabel(o.status)}</span></div><div class="order-service">${o.service_name}</div><div class="order-meta"><span>📊 ${fmt(o.quantity)} ta</span><span>💰 ${fmt(o.total_price)} so'm</span></div><div class="order-meta"><span>🔗 ${(o.link||'').substring(0,30)}...</span><span>📅 ${(o.created_at||'').substring(0,10)}</span></div></div>`).join('');
}

function renderRecentOrders(orders) {
    const el = document.getElementById('recentOrders');
    if (!orders.length) return el.innerHTML = '<div class="empty">Hali buyurtma bermagansiz</div>';
    el.innerHTML = orders.slice(0, 3).map(o => `<div class="order-card"><div class="order-header"><span class="order-id">${o.order_number}</span><span class="order-status status-${o.status}">${statusLabel(o.status)}</span></div><div class="order-service">${o.service_name}</div><div class="order-meta"><span>📊 ${fmt(o.quantity)} ta</span><span>💰 ${fmt(o.total_price)} so'm</span></div></div>`).join('');
}

function copyRefLink() { navigator.clipboard.writeText(STATE.user.ref_link); toast('✅ Nusxalandi!', 'success'); }
function shareRefLink() { tg.openTelegramLink(`https://t.me/share/url?url=${encodeURIComponent(STATE.user.ref_link)}&text=🎁 SMM Pro botga qo'shiling!`); }
function fmt(n) { return Math.round(n || 0).toLocaleString('uz-UZ').replace(/,/g, ' '); }
function statusLabel(s) { return { pending: '⏳ Kutilmoqda', processing: '🔄 Jarayonda', completed: '✅ Bajarildi', cancelled: '❌ Bekor' }[s] || s; }

function toast(msg, type = '') {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'toast show ' + type;
    setTimeout(() => t.classList.remove('show'), 3000);
}

async function refreshData() {
    const res = await apiCall('/api/user', { initData: tg.initData });
    STATE.user = res.user;
    renderUserData();
    renderRecentOrders(res.recent_orders || []);
}

window.onload = init;
