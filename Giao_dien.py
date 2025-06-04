import tkinter as tk
import json
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import datetime
from Login import show_login_window
from Helper import center_window
from Data_process import load_users, save_users, load_products,load_categories, get_next_order_id


# ===== Load dữ liệu từ module xử lý =====
product_data = load_products()
type_data = load_categories()

# Gom nhóm danh mục theo loại
menu_structure = {
    "Nón bảo hiểm": [],
    "Phụ kiện": [],
    "Đồ bảo hộ": []
}

for t in type_data:
    name = t.get("type_name", "")
    loai = t.get("loai", 0)
    if loai == 1:
        menu_structure["Nón bảo hiểm"].append({"name": name, "type_id": t.get("type_id")})
    elif loai == 2:
        menu_structure["Phụ kiện"].append({"name": name, "type_id": t.get("type_id")})
    elif loai == 3:
        menu_structure["Đồ bảo hộ"].append({"name": name, "type_id": t.get("type_id")})

# Tạo danh sách sản phẩm
all_products = []
for p in product_data:
    image_path = p.get("main_image", "").replace("\\", "/")
    if not image_path.startswith("images/"):
        image_path = os.path.join("images", image_path)

    all_products.append({
        "id": p.get("id"),
        "image": image_path,
        "name": p.get("product_name", "Sản phẩm không tên"),
        "price": p.get("price", "Liên hệ"),
        "description": p.get("description", "Không có mô tả."),
        "type_id": p.get("type_id"),
        "main_image": image_path,
        "gallery_images": [img.replace("\\", "/") for img in p.get("gallery_images", [])]
    })

# Biến toàn cục và phân trang
products_per_page = 12
current_page = 0
logged_in = False
current_user = None
root = None
search_entry = None
header_frame = None
account_frame = None
content_frame = None
canvas = None
scrollbar = None
scrollable_frame = None
scrollable_frame_id = None
columns = 4 
current_product_list = all_products.copy()
menu_items_widgets = []
SEARCH_PLACEHOLDER = "Tìm kiếm sản phẩm..."
logo_photo = None 


def paginate(products, page):
    start = page * products_per_page
    end = start + products_per_page
    return products[start:end]

