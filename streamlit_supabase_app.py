import streamlit as st
from datetime import datetime, date
from supabase import create_client, Client
from streamlit.errors import StreamlitSecretNotFoundError
from typing import Optional

# ==========================================
# CẤU HÌNH TRANG VÀ KẾT NỐI SUPABASE
# ==========================================
st.set_page_config(page_title="Hệ Thống Quản Lý Đơn Hàng", page_icon="📦", layout="wide")

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
            "⚠️ Chưa cấu hình khóa bí mật Supabase server-side. "
            "Thêm SUPABASE_SECRET_KEY (hoặc SUPABASE_SERVICE_ROLE_KEY) vào "
            ".streamlit/secrets.toml. Không dùng khóa publishable/anon cho ứng dụng nội bộ."
        )
        return None
    return create_supabase_client(supabase_url, supabase_key)

supabase = init_supabase()
TABLE_NAME = "order"
STATUS_LIST = ["pending", "completed", "cancelled"]

# ==========================================
# CÁC HÀM XỬ LÝ DỮ LIỆU (CRUD)
# ==========================================
def fetch_orders():
    if not supabase:
        return []
    try:
        res = supabase.table(TABLE_NAME).select("*").order("id", desc=False).execute()
        return res.data
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu từ bảng '{TABLE_NAME}': {e}")
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
# ĐIỀU HƯỚNG GIỮA CÁC MÀN HÌNH
# ==========================================
st.session_state.setdefault("page", "list")        # list | add | edit
st.session_state.setdefault("selected_order", None)
st.session_state.setdefault("flash", None)

def go(page: str, order=None):
    st.session_state.page = page
    st.session_state.selected_order = order
    st.rerun()

# ==========================================
# MÀN HÌNH 1: DANH SÁCH ĐƠN HÀNG
# ==========================================
def page_list():
    st.title("📦 Hệ Thống Quản Lý Đơn Hàng")

    if st.session_state.flash:
        st.success(st.session_state.flash)
        st.session_state.flash = None

    top_l, top_r = st.columns([5, 1])
    with top_l:
        st.header("📜 Danh Sách Đơn Hàng")
    with top_r:
        if st.button("➕ Thêm Đơn Hàng", use_container_width=True, type="primary"):
            go("add")

    orders = fetch_orders()
    if not orders:
        st.info("Chưa có đơn hàng. Hãy thêm một đơn hàng mới!")
        return

    widths = [1, 3, 3, 1.2, 2, 2, 2, 1]
    headers = ["ID", "Khách hàng", "Sản phẩm", "SL", "Đơn giá (VNĐ)", "Ngày đặt", "Trạng thái", ""]
    for col, h in zip(st.columns(widths), headers):
        col.markdown(f"**{h}**")
    st.divider()

    for o in orders:
        c = st.columns(widths)
        c[0].write(o["id"])
        c[1].write(o.get("customer_name", ""))
        c[2].write(o.get("product", ""))
        c[3].write(o.get("quantity", ""))
        price = o.get("price")
        c[4].write(f"{int(price):,}".replace(",", ".") if price is not None else "")
        c[5].write(o.get("order_date", ""))
        c[6].write(o.get("status", ""))
        if c[7].button("✏️", key=f"edit_{o['id']}", help="Chỉnh sửa đơn hàng"):
            go("edit", o)

# ==========================================
# MÀN HÌNH 2: THÊM ĐƠN HÀNG MỚI
# ==========================================
def page_add():
    st.title("➕ Thêm Đơn Hàng Mới")
    if st.button("⬅️ Quay lại danh sách"):
        go("list")

    with st.form("form_add_order"):
        customer_name = st.text_input("Tên khách hàng")
        product = st.text_input("Tên sản phẩm")
        c1, c2 = st.columns(2)
        quantity = c1.number_input("Số lượng", min_value=1, value=1, step=1)
        price = c2.number_input("Đơn giá (VNĐ)", min_value=0, value=100000, step=10000)
        order_date = st.date_input("Ngày đặt hàng", value=date.today())
        status = st.selectbox("Trạng thái", STATUS_LIST)

        if st.form_submit_button("💾 Lưu đơn hàng", use_container_width=True):
            if not supabase:
                st.error("Chưa kết nối Supabase!")
            elif not customer_name.strip() or not product.strip():
                st.error("Vui lòng nhập tên khách hàng và tên sản phẩm.")
            else:
                ok, msg = insert_order(customer_name, product, quantity, price, order_date, status)
                if ok:
                    st.session_state.flash = "✅ Đã thêm đơn hàng mới thành công!"
                    go("list")
                else:
                    st.error(f"❌ Thêm đơn hàng thất bại: {msg}")

# ==========================================
# MÀN HÌNH 3: CHỈNH SỬA ĐƠN HÀNG
# ==========================================
def page_edit():
    sel = st.session_state.selected_order
    if not sel:
        go("list")
    order_id = sel["id"]

    st.title(f"✏️ Chỉnh Sửa Đơn Hàng ID {order_id}")
    if st.button("⬅️ Quay lại danh sách"):
        go("list")

    try:
        parsed_date = datetime.strptime(str(sel.get("order_date")), "%Y-%m-%d").date()
    except Exception:
        parsed_date = date.today()
    current_status = sel.get("status", "pending")
    status_idx = STATUS_LIST.index(current_status) if current_status in STATUS_LIST else 0

    with st.form(f"form_edit_order_{order_id}"):
        c1, c2 = st.columns(2)
        with c1:
            customer_name = st.text_input("Tên khách hàng", value=sel.get("customer_name", ""))
            product = st.text_input("Tên sản phẩm", value=sel.get("product", ""))
            order_date = st.date_input("Ngày đặt hàng", value=parsed_date)
        with c2:
            quantity = st.number_input("Số lượng", min_value=1, value=int(sel.get("quantity") or 1), step=1)
            price = st.number_input("Đơn giá (VNĐ)", min_value=0, value=int(sel.get("price") or 0), step=10000)
            status = st.selectbox("Trạng thái", STATUS_LIST, index=status_idx)

        if st.form_submit_button("💾 Cập nhật thay đổi", use_container_width=True):
            if not supabase:
                st.error("Chưa kết nối Supabase!")
            elif not customer_name.strip() or not product.strip():
                st.error("Vui lòng nhập tên khách hàng và tên sản phẩm.")
            else:
                ok, msg = update_order(order_id, customer_name, product, quantity, price, order_date, status)
                if ok:
                    st.session_state.flash = f"✅ Đã cập nhật thành công đơn hàng ID {order_id}!"
                    go("list")
                else:
                    st.error(f"❌ Cập nhật thất bại: {msg}")

# ==========================================
# ROUTER
# ==========================================
{"list": page_list, "add": page_add, "edit": page_edit}[st.session_state.page]()