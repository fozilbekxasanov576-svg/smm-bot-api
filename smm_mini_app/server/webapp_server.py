from flask import Flask, request, jsonify
from flask_cors import CORS
import hashlib, hmac, json, sqlite3, uuid, os
from urllib.parse import parse_qsl
from functools import wraps

app = Flask(__name__)
CORS(app)

BOT_TOKEN = "9009367032:AAHdL3K6EG0Zna4rElYDct1T2E6VH41ZnNU"
ADMIN_CARDS = {
    "Click": "8600 1234 5678 9012", "Payme": "8600 9876 5432 1098",
    "Uzcard": "8600 1111 2222 3333", "Humo": "9860 4444 5555 6666"
}
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'smm_bot.db')

def get_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def verify_init_data(init_data: str):
    if not init_data: return None
    try:
        parsed = dict(parse_qsl(init_data))
        hash_val = parsed.pop('hash', None)
        if not hash_val: return None
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed.items()))
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        computed = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        if computed != hash_val: return None
        return json.loads(parsed.get('user', '{}'))
    except: return None

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        body = request.get_json(silent=True) or {}
        user = verify_init_data(body.get('initData'))
        if not user: return jsonify({"error": "Unauthorized"}), 401
        request.tg_user = user
        return f(*args, **kwargs)
    return wrapper

@app.route('/api/user', methods=['POST'])
@require_auth
def api_user():
    uid = request.tg_user.get('id')
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT * FROM users WHERE user_id=?', (uid,))
    u = c.fetchone()
    if not u: return jsonify({"error": "User not found. Botga /start yuboring."}), 404
    c.execute('SELECT COUNT(*) FROM orders WHERE user_id=?', (uid,)); total_orders = c.fetchone()[0]
    c.execute('SELECT COUNT(*) FROM users WHERE referrer_id=?', (uid,)); referrals = c.fetchone()[0]
    c.execute('SELECT DISTINCT category FROM services WHERE is_active=1'); categories = [r[0] for r in c.fetchall()]
    c.execute('''SELECT o.order_number, s.name, o.quantity, o.total_price, o.status, o.created_at, o.link
                 FROM orders o JOIN services s ON o.service_id=s.id
                 WHERE o.user_id=? ORDER BY o.created_at DESC LIMIT 5''', (uid,))
    recent = [{"order_number": r[0], "service_name": r[1], "quantity": r[2], "total_price": r[3], "status": r[4], "created_at": r[5], "link": r[6]} for r in c.fetchall()]
    conn.close()
    return jsonify({
        "user": {"user_id": u[0], "first_name": u[2], "username": u[1], "balance": u[3], "total_spent": u[4], "referral_balance": u[6], "referrals": referrals, "total_orders": total_orders, "ref_link": f"https://t.me/nakrutka_xizmatibot?start=ref{uid}"},
        "categories": categories, "recent_orders": recent, "cards": ADMIN_CARDS
    })

@app.route('/api/services', methods=['POST'])
@require_auth
def api_services():
    cat = request.get_json().get('category')
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT id, name, category, price_per_1000, min_order, max_order, description FROM services WHERE is_active=1 AND category=? ORDER BY price_per_1000', (cat,))
    services = [{"id": r[0], "name": r[1], "category": r[2], "price_per_1000": r[3], "min_order": r[4], "max_order": r[5], "description": r[6]} for r in c.fetchall()]
    conn.close()
    return jsonify({"services": services})

@app.route('/api/order/create', methods=['POST'])
@require_auth
def api_order_create():
    uid = request.tg_user['id']
    body = request.get_json()
    sid, link, qty = body.get('service_id'), (body.get('link') or '').strip(), int(body.get('quantity') or 0)
    if not link.startswith('http'): return jsonify({"error": "To'g'ri link kiriting"}), 400
    conn = get_db(); c = conn.cursor()
    c.execute('SELECT * FROM services WHERE id=? AND is_active=1', (sid,))
    s = c.fetchone()
    if not s: conn.close(); return jsonify({"error": "Xizmat topilmadi"}), 404
    if qty < s[4] or qty > s[5]: conn.close(); return jsonify({"error": f"Miqdor {s[4]}-{s[5]} orasida"}), 400
    total = (qty / 1000) * s[3]
    c.execute('SELECT balance FROM users WHERE user_id=?', (uid,))
    if c.fetchone()[0] < total: conn.close(); return jsonify({"error": "Balans yetarli emas"}), 400
    order_number = f"ORD{uuid.uuid4().hex[:8].upper()}"
    c.execute('INSERT INTO orders (order_number, user_id, service_id, link, quantity, total_price) VALUES (?, ?, ?, ?, ?, ?)', (order_number, uid, sid, link, qty, total))
    c.execute('UPDATE users SET balance = balance - ?, total_spent = total_spent + ? WHERE user_id=?', (total, total, uid))
    conn.commit(); conn.close()
    return jsonify({"order_number": order_number, "total": total})

@app.route('/api/orders', methods=['POST'])
@require_auth
def api_orders():
    uid = request.tg_user['id']
    conn = get_db(); c = conn.cursor()
    c.execute('''SELECT o.order_number, s.name, o.quantity, o.total_price, o.status, o.created_at, o.link
                 FROM orders o JOIN services s ON o.service_id=s.id
                 WHERE o.user_id=? ORDER BY o.created_at DESC LIMIT 50''', (uid,))
    orders = [{"order_number": r[0], "service_name": r[1], "quantity": r[2], "total_price": r[3], "status": r[4], "created_at": r[5], "link": r[6]} for r in c.fetchall()]
    conn.close()
    return jsonify({"orders": orders})

@app.route('/api/payment/create', methods=['POST'])
@require_auth
def api_payment_create():
    uid = request.tg_user['id']
    body = request.get_json()
    amount, method = float(body.get('amount') or 0), body.get('method', 'Click')
    if amount < 5000: return jsonify({"error": "Minimal to'lov: 5,000 so'm"}), 400
    conn = get_db(); c = conn.cursor()
    payment_id = f"PAY{uuid.uuid4().hex[:8].upper()}"
    c.execute('INSERT INTO payments (payment_id, user_id, amount, method) VALUES (?, ?, ?, ?)', (payment_id, uid, amount, method))
    conn.commit(); conn.close()
    return jsonify({"payment_id": payment_id})

@app.route('/', methods=['GET'])
def index(): return jsonify({"status": "ok", "message": "SMM Bot API ishlayapti"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