# ===== Hàm giao diện =====
def show_product_popup(product):
    popup = tk.Toplevel()
    popup.title("Chi Tiết Sản Phẩm")
    center_window(popup, 800, 550)
    popup.resizable(False, False)
    popup.configure(bg="#232333")

    popup.gallery_photos = [] 
    main_photo_ref = {"photo": None} 
    main_img_label_ref = {"label": None}

    main_img_size = (300, 300) 
    thumbnail_size = (80, 80)

    def update_main_image(new_image_path):
        try:
            if os.path.exists(new_image_path):
                new_img = Image.open(new_image_path).resize(main_img_size, Image.LANCZOS)
                new_photo = ImageTk.PhotoImage(new_img)
                
                if main_img_label_ref["label"]:
                    main_img_label_ref["label"].config(image=new_photo)
                    main_photo_ref["photo"] = new_photo 
            else:
                messagebox.showerror("Lỗi Ảnh", f"Không thể tìm thấy ảnh: {new_image_path}")
        except Exception as e:
            messagebox.showerror("Lỗi Ảnh", f"Lỗi khi tải ảnh: {new_image_path}\n{e}")

    image_frame = tk.Frame(popup, bg="#232333")
    image_frame.pack(side="left", padx=20, pady=20, fill="y")

    product_main_image_path = product.get("main_image", "").replace("\\", "/")
    
    try:
        if product_main_image_path and os.path.exists(product_main_image_path):
            img = Image.open(product_main_image_path).resize(main_img_size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(image_frame, image=photo, bg="#232333")
            img_label.image = photo 
            main_photo_ref["photo"] = photo 
            main_img_label_ref["label"] = img_label 
        else:
            img_label = tk.Label(image_frame, text="[Không có ảnh]", bg="#3C3C58", fg="white", 
                                 width=int(main_img_size[0]/10), height=int(main_img_size[1]/10),
                                 relief="solid", bd=1)
    except Exception as e:
        img_label = tk.Label(image_frame, text=f"[Lỗi tải ảnh: {str(e)}]", bg="#3C3C58", fg="white", 
                             width=int(main_img_size[0]/10), height=int(main_img_size[1]/10),
                             relief="solid", bd=1)
    
    img_label.pack(pady=10)

    gallery_frame = tk.Frame(image_frame, bg="#232333")
    gallery_frame.pack(pady=(0, 10)) 
    
    gallery_images = product.get("gallery_images", []) 
    
    max_thumbnails_to_show = 5 
    for i, img_rel_path in enumerate(gallery_images):
        if i >= max_thumbnails_to_show:
            break 

        full_path = img_rel_path.replace("\\", "/") 

        try:
            if os.path.exists(full_path):
                thumb_img = Image.open(full_path).resize(thumbnail_size, Image.LANCZOS)
                thumb_photo = ImageTk.PhotoImage(thumb_img)
                
                popup.gallery_photos.append(thumb_photo) 
                
                thumb_label = tk.Label(gallery_frame, image=thumb_photo, bg="#232333", cursor="hand2", bd=1, relief="solid")
                thumb_label.image = thumb_photo 
                
                thumb_label.bind("<Button-1>", lambda e, p=full_path: update_main_image(p)) 
                
                thumb_label.pack(side="left", padx=2, pady=2)
            else:
                tk.Label(gallery_frame, text="[FILE KHÔNG TỒN TỒN TẠI]", font=("Arial", 7), bg="#3C3C58", fg="white", 
                         width=int(thumbnail_size[0]/10), height=int(thumbnail_size[1]/10), 
                         bd=1, relief="solid").pack(side="left", padx=2, pady=2)
        except Exception:
            tk.Label(gallery_frame, text=f"[LỖI TẢI]", font=("Arial", 7), bg="#3C3C58", fg="white", 
                     width=int(thumbnail_size[0]/10), height=int(thumbnail_size[1]/10), 
                     bd=1, relief="solid").pack(side="left", padx=2, pady=2)

    details_frame = tk.Frame(popup, bg="#232333")
    details_frame.pack(side="left", padx=20, pady=20, fill="both", expand=True)

    tk.Label(details_frame, text=product.get("name", "N/A"), font=("Arial", 16, "bold"), bg="#232333", fg="white").pack(anchor="w", pady=(0, 5))
    tk.Label(details_frame, text=f"Giá: {product.get('price', 'N/A')} VNĐ", font=("Arial", 12, "bold"), bg="#232333", fg="#00ADB5").pack(anchor="w", pady=(0, 10))

    description_label = tk.Label(details_frame, text="Mô tả:", font=("Arial", 10, "bold"), bg="#232333", fg="white")
    description_label.pack(anchor="w", pady=(0, 2))
    
    description_text = tk.Text(details_frame, wrap="word", height=8, font=("Arial", 9), 
                               bg="#3C3C58", fg="white", bd=0, relief="flat", padx=5, pady=5)
    description_text.insert(tk.END, product.get("description", "Không có mô tả."))
    description_text.config(state="disabled")
    description_text.pack(anchor="w", fill="x", pady=(0, 10))

    button_frame = tk.Frame(details_frame, bg="#232333")
    button_frame.pack(pady=20)

    add_to_cart_btn = tk.Button(button_frame, text="Thêm vào giỏ hàng", font=("Arial", 10, "bold"), bg="#00ADB5", fg="white", command=lambda: add_to_cart(product.get("id")), bd=0, relief="flat", padx=15, pady=8, cursor="hand2")
    add_to_cart_btn.pack(side="left", padx=10)

    close_btn = tk.Button(button_frame, text="Đóng", font=("Arial", 10, "bold"), bg="#3C3C58", fg="white", command=popup.destroy,  bd=0, relief="flat", padx=15, pady=8, cursor="hand2")
    close_btn.pack(side="left", padx=10)

    popup.grab_set() 
    popup.transient(root) 
    root.wait_window(popup)

def add_to_cart_with_quantity(product_id, quantity):
    global current_user

    if not logged_in:
        messagebox.showwarning("Thông báo", "Vui lòng đăng nhập để thêm sản phẩm vào giỏ")
        return

    if quantity <= 0:
        messagebox.showwarning("Lỗi", "Số lượng phải lớn hơn 0.")
        return

    accounts = load_users()
    username = current_user["username"]

    for account in accounts:
        if account["username"] == username:
            found_item = False
            for item in account["cart"]:
                if item["product_id"] == product_id:
                    item["quantity"] += quantity
                    found_item = True
                    break

            if not found_item:
                account["cart"].append({
                    "product_id": product_id,
                    "quantity": quantity
                })

            save_users(accounts)
            messagebox.showinfo("Thành công", f"Đã thêm {quantity} sản phẩm vào giỏ hàng")
            return

    messagebox.showerror("Lỗi", "Không tìm thấy tài khoản")

def create_product_card(parent, product, row, col):
    card_bg = "#3C3C58" 
    text_fg = "white"   
    price_fg = "#00ADB5" 
    button_primary_bg = "#00ADB5" 
    button_secondary_bg = "#5C5C78" 

    frame = tk.Frame(parent, width=220, height=300, bg=card_bg, bd=1, relief="flat") 
    frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
    frame.pack_propagate(False) 

    frame.bind("<Button-1>", lambda e, p=product: show_product_popup(p))

    product_image_path = product.get("main_image", "").replace("\\", "/")
        
    if product_image_path and os.path.exists(product_image_path):
        img = Image.open(product_image_path).resize((140, 140), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        img_label = tk.Label(frame, image=photo, bg=card_bg, cursor="hand2")
        img_label.image = photo 
    else:
        img_label = tk.Label(frame, text="[Không có ảnh]", bg=card_bg, fg=text_fg, 
                                 width=14, height=7, relief="solid", bd=1)

    img_label.pack(pady=(10, 0))
    img_label.bind("<Button-1>", lambda e, p=product: show_product_popup(p)) 

    name_label = tk.Label(frame, text=product["name"], font=("Arial", 11, "bold"), 
                           wraplength=200, bg=card_bg, fg=text_fg, justify="center")
    name_label.pack(pady=(5, 0))
    name_label.bind("<Button-1>", lambda e, p=product: show_product_popup(p)) 

    price_label = tk.Label(frame, text=product["price"], fg=price_fg, 
                            font=("Arial", 13, "bold"), bg=card_bg)
    price_label.pack(pady=(5, 0))
    price_label.bind("<Button-1>", lambda e, p=product: show_product_popup(p)) 

    spacer = tk.Frame(frame, bg=card_bg)
    spacer.pack(expand=True, fill="both")

    button_frame = tk.Frame(frame, bg=card_bg) 
    button_frame.pack(pady=5) 

    view_detail_btn = tk.Button(button_frame, text="Xem chi tiết", font=("Arial", 11, "bold"), width=10, bg=button_primary_bg, fg=text_fg, bd=0, relief="flat", cursor="hand2",
                                 command=lambda p=product: show_product_popup(p))
    view_detail_btn.pack(side="left", padx=2)

    add_to_cart_btn = tk.Button(button_frame, text="Cho vào giỏ", font=("Arial", 11, "bold"), width=10, bg=button_secondary_bg, fg=text_fg, bd=0, relief="flat", cursor="hand2",
                                command=lambda: add_to_cart(product.get("id"))) 
    add_to_cart_btn.pack(side="left", padx=2)

def display_products(product_list):
    for widget in content_frame.winfo_children():
        widget.destroy()

    products_frame_bg = "#232333" 
    
    products_frame = tk.Frame(content_frame, bg=products_frame_bg)
    products_frame.pack(fill="both", expand=True, pady=(0, 20))
    
    global columns 
    if 'columns' not in globals():
        columns = 4 

    page_products = paginate(product_list, current_page) 

    if not page_products:
        tk.Label(products_frame, text="⚠️ Không tìm thấy sản phẩm nào.", font=("Arial", 12), 
                 bg=products_frame_bg, fg="white").pack(pady=20)
    else:
        for idx, product in enumerate(page_products):
            row = idx // columns
            col = idx % columns
            create_product_card(products_frame, product, row, col)
        
        for i in range(columns):
            products_frame.grid_columnconfigure(i, weight=1)
        
        show_pagination(product_list)

def show_pagination(product_list):
    pagination_container_bg = "#232333" 
    button_normal_bg = "#00ADB5"      
    button_active_bg = "#008B9B"      
    button_disabled_bg = "#5C5C78"    
    button_disabled_fg = "#AAAAAA"    
    text_fg = "white"                 

    pagination_container = tk.Frame(content_frame, bg=pagination_container_bg)
    pagination_container.pack(fill="x", pady=(0, 20))
    
    pagination_center = tk.Frame(pagination_container, bg=pagination_container_bg)
    pagination_center.pack()
    
    pagination_frame = tk.Frame(pagination_center, bg=pagination_container_bg, padx=10, pady=5)
    pagination_frame.pack()
    
    prev_btn = tk.Button(pagination_frame, text="⬅ Trước", command=prev_page, bg=button_normal_bg, fg=text_fg, font=("Arial", 10, "bold"), activebackground=button_active_bg, padx=12, pady=6, bd=0, relief="flat", cursor="hand2")
    prev_btn.grid(row=0, column=0, padx=(0, 5))
    
    total_pages = max(1, (len(product_list) - 1) // products_per_page + 1)
    page_label = tk.Label(pagination_frame, text=f"Trang {current_page + 1}/{total_pages}", font=("Arial", 10, "bold"), bg=pagination_container_bg, fg=text_fg, padx=10)
    page_label.grid(row=0, column=1)
    
    next_btn = tk.Button(pagination_frame, text="Tiếp ➡", command=next_page, bg=button_normal_bg, fg=text_fg, font=("Arial", 10, "bold"), activebackground=button_active_bg, padx=12, pady=6, bd=0, relief="flat", cursor="hand2")
    next_btn.grid(row=0, column=2, padx=(5, 0))
    
    prev_state = "normal" if current_page > 0 else "disabled"
    next_state = "normal" if (current_page + 1) * products_per_page < len(product_list) else "disabled"
    
    prev_btn.config(state=prev_state)
    next_btn.config(state=next_state)
    
    if prev_state == "disabled":
        prev_btn.config(bg=button_disabled_bg, fg=button_disabled_fg, cursor="arrow")
    if next_state == "disabled":
        next_btn.config(bg=button_disabled_bg, fg=button_disabled_fg, cursor="arrow")

def update_page():
    global current_page
    display_products(current_product_list)

def next_page():
    global current_page
    if (current_page + 1) * products_per_page < len(current_product_list):
        current_page += 1
        update_page()

def prev_page():
    global current_page
    if current_page > 0:
        current_page -= 1
        update_page()

def search_products():
    global current_product_list, current_page
    keyword = search_entry.get().lower().strip()
    if keyword == SEARCH_PLACEHOLDER.lower():
        current_product_list = all_products.copy()
    else:
        current_product_list = [p for p in all_products if keyword in p["name"].lower()]
    current_page = 0
    update_page()

def filter_by_type(type_id):
    global current_product_list, current_page
    current_product_list = [p for p in all_products if p.get("type_id") == type_id]
    current_page = 0
    update_page()

# ===== HỆ THỐNG TÀI KHOẢN =====
account_file = "account.json"

def get_next_account_id():
    accounts = load_users()
    if not accounts:
        return 1
    return max(account["id"] for account in accounts) + 1

def add_to_cart(product_id):
    global current_user
    
    if not logged_in:
        messagebox.showwarning("Thông báo", "Vui lòng đăng nhập để thêm sản phẩm vào giỏ")
        return
    
    accounts_dict = load_users()
    username = current_user["username"] 
    
    if username in accounts_dict: #
        user_account = accounts_dict[username] 
        
        found_item = False
        for item in user_account.get("cart", []): 
            if item["product_id"] == product_id:
                item["quantity"] += 1
                found_item = True
                break
        
        if not found_item:
            if "cart" not in user_account:
                user_account["cart"] = []
            user_account["cart"].append({
                "product_id": product_id,
                "quantity": 1
            })
            
        save_users(accounts_dict) 
        messagebox.showinfo("Thành công", "Sản phẩm đã được thêm vào giỏ hàng.")
        return
    else:
        messagebox.showerror("Lỗi", "Không tìm thấy thông tin tài khoản người dùng.")

def show_cart():
    if not logged_in:
        messagebox.showwarning("Thông báo", "Vui lòng đăng nhập để xem giỏ hàng")
        return

    cart_window = tk.Toplevel(root)
    cart_window.title("Giỏ Hàng")
    center_window(cart_window, 700, 450) 
    cart_window.resizable(False, False)
    cart_window.configure(bg="#232333") 

    accounts_dict = load_users() 

    cart_items = []
    username = current_user.get("username")
    if username and username in accounts_dict:
    
        user_account = accounts_dict[username] 
        cart_items = user_account.get("cart", [])
    else:
        messagebox.showerror("Lỗi", "Không tìm thấy thông tin tài khoản hiện tại.")
        cart_window.destroy()
        return

    if not cart_items:
        tk.Label(cart_window, text="Giỏ hàng trống", font=("Arial", 14), bg="#232333", fg="white").pack(pady=50)
        return

    cart_frame = tk.Frame(cart_window, bg="#232333")
    cart_frame.pack(fill="both", expand=True, padx=10, pady=10)

    # Tiêu đề các cột
    tk.Label(cart_frame, text="Sản phẩm", font=("Arial", 10, "bold"), bg="#232333", fg="white").grid(row=0, column=0, padx=5, pady=5, sticky="w")
    tk.Label(cart_frame, text="Số lượng", font=("Arial", 10, "bold"), bg="#232333", fg="white").grid(row=0, column=1, padx=5, pady=5)
    tk.Label(cart_frame, text="Thành tiền", font=("Arial", 10, "bold"), bg="#232333", fg="white").grid(row=0, column=2, padx=5, pady=5, sticky="e")
    tk.Label(cart_frame, text="Hành động", font=("Arial", 10, "bold"), bg="#232333", fg="white").grid(row=0, column=3, padx=5, pady=5) # Cột mới

    total = 0
    for idx, item in enumerate(cart_items):
        product = next((p for p in all_products if p["id"] == item["product_id"]), None)
        if not product:
            print(f"Cảnh báo: Sản phẩm ID {item['product_id']} không tìm thấy trong products.json")
            tk.Label(cart_frame, text=f"Sản phẩm ID {item['product_id']} không tồn tại", anchor="w", fg="red", bg="#232333").grid(row=idx+1, column=0, padx=5, pady=5, sticky="w")
            continue

        price = product.get("price", 0)
        try:
            if isinstance(price, str):
                clean_price = ''.join(filter(str.isdigit, price))
                price_value = int(clean_price) if clean_price else 0
            else:
                price_value = price
        except:
            price_value = 0

        item_quantity = item.get("quantity", 0)
        item_total = price_value * item_quantity
        total += item_total

        product_name = product.get("name", product.get("product_name", f"ID {item['product_id']}"))

        # Hiển thị thông tin sản phẩm
        tk.Label(cart_frame, text=product_name, anchor="w", bg="#232333", fg="white").grid(row=idx+1, column=0, padx=5, pady=5, sticky="w")
        tk.Label(cart_frame, text=str(item_quantity), bg="#232333", fg="white").grid(row=idx+1, column=1, padx=5, pady=5)
        tk.Label(cart_frame, text=f"{item_total:,} VNĐ", bg="#232333", fg="#00ADB5").grid(row=idx+1, column=2, padx=5, pady=5, sticky="e")
        
        # Nút Xóa
        tk.Button(cart_frame, text="Xóa",
                  command=lambda p_id=item["product_id"]: remove_from_cart(p_id, cart_window),
                  bg="#FF5733", fg="white", font=("Arial", 9, "bold"), bd=0, relief="flat", cursor="hand2", padx=10, pady=5).grid(row=idx+1, column=3, padx=5, pady=5)

    # Cấu hình các cột để có thể mở rộng
    cart_frame.grid_columnconfigure(0, weight=1) 
    cart_frame.grid_columnconfigure(1, weight=0) 
    cart_frame.grid_columnconfigure(2, weight=0) 
    cart_frame.grid_columnconfigure(3, weight=0) 

    # Tổng cộng
    total_label_frame = tk.Frame(cart_window, bg="#232333")
    total_label_frame.pack(fill="x", pady=5, padx=10)

    tk.Label(total_label_frame, text="Tổng cộng:", font=("Arial", 12, "bold"), bg="#232333", fg="white").pack(side="left", padx=5)
    tk.Label(total_label_frame, text=f"{total:,} VNĐ", font=("Arial", 12, "bold"), bg="#232333", fg="#00ADB5").pack(side="right", padx=5)

    tk.Button(cart_window, text="Thanh toán", bg="#00ADB5", fg="white", font=("Arial", 12, "bold"),
              command=lambda: checkout(cart_window), bd=0, relief="flat", padx=15, pady=8, cursor="hand2").pack(pady=10)


def remove_from_cart(product_id, cart_window_ref):
    global current_user
    if not logged_in or not current_user:
        messagebox.showwarning("Thông báo", "Vui lòng đăng nhập để xóa sản phẩm.")
        return
    accounts_dict = load_users() 
    username = current_user["username"] 
    if username in accounts_dict:
        user_account = accounts_dict[username] 
        
        initial_cart_len = len(user_account.get("cart", []))

        user_account["cart"] = [item for item in user_account.get("cart", []) if item["product_id"] != product_id]
        
        if len(user_account["cart"]) < initial_cart_len:
            save_users(accounts_dict) 
            messagebox.showinfo("Thành công", "Đã xóa sản phẩm khỏi giỏ hàng.")

            if cart_window_ref and cart_window_ref.winfo_exists():
                cart_window_ref.destroy()
            show_cart() 
        else:
            messagebox.showwarning("Thông báo", "Không tìm thấy sản phẩm này trong giỏ hàng.")
    else:
        messagebox.showerror("Lỗi", "Không tìm thấy thông tin tài khoản người dùng.")
    
def load_json_safe(filename, default=None):
    if default is None:
        default = []
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default
    except (json.JSONDecodeError, FileNotFoundError):
        return default
    
def get_next_order_id():
    orders = load_json_safe("orders.json", default=[])
    if not orders:
        return 1
    return max(order["id"] for order in orders) + 1

def checkout(cart_window):
    global current_user
    
    # Lấy thông tin giỏ hàng
    accounts_dict = load_users()
    username = current_user["username"] 

    cart_items = []
    user_account = None

    if username in accounts_dict: 
        user_account = accounts_dict[username] 
        cart_items = user_account.get("cart", []) 
    else:
        messagebox.showerror("Lỗi", "Không tìm thấy thông tin tài khoản người dùng hiện tại.")
        cart_window.destroy()
        return

    if not cart_items:
        messagebox.showwarning("Thông báo", "Giỏ hàng trống. Không thể thanh toán.")
        cart_window.destroy()
        return
    
    # Tính tổng tiền
    total = 0
    for item in cart_items:
        product = next((p for p in all_products if p["id"] == item["product_id"]), None)
        if product:
            try:
                
                if isinstance(product.get("price"), str):
                    clean_price = ''.join(filter(str.isdigit, product["price"]))
                    price_value = int(clean_price) if clean_price else 0
                else:
                    price_value = product["price"]
            except:
                price_value = 0 
            total += price_value * item.get("quantity", 0) 
    
    # Tạo đơn hàng mới
    new_order = {
        "id": get_next_order_id(),
        "customer_name": username, 
        "email": user_account.get("email", "N/A"), 
        "items": cart_items.copy(),
        "total_price": total,
        "status": "pending",
        "order_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    orders = load_json_safe("orders.json", default=[]) #
    orders.append(new_order)
    with open("orders.json", 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)
    
    messagebox.showinfo("Thành công", "Thanh toán thành công! Cảm ơn quý khách.")
    cart_window.destroy()
    
    if user_account: 
        user_account["cart"] = []
        save_users(accounts_dict) 

def show_login_dialog():
    def on_login_success(user_info):
        global logged_in, current_user
        if user_info["type_acc"] in ["admin", "owner"]:
            root.withdraw() 

            import admin

            def return_to_customer():
                global root 
                logout()  
                if root: 
                    root.destroy() 
                init_main_ui()
            
            admin.show_admin_panel(user_info, on_return_callback=return_to_customer)
        else:
            logged_in = True
            current_user = user_info
            update_login_ui()
            messagebox.showinfo("Thành công", f"Chào mừng {user_info['username']}!")

    show_login_window(login_callback=on_login_success)

def logout():
    global logged_in, current_user
    logged_in = False
    current_user = None
    update_login_ui()

def open_admin_panel():
    import admin
    admin.show_admin_panel(current_user)

def update_login_ui():
    global account_frame
    try:
        if not account_frame or not account_frame.winfo_exists():
            return  
    except:
        return

    for widget in account_frame.winfo_children():
        widget.destroy()

    header_bg_color = "#1A1A2E" 
    button_bg_color = "#3C3C58" 
    text_color = "white"

    if logged_in:
        user_frame = tk.Frame(account_frame, bg=header_bg_color)
        user_frame.pack(side="right", padx=5)

        tk.Label(user_frame, text=f"👤 {current_user['username']}", font=("Arial", 12), bg=header_bg_color, fg=text_color).pack(side="left")

        logout_btn = tk.Button(user_frame, text="Đăng xuất", font=("Arial", 12, "bold"), bg=button_bg_color, fg=text_color, command=logout, bd=0, relief="flat", padx=10, pady=5, cursor="hand2")
        logout_btn.pack(side="left", padx=10)
    else:
        btn_frame = tk.Frame(account_frame, bg=header_bg_color)
        btn_frame.pack(side="right", padx=5)

        login_btn = tk.Button(btn_frame, text="Đăng nhập", font=("Arial", 10, "bold"), bg=button_bg_color, fg="white", command=show_login_dialog, bd=0, relief="flat", padx=10, pady=5, cursor="hand2") 
        login_btn.pack(side="left", padx=10)

def toggle_menu():
    global menu_expanded, menu_items_widgets
    if menu_expanded is None:
        return 

    if menu_expanded.get():
        for widget in menu_items_widgets:
            widget.pack_forget()
        menu_expanded.set(False)
    else:
        for widget in menu_items_widgets:
            widget.pack(fill="x", pady=(0, 0)) 
        menu_expanded.set(True)

def on_canvas_configure(event):
    global canvas, scrollable_frame_id
    canvas.configure(scrollregion=canvas.bbox("all"))
    canvas.itemconfig(scrollable_frame_id, width=event.width)

def on_entry_focus_in(event):
    global search_entry, SEARCH_PLACEHOLDER
    if search_entry.get() == SEARCH_PLACEHOLDER:
        search_entry.delete(0, tk.END)
        search_entry.config(fg="white")

def on_entry_focus_out(event):
    global search_entry, SEARCH_PLACEHOLDER
    if not search_entry.get():
        search_entry.insert(0, SEARCH_PLACEHOLDER)
        search_entry.config(fg="#888888")

def click_outside_handler(event):
    global root, search_entry
    if search_entry and search_entry.winfo_exists() and search_entry.focus_get() == search_entry:
        if event.widget != search_entry:
            root.focus_set()

def init_main_ui():
    global root, header_frame, account_frame, content_frame, search_entry
    global canvas, scrollbar, scrollable_frame, scrollable_frame_id
    global menu_expanded, menu_items_widgets, SEARCH_PLACEHOLDER, logo_photo

    root = tk.Tk()
    root.title("Cửa Hàng Mũ Bảo Hiểm")
    center_window(root, 1200, 800)

    # Cấu hình để cửa sổ thay đổi kích thước đúng cách
    root.grid_columnconfigure(1, weight=1)
    root.grid_rowconfigure(1, weight=1)

    # ===== HEADER =====
    header_frame = tk.Frame(root, height=100, bg="#1A1A2E")
    header_frame.pack(side="top", fill="x")

    logo_path = os.path.join("images", "Logo", "Logo2.png")
    logo_width = 230
    logo_height = 95

    if os.path.exists(logo_path):
        logo_img_orig = Image.open(logo_path)
        logo_img_resized = logo_img_orig.resize((logo_width, logo_height), Image.LANCZOS)
        logo_photo = ImageTk.PhotoImage(logo_img_resized)
        logo_label = tk.Label(header_frame, image=logo_photo, bg="#1A1A2E")
        logo_label.image = logo_photo 
        root.logo_photo = logo_photo 
    else:
        logo_label = tk.Label(header_frame, text="🏍️HelmetShop", font=("Arial", 20, "bold"), bg="#1A1A2E", fg="white")
    logo_label.pack(side="left", padx=25, pady=5)

    # Thanh tìm kiếm
    search_frame = tk.Frame(header_frame, bg="#1A1A2E")
    search_frame.pack(side="left", padx=20, expand=True)
    
    search_entry = tk.Entry(search_frame, font=("Arial", 12), width=40,
                            bd=1, relief="flat", bg="#3C3C58", fg="white", insertbackground="white")
    search_entry.pack(side="left", padx=(0, 5))
    search_entry.insert(0, SEARCH_PLACEHOLDER)
    search_entry.config(fg="#888888")
    search_entry.bind("<FocusIn>", on_entry_focus_in)
    search_entry.bind("<FocusOut>", on_entry_focus_out)
    search_entry.bind("<Return>", lambda e: search_products())

    search_button = tk.Button(search_frame, text="Tìm kiếm", font=("Arial", 10, "bold"),
                             bg="#00ADB5", fg="white", command=search_products,
                             bd=0, relief="flat", padx=10, pady=5, cursor="hand2")
    search_button.pack(side="left")

    # Frame cho nút tài khoản và giỏ hàng 
    account_cart_frame = tk.Frame(header_frame, bg="#1A1A2E")
    account_cart_frame.pack(side="right", padx=20, pady=5)

    account_frame = tk.Frame(account_cart_frame, bg="#1A1A2E")
    account_frame.pack(side="left", padx=10)

    cart_button = tk.Button(account_cart_frame, text=" Giỏ hàng", font=("Arial", 10, "bold"),
                            bg="#3C3C58", fg="white", command=show_cart,
                            bd=0, relief="flat", padx=10, pady=5, cursor="hand2")
    cart_button.pack(side="left", padx=10)

    # Cập nhật giao diện đăng nhập ban đầu
    update_login_ui()
    root.bind("<Button-1>", click_outside_handler, add="+")

    # ===== PHẦN CÒN LẠI CỦA GIAO DIỆN =====
    left_frame = tk.Frame(root, width=200, bg="#1A1A2E")
    left_frame.pack(side="left", fill="y", pady=(0, 0))
    menu_expanded = tk.BooleanVar(value=False) 
    menu_items_widgets.clear()

    menu_button = tk.Button(left_frame, text="📂 Danh mục sản phẩm", 
                            bg="#00ADB5", fg="white", 
                            font=("Arial", 12, "bold"), anchor="w", padx=10, pady=12, 
                            bd=0, relief="flat", activebackground="#008B9B", 
                            activeforeground="white", command=toggle_menu, cursor="hand2")
    menu_button.pack(fill="x")

    # Tạo menu theo nhóm loại đã định nghĩa
    for group_name, items in menu_structure.items():
        group_label = tk.Label(left_frame, text=f"📁 {group_name}", bg="#1A1A2E", fg="white", font=("Arial", 11, "bold"), anchor="w", padx=10, pady=8) 
        menu_items_widgets.append(group_label)
        
        for item in items:
            type_id = item["type_id"] 
            btn = tk.Button(left_frame, text=f"   ⮞ {item['name']}", anchor="w", relief="flat", bg="#1A1A2E", fg="white", padx=25, pady=8, font=("Arial", 9), activebackground="#3C3C58", activeforeground="white", bd=0, cursor="hand2", command=lambda tid=type_id: filter_by_type(tid))
            menu_items_widgets.append(btn)
        
    # ===== VÙNG NỘI DUNG CHÍNH (CÓ THANH CUỘN) =====
    right_frame = tk.Frame(root, bg="#232333") 
    right_frame.pack(side="right", fill="both", expand=True, pady=(0, 0))

    # Tạo canvas và thanh cuộn
    canvas = tk.Canvas(right_frame, bg="#232333", highlightthickness=0) 
    scrollbar = tk.Scrollbar(right_frame, orient="vertical", command=canvas.yview, 
                             bg="#3C3C58", troughcolor="#1A1A2E", bd=0, relief="flat") 
    scrollable_frame = tk.Frame(canvas, bg="#232333") 

    scrollable_frame_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    canvas.bind("<Configure>", on_canvas_configure)
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Frame chứa nội dung 
    content_frame = tk.Frame(scrollable_frame, bg="#232333")
    content_frame.pack(fill="both", expand=True)

    scrollable_frame.grid_columnconfigure(0, weight=1)
    content_frame.grid_columnconfigure(0, weight=1)

    # Hiển thị cảnh báo nếu không có sản phẩm
    if not all_products:
        messagebox.showwarning("Cảnh báo", "Không có dữ liệu sản phẩm. Vui lòng kiểm tra file products.json")
        
    update_page() 

    root.mainloop()

if __name__ == "__main__":
    init_main_ui()