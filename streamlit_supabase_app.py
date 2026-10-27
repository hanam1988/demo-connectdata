import html
import streamlit as st
from datetime import datetime, date
from supabase import create_client, Client
from streamlit.errors import StreamlitSecretNotFoundError
from typing import Optional

# ==========================================
# CẤU HÌNH TRANG
# ==========================================
st.set_page_config(page_title="Quản Lý Đơn Hàng", page_icon="📦", layout="wide")

# ==========================================
# GIAO DIỆN (CSS)
# ==========================================
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;500;600;700&display=swap');

:root {
    --ink: #1c2530;
    --muted: #6b7684;
    --line: #e3e7ec;
    --bg: #f4f6f8;
    --card: #ffffff;
    --accent: #0f5c4d;
    --accent-dark: #0a443a;
    --gold: #b8893b;
}

html, body, [class*="css"], .stApp, button, input, textarea, select {
    font-family: 'Be Vietnam Pro', system-ui, sans-serif !important;
}
.stApp { background: var(--bg); color: var(--ink); }
#MainMenu, footer, header[data-testid="stHeader"] { visibility: hidden; height: 0; }
.block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 4rem; }

/* Tiêu đề trang */
.page-title { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.01em; margin: 0; color: var(--ink); }
.page-sub { color: var(--muted); font-size: 0.95rem; margin: 0.15rem 0 1.25rem 0; }

/* Thẻ số liệu */
.stat {
    background: var(--card); border: 1px solid var(--line); border-radius: 12px;
    padding: 1rem 1.25rem;
}
.stat .label { color: var(--muted); font-size: 0.85rem; }
.stat .value { font-size: 1.6rem; font-weight: 700; margin-top: 0.15rem; }
.stat.accent { border-left: 4px solid var(--gold); }

/* Hàng đơn hàng */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: var(--card); border-color: var(--line) !important; border-radius: 12px;
}
.cell-main { font-weight: 600; color: var(--ink); line-height: 1.3; }
.cell-sub { color: var(--muted); font-size: 0.85rem; line-height: 1.3; }
.cell-num { font-weight: 600; font-variant-numeric: tabular-nums; }
.col-head { color: var(--muted); font-size: 0.82rem; font-weight: 500; padding: 0 1rem; }

