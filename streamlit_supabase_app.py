
# ==========================================
# GIAO DIỆN NGƯỜI DÙNG - 2 MÀN HÌNH RIÊNG
# ==========================================

st.title("📦 Hệ Thống Quản Lý Đơn Hàng")

# Khởi tạo trạng thái điều hướng
if "page" not in st.session_state:
    st.session_state.page = "list"

if "selected_order" not in st.session_state:
    st.session_state.selected_order = None


# ==========================================
# MÀN HÌNH 1: DANH SÁCH ĐƠN HÀNG
# ==========================================
def show_order_list():
    col_title, col_add = st.columns([5, 1])

    with col_title:
        st.header("📜 Danh Sách Đơn Hàng")

    with col_add:
        if st.button("➕ Add", use_container_width=True):
            st.session_state.page = "add"
            st.rerun()

    st.markdown("---")

    orders = fetch_orders()

    if not orders:
        st.info("Chưa có đơn hàng. Hãy thêm một đơn hàng mới!")
        return

    # Tiêu đề danh sách
    st.caption(f"Tổng số đơn hàng: {len(orders)}")

    for o in orders:
        order_id = o["id"]

        with st.container(border=True):
            col_info, col_edit = st.columns([10, 1])

            with col_info:
                st.markdown(
                    f"**ID {order_id} - "
                    f"{o.get('customer_name', '')} "
                    f"({o.get('product', '')})**"
                )

                st.write(
                    f"Số lượng: {o.get('quantity', '')} | "
                    f"Đơn giá: {o.get('price', 0):,} VNĐ | "
                    f"Ngày đặt: {o.get('order_date', '')} | "
                    f"Trạng thái: {o.get('status', '')}"
                )

            with col_edit:
                if st.button(
                    "✏️",
                    key=f"edit_{order_id}",
                    help="Chỉnh sửa đơn hàng",
                    use_container_width=True
                ):
                    st.session_state.selected_order = o
                    st.session_state.page = "edit"
                    st.rerun()


# ==========================================
# MÀN HÌNH 2: THÊM ĐƠN HÀNG
# ==========================================
def show_add_order():
    st.header("➕ Thêm Đơn Hàng Mới")

    if st.button("⬅️ Quay lại danh sách"):
        st.session_state.page = "list"
        st.rerun()

    with st.form("form_add_order"):
        customer_name = st.text_input("Tên khách hàng")
        product = st.text_input("Tên sản phẩm")

        col1, col2 = st.columns(2)

        with col1:
            quantity = st.number_input(
                "Số lượng", min_value=1, value=1, step=1
            )

        with col2:
            price = st.number_input(
                "Đơn giá (VNĐ)", min_value=0,
                value=100000, step=10000
            )

        order_date = st.date_input(
            "Ngày đặt hàng", value=date.today()
        )

        status = st.selectbox(
            "Trạng thái",
            ["pending", "completed", "cancelled"]
        )

        submitted = st.form_submit_button(
            "💾 Lưu đơn hàng",
            use_container_width=True
        )

        if submitted:
            if not supabase:
                st.error("Chưa kết nối Supabase!")
            elif not customer_name.strip() or not product.strip():
                st.warning("Vui lòng nhập tên khách hàng và sản phẩm!")
            else:
                success, msg = insert_order(
                    customer_name.strip(),
                    product.strip(),
                    quantity,
                    price,
                    order_date,
                    status
                )

                if success:
                    st.session_state.page = "list"
                    st.session_state.selected_order = None
                    st.session_state.flash_message = (
                        "Đã thêm đơn hàng thành công!"
                    )
                    st.rerun()
                else:
                    st.error(f"Thêm đơn hàng thất bại: {msg}")


# ==========================================
# MÀN HÌNH 3: CHỈNH SỬA ĐƠN HÀNG
# ==========================================
def show_edit_order():
    sel = st.session_state.selected_order

    if not sel:
        st.session_state.page = "list"
        st.rerun()
        return

    order_id = sel["id"]

    st.header(f"✏️ Chỉnh Sửa Đơn Hàng ID {order_id}")

    if st.button("⬅️ Quay lại danh sách"):
        st.session_state.page = "list"
        st.session_state.selected_order = None
        st.rerun()

    try:
        parsed_date = date.fromisoformat(str(sel["order_date"])[:10])
    except (ValueError, TypeError, KeyError):
        parsed_date = date.today()

    status_list = ["pending", "completed", "cancelled"]
    current_status = sel.get("status", "pending")
    status_index = (
        status_list.index(current_status)
        if current_status in status_list else 0
    )

    with st.form(f"form_edit_order_{order_id}"):
        col1, col2 = st.columns(2)

        with col1:
            edit_customer = st.text_input(
                "Tên khách hàng",
                value=sel.get("customer_name", "")
            )
            edit_product = st.text_input(
                "Tên sản phẩm",
                value=sel.get("product", "")
            )
            edit_date = st.date_input(
                "Ngày đặt hàng", value=parsed_date
            )

        with col2:
            edit_quantity = st.number_input(
                "Số lượng",
                min_value=1,
                value=max(1, int(sel.get("quantity") or 1)),
                step=1
            )
            edit_price = st.number_input(
                "Đơn giá (VNĐ)",
                min_value=0,
                value=max(0, int(sel.get("price") or 0)),
                step=10000
            )
            edit_status = st.selectbox(
                "Trạng thái",
                status_list,
                index=status_index
            )

        submitted = st.form_submit_button(
            "💾 Lưu thay đổi",
            use_container_width=True
        )

        if submitted:
            if not supabase:
                st.error("Chưa kết nối Supabase!")
            elif not edit_customer.strip() or not edit_product.strip():
                st.warning("Vui lòng nhập tên khách hàng và sản phẩm!")
            else:
                success, msg = update_order(
                    order_id,
                    edit_customer.strip(),
                    edit_product.strip(),
                    edit_quantity,
                    edit_price,
                    edit_date,
                    edit_status
                )

                if success:
                    st.session_state.page = "list"
                    st.session_state.selected_order = None
                    st.session_state.flash_message = (
                        f"Đã cập nhật đơn hàng ID {order_id} thành công!"
                    )
                    st.rerun()
                else:
                    st.error(f"Cập nhật thất bại: {msg}")


# ==========================================
# ĐIỀU HƯỚNG GIỮA CÁC MÀN HÌNH
# ==========================================
if st.session_state.page == "list":
    flash_message = st.session_state.pop("flash_message", None)

    if flash_message:
        st.success(f"✅ {flash_message}")

    show_order_list()

elif st.session_state.page == "add":
    show_add_order()

elif st.session_state.page == "edit":
    show_edit_order()
