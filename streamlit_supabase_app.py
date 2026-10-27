import streamlit as st
import pandas as pd
from datetime import datetime, date
from supabase import create_client, Client
from streamlit.errors import StreamlitSecretNotFoundError
from typing import Optional

# ==========================================
# CẤU HÌNH TRANG VÀ KẾT NỐI SUPABASE
# ==========================================
st.set_page_config(
    page_title="Hệ Thống Quản Lý Đơn Hàng",
    page_icon="📦",
    layout="wide"
)

# Tạo lại kết nối khi cấu hình thay đổi, nhưng không cache trạng thái thiếu cấu hình.
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
        supabase_url = ""
        supabase_key = ""

    if not supabase_url or not supabase_key:
        st.warning(
            "⚠️ Chưa cấu hình khóa bí mật Supabase server-side. "
            "Thêm `SUPABASE_SECRET_KEY` (hoặc `SUPABASE_SERVICE_ROLE_KEY`) vào "
            "`.streamlit/secrets.toml`. Không dùng khóa publishable/anon cho ứng dụng nội bộ."
        )

    if supabase_url and supabase_key:
        return create_supabase_client(supabase_url, supabase_key)
    return None

supabase = init_supabase()
TABLE_NAME = "order"  # Tên bảng trong Supabase: 'order'

# ==========================================
# CÁC HÀM XỬ LÝ DỮ LIỆU (CRUD)
# ==========================================
def fetch_orders():
    """Lấy danh sách tất cả đơn hàng từ Supabase"""
    if not supabase:
        return []
    try:
        response = supabase.table(TABLE_NAME).select("*").order("id", desc=False).execute()
        return response.data
    except Exception as e:
        st.error(f"Lỗi khi tải dữ liệu từ bảng '{TABLE_NAME}': {e}")
        return []

def insert_order(customer_name, product, quantity, price, order_date, status):
    """Thêm một đơn hàng mới vào Supabase"""
    try:
        data = {
            "customer_name": customer_name,
            "product": product,
            "quantity": int(quantity),
            "price": int(price),
            "order_date": str(order_date),
            "status": status
        }
        response = supabase.table(TABLE_NAME).insert(data).execute()
        return True, response.data
    except Exception as e:
        return False, str(e)

def update_order(order_id, customer_name, product, quantity, price, order_date, status):
    """Cập nhật thông tin đơn hàng theo ID"""
    try:
        data = {
            "customer_name": customer_name,
            "product": product,
            "quantity": int(quantity),
            "price": int(price),
            "order_date": str(order_date),
            "status": status
        }
        response = supabase.table(TABLE_NAME).update(data).eq("id", order_id).execute()
        return True, response.data
    except Exception as e:
        return False, str(e)

def delete_order(order_id):
    """Xóa đơn hàng theo ID"""
    try:
        response = supabase.table(TABLE_NAME).delete().eq("id", order_id).execute()
        return True, response.data
    except Exception as e:
        return False, str(e)

# ==========================================
# GIAO DIỆN NGƯỜI DÙNG
# ==========================================
st.title("📦 Hệ Thống Quản Lý Đơn Hàng")

# Section: Thêm Đơn Hàng Mới (trên màn hình chính)
with st.expander("➕ Thêm Đơn Hàng Mới", expanded=False):
    with st.form("form_add_order"):
        customer_name = st.text_input("Tên khách hàng", key="add_customer")
        product = st.text_input("Tên sản phẩm", key="add_product")
        col1_add, col2_add = st.columns(2)
        with col1_add:
            quantity = st.number_input("Số lượng", min_value=1, value=1, step=1, key="add_quantity")
        with col2_add:
            price = st.number_input("Đơn giá (VNĐ)", min_value=0, value=100000, step=10000, key="add_price")
        order_date = st.date_input("Ngày đặt hàng", value=date.today(), key="add_order_date")
        status_list = ["pending", "completed", "cancelled"]
        status = st.selectbox("Trạng thái", status_list, key="add_status")
        
        btn_add = st.form_submit_button("➕ Thêm Đơn Hàng", use_container_width=True)
        
        if btn_add:
            if not supabase:
                st.error("Chưa kết nối Supabase!")
            else:
                success, msg = insert_order(customer_name, product, quantity, price, order_date, status)
                if success:
                    st.success("✅ Đã thêm đơn hàng mới thành công!")
                    st.experimental_rerun()
                else:
                    st.error(f"❌ Thêm đơn hàng thất bại: {msg}")