/* Nhãn trạng thái */
.pill {
    display: inline-block; padding: 0.2rem 0.7rem; border-radius: 999px;
    font-size: 0.8rem; font-weight: 600;
}
.pill.pending   { background: #fff4de; color: #8a5a00; }
.pill.completed { background: #dff3ea; color: #0b5a40; }
.pill.cancelled { background: #fde5e3; color: #9a2b22; }

/* Nút */
.stButton > button, .stFormSubmitButton > button {
    border-radius: 10px; font-weight: 600; border: 1px solid var(--line);
    transition: background .15s, border-color .15s;
}
.stButton > button:hover { border-color: var(--accent); color: var(--accent); }
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
    background: var(--accent); border-color: var(--accent); color: #fff;
}
.stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
    background: var(--accent-dark); border-color: var(--accent-dark); color: #fff;
}
.stButton > button:focus-visible, .stFormSubmitButton > button:focus-visible {
    outline: 2px solid var(--gold); outline-offset: 2px;
}

/* Form */
div[data-testid="stForm"] {
    background: var(--card); border: 1px solid var(--line); border-radius: 14px; padding: 1.5rem;
}
.form-title { font-size: 1.4rem; font-weight: 700; margin: 0.5rem 0 0.25rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================
# KẾT NỐI SUPABASE
# ==========================================
@st.cache_resource
def create_supabase_client(supabase_url: str, supabase_key: str) -> Client:
    return create_client(supabase_url, supabase_key)

def init_supabase() -> Optional[Client]:
    try:
        supabase_url = st.secrets.get("SUPABASE_URL", "")
        supabase_key = (
            st.secrets.get("SUPABASE_SECRET_KEY", "")
            or st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", "")
        )
    except StreamlitSecretNotFoundError:
        supabase_url, supabase_key = "", ""

    if not supabase_url or not supabase_key:
        st.warning(
            "Chưa cấu hình khóa Supabase. Thêm SUPABASE_URL và SUPABASE_SECRET_KEY "
            "(hoặc SUPABASE_SERVICE_ROLE_KEY) vào .streamlit/secrets.toml."
        )
        return None
    return create_supabase_client(supabase_url, supabase_key)

supabase = init_supabase()
TABLE_NAME = "order"
STATUS_LIST = ["pending", "completed", "cancelled"]
STATUS_LABEL = {"pending": "Chờ xử lý", "completed": "Hoàn thành", "cancelled": "Đã hủy"}

# ==========================================
# XỬ LÝ DỮ LIỆU (CRUD)
# ==========================================
def fetch_orders():
    if not supabase:
        return []
    try:
        res = supabase.table(TABLE_NAME).select("*").order("id", desc=True).execute()
        return res.data
    except Exception as e:
        st.error(f"Không tải được dữ liệu từ bảng '{TABLE_NAME}': {e}")
        return []

def _build_payload(customer_name, product, quantity, price, order_date, status):
    return {
        "customer_name": customer_name.strip(),
        "product": product.strip(),
        "quantity": int(quantity),
        "price": int(price),
        "order_date": str(order_date),
        "status": status,
    }

def insert_order(*args):
    try:
        res = supabase.table(TABLE_NAME).insert(_build_payload(*args)).execute()
        return True, res.data
    except Exception as e:
        return False, str(e)

def update_order(order_id, *args):
    try:
        res = supabase.table(TABLE_NAME).update(_build_payload(*args)).eq("id", order_id).execute()
        return True, res.data
    except Exception as e:
        return False, str(e)

# ==========================================
# TIỆN ÍCH
# ==========================================
def vnd(value) -> str:
    try:
        return f"{int(value):,}".replace(",", ".") + " ₫"
    except (TypeError, ValueError):
        return "-"

def fmt_date(value) -> str:
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(value or "-")

def esc(value) -> str:
    return html.escape(str(value if value is not None else ""))

# ==========================================
# ĐIỀU HƯỚNG
# ==========================================
st.session_state.setdefault("page", "list")
st.session_state.setdefault("selected_order", None)
st.session_state.setdefault("flash", None)

def go(page: str, order=None):
    st.session_state.page = page
    st.session_state.selected_order = order
    st.rerun()

# ==========================================
# MÀN HÌNH 1: DANH SÁCH
# ==========================================
def page_list():
    head_l, head_r = st.columns([5, 1.4], vertical_alignment="center")
    with head_l:
        st.markdown(
            '<p class="page-title">Đơn hàng</p>'
            '<p class="page-sub">Theo dõi, thêm mới và chỉnh sửa đơn hàng.</p>',
            unsafe_allow_html=True,
        )
    with head_r:
        if st.button("＋ Thêm đơn hàng", type="primary", use_container_width=True):
            go("add")

    if st.session_state.flash:
        st.success(st.session_state.flash)
        st.session_state.flash = None

    orders = fetch_orders()

    # --- Số liệu tổng quan ---
    total = len(orders)
    pending = sum(1 for o in orders if o.get("status") == "pending")
    revenue = sum(
        int(o.get("quantity") or 0) * int(o.get("price") or 0)
        for o in orders
        if o.get("status") != "cancelled"
    )
    s1, s2, s3 = st.columns(3)
    s1.markdown(f'<div class="stat"><div class="label">Tổng đơn hàng</div><div class="value">{total}</div></div>', unsafe_allow_html=True)
    s2.markdown(f'<div class="stat"><div class="label">Đang chờ xử lý</div><div class="value">{pending}</div></div>', unsafe_allow_html=True)
    s3.markdown(f'<div class="stat accent"><div class="label">Doanh thu (không tính đơn đã hủy)</div><div class="value">{vnd(revenue)}</div></div>', unsafe_allow_html=True)

    st.write("")

    # --- Tìm kiếm & lọc ---
    f1, f2 = st.columns([3, 1.4])
    keyword = f1.text_input("Tìm kiếm", placeholder="Tìm theo tên khách hàng hoặc sản phẩm", label_visibility="collapsed")
    status_filter = f2.selectbox(
        "Trạng thái", ["all"] + STATUS_LIST,
        format_func=lambda s: "Tất cả trạng thái" if s == "all" else STATUS_LABEL[s],
        label_visibility="collapsed",
    )

    kw = keyword.strip().lower()
    filtered = [
        o for o in orders
        if (status_filter == "all" or o.get("status") == status_filter)
        and (not kw or kw in str(o.get("customer_name", "")).lower() or kw in str(o.get("product", "")).lower())
    ]

    if not orders:
        st.info("Chưa có đơn hàng nào. Chọn “Thêm đơn hàng” để tạo đơn đầu tiên.")
        return
    if not filtered:
        st.info("Không có đơn hàng nào khớp với bộ lọc.")
        return

    # --- Bảng đơn hàng ---
    widths = [0.7, 2.4, 2.6, 0.8, 1.6, 1.4, 1.5, 0.7]
    heads = ["Mã", "Khách hàng", "Sản phẩm", "SL", "Thành tiền", "Ngày đặt", "Trạng thái", ""]
    for col, h in zip(st.columns(widths), heads):
        col.markdown(f'<div class="col-head">{h}</div>', unsafe_allow_html=True)

    for o in filtered:
        with st.container(border=True):
            c = st.columns(widths, vertical_alignment="center")
            qty = int(o.get("quantity") or 0)
            price = int(o.get("price") or 0)
            status = o.get("status", "pending")
            c[0].markdown(f'<span class="cell-sub">#{esc(o["id"])}</span>', unsafe_allow_html=True)
            c[1].markdown(f'<div class="cell-main">{esc(o.get("customer_name"))}</div>', unsafe_allow_html=True)
            c[2].markdown(f'<div class="cell-main">{esc(o.get("product"))}</div>'
                          f'<div class="cell-sub">Đơn giá {vnd(price)}</div>', unsafe_allow_html=True)
            c[3].markdown(f'<span class="cell-num">{qty}</span>', unsafe_allow_html=True)
            c[4].markdown(f'<span class="cell-num">{vnd(qty * price)}</span>', unsafe_allow_html=True)
            c[5].markdown(f'<span class="cell-sub">{fmt_date(o.get("order_date"))}</span>', unsafe_allow_html=True)
            c[6].markdown(
                f'<span class="pill {esc(status)}">{esc(STATUS_LABEL.get(status, status))}</span>',
                unsafe_allow_html=True,
            )
            if c[7].button("✏️", key=f"edit_{o['id']}", help="Chỉnh sửa đơn hàng", use_container_width=True):
                go("edit", o)

# ==========================================
# MÀN HÌNH 2: THÊM ĐƠN HÀNG
# ==========================================
def page_add():
    _, mid, _ = st.columns([1, 2.4, 1])
    with mid:
        if st.button("← Quay lại danh sách"):
            go("list")
        st.markdown('<p class="form-title">Thêm đơn hàng mới</p>'
                    '<p class="page-sub">Nhập thông tin đơn hàng rồi lưu.</p>', unsafe_allow_html=True)

        with st.form("form_add_order"):
            customer_name = st.text_input("Tên khách hàng")
            product = st.text_input("Tên sản phẩm")
            c1, c2 = st.columns(2)
            quantity = c1.number_input("Số lượng", min_value=1, value=1, step=1)
            price = c2.number_input("Đơn giá (VNĐ)", min_value=0, value=100000, step=10000)
            c3, c4 = st.columns(2)
            order_date = c3.date_input("Ngày đặt hàng", value=date.today(), format="DD/MM/YYYY")
            status = c4.selectbox("Trạng thái", STATUS_LIST, format_func=lambda s: STATUS_LABEL[s])

            if st.form_submit_button("Lưu đơn hàng", type="primary", use_container_width=True):
                if not supabase:
                    st.error("Chưa kết nối Supabase.")
                elif not customer_name.strip() or not product.strip():
                    st.error("Nhập tên khách hàng và tên sản phẩm để tiếp tục.")
                else:
                    ok, msg = insert_order(customer_name, product, quantity, price, order_date, status)
                    if ok:
                        st.session_state.flash = "Đã thêm đơn hàng mới."
                        go("list")
                    else:
                        st.error(f"Không thêm được đơn hàng: {msg}")

# ==========================================
# MÀN HÌNH 3: CHỈNH SỬA ĐƠN HÀNG
# ==========================================
def page_edit():
    sel = st.session_state.selected_order
    if not sel:
        go("list")
    order_id = sel["id"]

    try:
        parsed_date = datetime.strptime(str(sel.get("order_date")), "%Y-%m-%d").date()
    except Exception:
        parsed_date = date.today()
    current_status = sel.get("status", "pending")
    status_idx = STATUS_LIST.index(current_status) if current_status in STATUS_LIST else 0

    _, mid, _ = st.columns([1, 2.4, 1])
    with mid:
        if st.button("← Quay lại danh sách"):
            go("list")
        st.markdown(f'<p class="form-title">Chỉnh sửa đơn hàng #{esc(order_id)}</p>'
                    '<p class="page-sub">Cập nhật thông tin rồi lưu thay đổi.</p>', unsafe_allow_html=True)

        with st.form(f"form_edit_order_{order_id}"):
            customer_name = st.text_input("Tên khách hàng", value=sel.get("customer_name", ""))
            product = st.text_input("Tên sản phẩm", value=sel.get("product", ""))
            c1, c2 = st.columns(2)
            quantity = c1.number_input("Số lượng", min_value=1, value=int(sel.get("quantity") or 1), step=1)
            price = c2.number_input("Đơn giá (VNĐ)", min_value=0, value=int(sel.get("price") or 0), step=10000)
            c3, c4 = st.columns(2)
            order_date = c3.date_input("Ngày đặt hàng", value=parsed_date, format="DD/MM/YYYY")
            status = c4.selectbox("Trạng thái", STATUS_LIST, index=status_idx, format_func=lambda s: STATUS_LABEL[s])

            if st.form_submit_button("Lưu thay đổi", type="primary", use_container_width=True):
                if not supabase:
                    st.error("Chưa kết nối Supabase.")
                elif not customer_name.strip() or not product.strip():
                    st.error("Nhập tên khách hàng và tên sản phẩm để tiếp tục.")
                else:
                    ok, msg = update_order(order_id, customer_name, product, quantity, price, order_date, status)
                    if ok:
                        st.session_state.flash = f"Đã cập nhật đơn hàng #{order_id}."
                        go("list")
                    else:
                        st.error(f"Không cập nhật được đơn hàng: {msg}")

# ==========================================
# ROUTER
# ==========================================
{"list": page_list, "add": page_add, "edit": page_edit}[st.session_state.page]()