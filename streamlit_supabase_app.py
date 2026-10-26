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
        supabase_key = st.secrets.get("SUPABASE_KEY", "")
    except StreamlitSecretNotFoundError:
        supabase_url = ""
        supabase_key = ""

    if not supabase_url or not supabase_key:
        st.warning(
            "⚠️ Chưa đọc được Supabase URL hoặc API Key. "
            "Hãy kiểm tra `.streamlit/secrets.toml` và chạy ứng dụng từ thư mục dự án."
        )
        with st.sidebar.expander("🔑 Cấu hình kết nối Supabase"):
            supabase_url = st.text_input("Supabase URL", value=supabase_url, type="default")
            supabase_key = st.text_input("Supabase Key (Anon/Service)", value=supabase_key, type="password")

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
# ĐIỀU HƯỚNG GIAO DIỆN CHÍNH
# ==========================================
st.sidebar.title("📦 Quản Lý Đơn Hàng")
menu = st.sidebar.radio(
    "Chọn màn hình chức năng:",
    ["📚 Thư viện đơn hàng", "➕ Nhập liệu đơn hàng mới", "✏️ Chỉnh sửa & Xóa đơn hàng"]
)

# Hiển thị trạng thái kết nối
if supabase:
    st.sidebar.success(f"🟢 Đã kết nối Supabase (Bảng: `{TABLE_NAME}`)")
else:
    st.sidebar.error("🔴 Chưa kết nối Supabase")

# ------------------------------------------
# 1. MÀN HÌNH THƯ VIỆN ĐƠN HÀNG (READ)
# ------------------------------------------
if menu == "📚 Thư viện đơn hàng":
    st.header("📚 Thư Viện & Danh Sách Đơn Hàng")
    
    orders = fetch_orders()
    
    if orders:
        df = pd.DataFrame(orders)
        
        # Thống kê nhanh
        col1, col2, col3, col4 = st.columns(4)
        total_orders = len(df)
        total_revenue = (df['quantity'] * df['price']).sum() if 'quantity' in df.columns and 'price' in df.columns else 0
        completed_orders = len(df[df['status'] == 'completed']) if 'status' in df.columns else 0
        pending_orders = len(df[df['status'] == 'pending']) if 'status' in df.columns else 0
        
        col1.metric("Tổng đơn hàng", f"{total_orders}")
        col2.metric("Tổng doanh thu (VNĐ)", f"{total_revenue:,.0f} đ")
        col3.metric("Đã hoàn thành", f"{completed_orders}")
        col4.metric("Chờ xử lý", f"{pending_orders}")
        
        st.divider()
        
        # Bộ lọc tìm kiếm
        filter_col1, filter_col2 = st.columns([2, 1])
        with filter_col1:
            search_query = st.text_input("🔍 Tìm theo tên khách hàng hoặc sản phẩm:")
        with filter_col2:
            status_options = ["Tất cả"] + sorted(list(df['status'].dropna().unique())) if 'status' in df.columns else ["Tất cả"]
            selected_status = st.selectbox("Lọc theo trạng thái:", status_options)
            
        # Áp dụng bộ lọc
        filtered_df = df.copy()
        if search_query:
            filtered_df = filtered_df[
                filtered_df['customer_name'].astype(str).str.contains(search_query, case=False, na=False) |
                filtered_df['product'].astype(str).str.contains(search_query, case=False, na=False)
            ]
        if selected_status != "Tất cả":
            filtered_df = filtered_df[filtered_df['status'] == selected_status]
            
        # Tính thành tiền hiển thị
        if 'quantity' in filtered_df.columns and 'price' in filtered_df.columns:
            filtered_df['total_amount'] = filtered_df['quantity'] * filtered_df['price']

        st.subheader(f"Danh sách kết quả ({len(filtered_df)} đơn)")
        st.dataframe(
            filtered_df,
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", format="%d"),
                "customer_name": "Tên khách hàng",
                "product": "Sản phẩm",
                "quantity": st.column_config.NumberColumn("Số lượng", format="%d"),
                "price": st.column_config.NumberColumn("Đơn giá (VNĐ)", format="%d đ"),
                "total_amount": st.column_config.NumberColumn("Thành tiền (VNĐ)", format="%d đ"),
                "order_date": "Ngày đặt",
                "status": st.column_config.TextColumn("Trạng thái")
            },
            hide_index=True
        )
    else:
        st.info(f"Chưa có đơn hàng nào hoặc chưa kết nối được với bảng `{TABLE_NAME}` trong Supabase.")

# ------------------------------------------
# 2. MÀN HÌNH NHẬP LIỆU (CREATE)
# ------------------------------------------
elif menu == "➕ Nhập liệu đơn hàng mới":
    st.header("➕ Nhập Liệu Đơn Hàng Mới")
    st.write(f"Điền thông tin bên dưới để lưu đơn hàng mới vào bảng `{TABLE_NAME}` trên Supabase.")
    
    with st.form("form_create_order", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            customer_name = st.text_input("Tên khách hàng (*)", placeholder="Ví dụ: Nguyen Van A")
            product = st.text_input("Tên sản phẩm (*)", placeholder="Ví dụ: Ao thun")
            order_date = st.date_input("Ngày đặt hàng", value=date.today())
        with col2:
            quantity = st.number_input("Số lượng (*)", min_value=1, value=1, step=1)
            price = st.number_input("Đơn giá (VNĐ) (*)", min_value=0, value=100000, step=10000)
            status = st.selectbox("Trạng thái đơn hàng", ["pending", "completed", "cancelled"])
            
        submitted = st.form_submit_button("💾 Lưu đơn hàng", use_container_width=True)
        
        if submitted:
            if not customer_name.strip() or not product.strip():
                st.error("Vui lòng điền đầy đủ Tên khách hàng và Sản phẩm!")
            elif not supabase:
                st.error("Chưa kết nối Supabase, không thể lưu dữ liệu!")
            else:
                success, msg = insert_order(customer_name, product, quantity, price, order_date, status)
                if success:
                    st.success(f"✅ Đã thêm đơn hàng thành công vào bảng `{TABLE_NAME}`!")
                    st.balloons()
                else:
                    st.error(f"❌ Thêm đơn hàng thất bại: {msg}")

# ------------------------------------------
# 3. MÀN HÌNH SỬA & XÓA (UPDATE & DELETE)
# ------------------------------------------
elif menu == "✏️ Chỉnh sửa & Xóa đơn hàng":
    st.header("✏️ Chỉnh Sửa & Xóa Đơn Hàng")
    
    orders = fetch_orders()
    if not orders:
        st.info("Hiện không có đơn hàng nào để chỉnh sửa hoặc xóa.")
    else:
        # Chọn đơn hàng cần thao tác
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
                    # Chuyển đổi chuỗi ngày thành datetime.date
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
                            st.rerun()
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
                        st.rerun()
                    else:
                        st.error(f"❌ Xóa thất bại: {msg}")