st.markdown("---")

# Section: Danh Sách Đơn Hàng
st.header("📜 Danh Sách Đơn Hàng")

orders = fetch_orders()
if orders:
    df = pd.DataFrame(orders)
    # Reorder columns to have 'id' first for better visibility
    df = df[["id", "customer_name", "product", "quantity", "price", "order_date", "status"]]
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Section: Quản Lý Đơn Hàng
    st.subheader("🛠️ Quản Lý Đơn Hàng")
    
    # Create a dictionary for easier lookup
    order_dict = {f"ID {o['id']} - {o.get('customer_name', '')} ({o.get('product', '')})": o for o in orders}
    selected_label = st.selectbox("Chọn đơn hàng cần sửa hoặc xóa:", list(order_dict.keys()))
    selected_order = order_dict[selected_label]
    
    order_id = selected_order['id']
    
    st.write(f"Đang chọn đơn hàng: **ID {order_id}**")
    
    tab_edit, tab_delete = st.tabs(["✏️ Chỉnh sửa thông tin", "🗑️ Xóa đơn hàng"])
    
    # TAB SỬA
    with tab_edit:
        with st.form("form_edit_order"):
            col1, col2 = st.columns(2)
            with col1:
                edit_customer = st.text_input("Tên khách hàng", value=selected_order.get('customer_name', ''))
                edit_product = st.text_input("Tên sản phẩm", value=selected_order.get('product', ''))
                current_date_val = selected_order.get('order_date')
                try:
                    parsed_date = datetime.strptime(str(current_date_val), "%Y-%m-%d").date()
                except Exception:
                    parsed_date = date.today()
                edit_date = st.date_input("Ngày đặt hàng", value=parsed_date)
            with col2:
                edit_quantity = st.number_input("Số lượng", min_value=1, value=int(selected_order.get('quantity', 1)), step=1)
                edit_price = st.number_input("Đơn giá (VNĐ)", min_value=0, value=int(selected_order.get('price', 0)), step=10000)
                status_list = ["pending", "completed", "cancelled"]
                current_status = selected_order.get('status', 'pending')
                default_status_idx = status_list.index(current_status) if current_status in status_list else 0
                edit_status = st.selectbox("Trạng thái", status_list, index=default_status_idx)
            btn_update = st.form_submit_button("💾 Cập nhật thay đổi", use_container_width=True)
            if btn_update:
                if not supabase:
                    st.error("Chưa kết nối Supabase!")
                else:
                    success, msg = update_order(
                        order_id, edit_customer, edit_product, edit_quantity, edit_price, edit_date, edit_status
                    )
                    if success:
                        st.success(f"✅ Đã cập nhật thành công đơn hàng ID {order_id}!")
                        st.experimental_rerun()
                    else:
                        st.error(f"❌ Cập nhật thất bại: {msg}")

    # TAB XÓA
    with tab_delete:
        st.warning(f"⚠️ Cảnh báo: Hành động này sẽ xóa vĩnh viễn đơn hàng **ID {order_id}** ({selected_order.get('customer_name')} - {selected_order.get('product')}) khỏi bảng `{TABLE_NAME}`!")
        confirm_delete = st.checkbox("Tôi xác nhận muốn xóa đơn hàng này.")
        if st.button("🗑️ Xác nhận xóa", type="primary", disabled=not confirm_delete):
            if not supabase:
                st.error("Chưa kết nối Supabase!")
            else:
                success, msg = delete_order(order_id)
                if success:
                    st.success(f"✅ Đã xóa đơn hàng ID {order_id} thành công!")
                    st.experimental_rerun()
                else:
                    st.error(f"❌ Xóa thất bại: {msg}")
else:
    st.info("Chưa có đơn hàng nào. Hãy thêm một đơn hàng mới!")
