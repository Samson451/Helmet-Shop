import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
from Login import center_window
from Data_process import load_users, save_users, load_products, save_products, load_categories, save_categories, load_orders, save_orders
import crawl 
import os 
import threading
import time

# Ánh xạ loại hiển thị cho danh mục sản phẩm
LOAI_HIEN_THI = {
    1: "Nón",
    2: "Phụ kiện",
    3: "Đồ bảo hộ"
}

# Ánh xạ ngược từ tên loại sang ID
REVERSE_LOAI_HIEN_THI = {v: k for k, v in LOAI_HIEN_THI.items()}


class AdminDashboard:
    def __init__(self, root, current_user, on_return_callback=None):
        self.root = root
        self.root.title("Admin Dashboard")
        center_window(root, 1200, 800)
        self.root.iconbitmap("images\Logo\Logo.ico")
        self.current_user = current_user
        self.on_return_callback = on_return_callback
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Cấu hình styles chung cho ứng dụng
        self.style.configure('TFrame', background='#f0f2f5')
        self.style.configure('TLabel', background='#f0f2f5', font=('Arial', 10))
        self.style.configure('TButton', font=('Arial', 10, 'bold'), padding=8, relief='flat')
        self.style.map('TButton', background=[('active', '#007bff'), ('!disabled', '#007bff')], foreground=[('active', 'white'), ('!disabled', 'white')])
        
        self.style.configure('Treeview.Heading', font=('Arial', 11, 'bold'), background='#007bff', foreground='white')
        self.style.configure('Treeview', font=('Arial', 10), rowheight=28, background='white', foreground='black', fieldbackground='white')
        self.style.map('Treeview', background=[('selected', '#347083')])

        self.style.configure('Bold.TLabel', font=('Arial', 18, 'bold'), background='#f0f2f5', foreground='#333333')
        self.style.configure('SmallBold.TLabel', font=('Arial', 13, 'bold'), background='#f0f2f5', foreground='#333333')
        self.style.configure('Stat.TLabel', background='#f0f2f5', foreground='#555555', font=('Arial', 10))

        # Cấu hình Styles cho Sidebar Menu
        self.style.configure('Sidebar.TFrame', background='#2c3e50') 
        self.style.configure('Sidebar.TButton', font=('Segoe UI', 11, 'bold'), foreground='white', background='#2c3e50', relief='flat', anchor='w', padding=[20, 15] 
                             )
        self.style.map('Sidebar.TButton', background=[('active', '#34495e'), ('!disabled', '#2c3e50')], foreground=[('active', '#f39c12'), ('!disabled', 'white')] 
                        )
        
        # Style cho nút sidebar được chọn
        self.style.configure('Sidebar.Selected.TButton', font=('Segoe UI', 11, 'bold'), foreground='#f39c12', background='#34495e', relief='flat', anchor='w', padding=[20, 15]
                             )
        self.style.map('Sidebar.Selected.TButton', background=[('active', '#34495e'), ('!disabled', '#34495e')]
                        )
        
        # Thiết lập bố cục chính 
        self.main_container = ttk.Frame(root, style='TFrame')
        self.main_container.pack(fill='both', expand=True)
        
        self.sidebar_frame = ttk.Frame(self.main_container, width=220, style='Sidebar.TFrame')
        self.sidebar_frame.pack(side='left', fill='y')
        self.sidebar_frame.pack_propagate(False) 

        self.content_frame = ttk.Frame(self.main_container, style='TFrame')
        self.content_frame.pack(side='right', fill='both', expand=True, padx=10, pady=10)

        # Tạo notebook (tab) 
        self.style.layout("TNotebook.Tab", []) 
        self.notebook = ttk.Notebook(self.content_frame)
        self.notebook.pack(fill='both', expand=True)

        # Tạo các frame cho mỗi phần quản lý
        self.dashboard_frame = ttk.Frame(self.notebook, style='TFrame')
        self.account_frame = ttk.Frame(self.notebook, style='TFrame')
        self.category_frame = ttk.Frame(self.notebook, style='TFrame')
        self.product_frame = ttk.Frame(self.notebook, style='TFrame')
        self.order_frame = ttk.Frame(self.notebook, style='TFrame')
        self.crawl_frame = ttk.Frame(self.notebook, style='TFrame') 

        # Thêm các frame vào notebook
        self.notebook.add(self.dashboard_frame, text='') 
        self.notebook.add(self.account_frame, text='')
        self.notebook.add(self.category_frame, text='')
        self.notebook.add(self.product_frame, text='')
        self.notebook.add(self.order_frame, text='')
        self.notebook.add(self.crawl_frame, text='') 

        # Danh sách các nút menu sidebar và tab hiện tại
        self.menu_buttons = {}
        self.current_active_tab = None

        # Khu vực thông tin Admin Panel trong Sidebar
        profile_frame = ttk.Frame(self.sidebar_frame, style='Sidebar.TFrame')
        profile_frame.pack(pady=20, fill='x')
        ttk.Label(profile_frame, text="ADMIN PANEL", font=('Segoe UI', 14, 'bold'),
                  foreground='white', background='#2c3e50').pack(pady=(0, 10))
        ttk.Label(profile_frame, text=f"Welcome, {self.current_user['username']}",
                  font=('Segoe UI', 10), foreground='#f39c12', background='#2c3e50').pack()

        # Thêm các nút điều hướng sidebar 
        self._add_sidebar_button("Tổng quan", 0)
        self._add_sidebar_button("Tài khoản", 1)
        self._add_sidebar_button("Danh mục", 2)
        self._add_sidebar_button("Sản phẩm", 3)
        self._add_sidebar_button("Đơn hàng", 4)
        self._add_sidebar_button("Lấy dữ liệu", 5) 

        # Thanh giãn cách để đẩy nút đăng xuất xuống dưới cùng
        ttk.Frame(self.sidebar_frame, style='Sidebar.TFrame').pack(expand=True, fill='y')

        # Nút Đăng xuất
        logout_btn = ttk.Button(self.sidebar_frame, text=" Đăng xuất",
                                 style='Sidebar.TButton', command=self.logout)
        logout_btn.pack(fill='x', pady=10)

        # Chọn tab đầu tiên khi khởi tạo
        self._on_tab_change(0)

        # Khởi tạo các thành phần giao diện cho từng tab
        self.create_dashboard()
        self.create_account_management()
        self.create_category_management()
        self.create_product_management()
        self.create_order_management()
        self.create_data_crawl()

        self.crawling_thread = None  
        self.progress_update_job = None 

    # === NEW: Data Crawl Tab ===
    def create_data_crawl(self):  
        ttk.Label(self.crawl_frame, text="Chức năng thu thập dữ liệu sản phẩm từ nguồn bên ngoài.",
                  style='TLabel', font=('Arial', 11, 'bold')).pack(pady=20)

        # Progress bar
        self.crawl_progress = ttk.Progressbar(self.crawl_frame, orient="horizontal", length=400, mode="determinate")
        self.crawl_progress.pack(pady=10)

        # Progress label
        self.crawl_status_label = ttk.Label(self.crawl_frame, text="Sẵn sàng để thu thập dữ liệu.", style='TLabel', font=('Arial', 10))
        self.crawl_status_label.pack(pady=5)

        # Start Crawl Button
        self.start_crawl_button = ttk.Button(self.crawl_frame, text="Bắt đầu Lấy dữ liệu", command=self.start_crawl_process, width=25)
        self.start_crawl_button.pack(pady=20)

    def start_crawl_process(self):
        if self.crawling_thread and self.crawling_thread.is_alive():
            messagebox.showwarning("Cảnh báo", "Quá trình thu thập dữ liệu đang chạy.", parent=self.root)
            return

        if not messagebox.askyesno("Xác nhận", "Bạn có chắc chắn muốn bắt đầu thu thập dữ liệu mới? Điều này có thể mất một thời gian và ghi đè dữ liệu sản phẩm và danh mục hiện có.", parent=self.root):
            return

        self.start_crawl_button.config(state=tk.DISABLED)
        self.crawl_progress.config(value=0) # Reset progress
        self.crawl_status_label.config(text="Đang bắt đầu thu thập dữ liệu...")

        self.crawling_thread = threading.Thread(target=self._run_crawl_backend)
        self.crawling_thread.start()
        self._simulate_progress()

    def _run_crawl_backend(self):
        try:
            print("Running crawl.main() in background...")
            crawl.main()
            print("Crawl.main() finished.")
            self.root.after(0, self._crawl_finished, True)
        except Exception as e:
            print(f"Error during crawl: {e}")
            self.root.after(0, self._crawl_finished, False, str(e)) 

    def _simulate_progress(self):
        current_progress = self.crawl_progress['value']
        if self.crawling_thread and self.crawling_thread.is_alive() and current_progress < 99:

            increment = 1 
            new_progress = min(current_progress + increment, 99)
            self.crawl_progress.config(value=new_progress)
            self.crawl_status_label.config(text=f"Đang thu thập dữ liệu... {int(new_progress)}%")
            self.progress_update_job = self.root.after(100, self._simulate_progress)
        elif self.crawling_thread and self.crawling_thread.is_alive() and current_progress >= 99:
            self.crawl_status_label.config(text="Đang hoàn tất quá trình...")
            self.progress_update_job = self.root.after(500, self._simulate_progress) 
       

    def _crawl_finished(self, success, error_message=None):
        if self.progress_update_job:
            self.root.after_cancel(self.progress_update_job) 

        self.crawl_progress.config(value=100)
        self.start_crawl_button.config(state=tk.NORMAL)

        if success:
            self.crawl_status_label.config(text="Thu thập dữ liệu hoàn tất!")
            messagebox.showinfo("Thành công", "Đã thu thập dữ liệu và cập nhật hệ thống.", parent=self.root)

            self.load_initial_data()
            self.refresh_users() 
            self.refresh_products() 
            self.refresh_orders() 
        else:
            self.crawl_status_label.config(text=f"Lỗi: {error_message}")
            messagebox.showerror("Lỗi", f"Lỗi trong quá trình thu thập dữ liệu: {error_message}", parent=self.root)

    def on_closing(self):
        if messagebox.askokcancel("Thoát", "Bạn có muốn thoát chương trình không?"):
            self.root.destroy()

    # Hàm thêm nút sidebar
    def _add_sidebar_button(self, text, tab_index):
        btn = ttk.Button(self.sidebar_frame, text=f" {text}",
                         style='Sidebar.TButton',
                         command=lambda: self._on_tab_change(tab_index))
        btn.pack(fill='x', pady=2)
        self.menu_buttons[tab_index] = btn

    # Hàm xử lý thay đổi tab 
    def _on_tab_change(self, tab_index):
        # Cập nhật styles nút sidebar
        for idx, btn in self.menu_buttons.items():
            if idx == tab_index:
                btn.config(style='Sidebar.Selected.TButton')
            else:
                btn.config(style='Sidebar.TButton')
        
        # Chuyển đổi tab notebook
        self.notebook.select(tab_index)
        self.current_active_tab = tab_index

    # --- Phần quản lý Dashboard  ---
    def create_dashboard(self):
        # Khu vực hiển thị thống kê
        stats_frame = ttk.Frame(self.dashboard_frame, style='TFrame')
        stats_frame.pack(fill='x', padx=20, pady=20)

        user_count = len(self.load_accounts())
        product_count = len(self.load_products())
        category_count = len(self.load_categories())
        order_count = len(self.load_orders())

        stats = [
            ("Tài khoản", user_count, "#4e73df"),  
            ("Sản phẩm", product_count, "#1cc88a"), 
            ("Danh mục", category_count, "#36b9cc"), 
            ("Đơn hàng", order_count, "#f6c23e")    
        ]

        for i, (title, count, color) in enumerate(stats):
            stat_card_frame = ttk.Frame(stats_frame, style='TFrame', relief='raised', borderwidth=1)
            stat_card_frame.grid(row=0, column=i, padx=15, pady=10, sticky='nsew')
            stats_frame.grid_columnconfigure(i, weight=1)

            inner_bg_frame = tk.Frame(stat_card_frame, bg=color, bd=0)
            inner_bg_frame.pack(fill='both', expand=True, ipadx=25, ipady=15)

            ttk.Label(inner_bg_frame, text=title, background=color, foreground='white',
                      font=("Arial", 12, "bold")).pack(pady=(8, 5))
            ttk.Label(inner_bg_frame, text=str(count), background=color, foreground='white',
                      font=("Arial", 32, "bold")).pack(pady=(5, 8))

    # --- Phần quản lý Tài khoản ---
    def create_account_management(self):
        ttk.Label(self.account_frame, text="QUẢN LÝ TÀI KHOẢN",
                  style='Bold.TLabel').pack(pady=15)

        # Khung chứa các nút hành động 
        btn_frame = ttk.Frame(self.account_frame, style='TFrame')
        btn_frame.pack(fill='x', padx=10, pady=10, side='top')

        ttk.Button(btn_frame, text="Làm mới", command=self.refresh_accounts).pack(side='left', padx=8, pady=5)
        ttk.Button(btn_frame, text="Thêm mới", command=self.add_account).pack(side='left', padx=8, pady=5)
        ttk.Button(btn_frame, text="Sửa", command=self.edit_account).pack(side='left', padx=8, pady=5)
        ttk.Button(btn_frame, text="Xóa", command=self.delete_account).pack(side='left', padx=8, pady=5)

        # Bảng hiển thị tài khoản
        columns = ("id", "username", "email", "type_acc")
        self.account_tree = ttk.Treeview(self.account_frame, columns=columns, show="headings")

        self.account_tree.heading("id", text="ID")
        self.account_tree.heading("username", text="Tên đăng nhập")
        self.account_tree.heading("email", text="Email")
        self.account_tree.heading("type_acc", text="Loại tài khoản")

        self.account_tree.column("id", width=60, anchor='center')
        self.account_tree.column("username", width=180)
        self.account_tree.column("email", width=250)
        self.account_tree.column("type_acc", width=160, anchor='center')

        scrollbar = ttk.Scrollbar(self.account_frame, orient="vertical", command=self.account_tree.yview)
        self.account_tree.configure(yscrollcommand=scrollbar.set)

        self.account_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)

        self.refresh_accounts()

    # --- Phần quản lý Danh mục ---
    def create_category_management(self):
        ttk.Label(self.category_frame, text="QUẢN LÝ DANH MỤC SẢN PHẨM",
                  style='Bold.TLabel').pack(pady=15)

        btn_frame = ttk.Frame(self.category_frame, style='TFrame')
        btn_frame.pack(fill='x', padx=10, pady=10, side='top')

        ttk.Button(btn_frame, text="Làm mới", command=self.refresh_categories).pack(side='left', padx=8, pady=5)
        ttk.Button(btn_frame, text="Thêm mới", command=self.add_category).pack(side='left', padx=8, pady=5)
        ttk.Button(btn_frame, text="Sửa", command=self.edit_category).pack(side='left', padx=8, pady=5)
        ttk.Button(btn_frame, text="Xóa", command=self.delete_category).pack(side='left', padx=8, pady=5)

        # Bảng hiển thị danh mục
        columns = ("type_id", "type_name", "loai")
        self.category_tree = ttk.Treeview(self.category_frame, columns=columns, show="headings")

        self.category_tree.heading("type_id", text="ID")
        self.category_tree.heading("type_name", text="Tên danh mục")
        self.category_tree.heading("loai", text="Loại")

        self.category_tree.column("type_id", width=60, anchor='center')
        self.category_tree.column("type_name", width=300)
        self.category_tree.column("loai", width=120, anchor='center')

        scrollbar = ttk.Scrollbar(self.category_frame, orient="vertical", command=self.category_tree.yview)
        self.category_tree.configure(yscrollcommand=scrollbar.set)

        self.category_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)

        self.refresh_categories()

    # --- Phần quản lý Sản phẩm ---
    def create_product_management(self):
        ttk.Label(self.product_frame, text="QUẢN LÝ SẢN PHẨM", style='Bold.TLabel').pack(pady=15)

        # Khung tìm kiếm và lọc 
        filter_actions_frame = ttk.Frame(self.product_frame, style='TFrame')
        filter_actions_frame.pack(fill='x', padx=10, pady=5)

        search_frame = ttk.Frame(filter_actions_frame, style='TFrame')
        search_frame.pack(side='left', padx=5, pady=5) # Đặt khung tìm kiếm bên trái
        ttk.Label(search_frame, text="Tìm kiếm:").pack(side='left', padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side='left', padx=5)
        search_entry.bind('<Return>', self.search_products)
        self.search_var.trace_add("write", lambda *args: self.search_products())

        category_filter_frame = ttk.Frame(filter_actions_frame, style='TFrame')
        category_filter_frame.pack(side='left', padx=20, pady=5)
        ttk.Label(category_filter_frame, text="Lọc theo danh mục:").pack(side='left', padx=5)
        self.category_filter_var = tk.StringVar(value="Tất cả")
        categories_for_filter = ["Tất cả"] + [cat["type_name"] for cat in self.load_categories()]
        self.category_filter_combobox = ttk.Combobox(category_filter_frame, textvariable=self.category_filter_var,
                                                values=categories_for_filter, state="readonly", width=20)
        self.category_filter_combobox.pack(side='left', padx=5)
        self.category_filter_combobox.bind("<<ComboboxSelected>>", lambda e: self.filter_products_by_category())
        
        ttk.Button(filter_actions_frame, text="Hiển thị tất cả", command=self.reset_product_search).pack(side='left', padx=10, pady=5)

        # Khung nút hành động 
        btn_frame = ttk.Frame(self.product_frame, style='TFrame')
        btn_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(btn_frame, text="Làm mới", command=self.refresh_products).pack(side='left', padx=8, pady=5)
        ttk.Button(btn_frame, text="Thêm mới", command=self.add_product).pack(side='left', padx=8, pady=5)
        ttk.Button(btn_frame, text="Sửa", command=self.edit_product).pack(side='left', padx=8, pady=5)
        ttk.Button(btn_frame, text="Xóa", command=self.delete_product).pack(side='left', padx=8, pady=5)

        # Bảng hiển thị sản phẩm
        columns = ("id", "product_name", "price", "category")
        self.product_tree = ttk.Treeview(self.product_frame, columns=columns, show="headings")
        self.product_tree.heading("id", text="ID")
        self.product_tree.heading("product_name", text="Tên sản phẩm")
        self.product_tree.heading("price", text="Giá")
        self.product_tree.heading("category", text="Danh mục")

        self.product_tree.column("id", width=60, anchor='center')
        self.product_tree.column("product_name", width=300)
        self.product_tree.column("price", width=180)
        self.product_tree.column("category", width=180)

        scrollbar = ttk.Scrollbar(self.product_frame, orient="vertical", command=self.product_tree.yview)
        self.product_tree.configure(yscrollcommand=scrollbar.set)

        self.product_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)

        self.current_product_list = None
        self.refresh_products()

    def search_products(self, event=None):
        keyword = self.search_var.get().lower().strip()
        all_products = self.load_products()

        if not keyword:
            self.current_product_list = None
            self.refresh_products()
            return

        # Tìm kiếm theo tên sản phẩm hoặc ID
        self.current_product_list = [
            p for p in all_products
            if keyword in p.get("product_name", "").lower() or
               str(p.get("id", "")).lower() == keyword
        ]
        self.refresh_products(self.current_product_list)

    def filter_products_by_category(self):
        selected_category = self.category_filter_var.get()
        if selected_category == "Tất cả":
            self.reset_product_search()
            return

        all_products = self.load_products()
        categories = self.load_categories()

        category_id = None
        for cat in categories:
            if cat["type_name"] == selected_category:
                category_id = cat["type_id"]
                break

        if not category_id:
            self.current_product_list = [] 
            self.refresh_products(self.current_product_list)
            return

        self.current_product_list = [
            p for p in all_products
            if p.get("type_id") == category_id
        ]
        self.refresh_products(self.current_product_list)

    def reset_product_search(self):
        self.search_var.set("")
        self.category_filter_var.set("Tất cả")
        self.current_product_list = None
        self.refresh_products()

    # --- Phần quản lý Đơn hàng ---
    def create_order_management(self):
        ttk.Label(self.order_frame, text="QUẢN LÝ ĐƠN HÀNG",
                  style='Bold.TLabel').pack(pady=15)

        btn_frame = ttk.Frame(self.order_frame, style='TFrame')
        btn_frame.pack(fill='x', padx=10, pady=10, side='top')

        ttk.Button(btn_frame, text="Làm mới", command=self.refresh_orders).pack(side='left', padx=8, pady=5)
        ttk.Button(btn_frame, text="Xem chi tiết", command=self.view_order_details).pack(side='left', padx=8, pady=5)
        ttk.Button(btn_frame, text="Cập nhật TT", command=self.update_order_status).pack(side='left', padx=8, pady=5)

        # Bảng hiển thị đơn hàng
        columns = ("id", "customer_name", "email", "total_price", "status")
        self.order_tree = ttk.Treeview(self.order_frame, columns=columns, show="headings")

        self.order_tree.heading("id", text="Mã ĐH")
        self.order_tree.heading("customer_name", text="Khách hàng")
        self.order_tree.heading("email", text="Email")
        self.order_tree.heading("total_price", text="Tổng tiền")
        self.order_tree.heading("status", text="Trạng thái")

        self.order_tree.column("id", width=80, anchor='center')
        self.order_tree.column("customer_name", width=180)
        self.order_tree.column("email", width=250)
        self.order_tree.column("total_price", width=150, anchor='e')
        self.order_tree.column("status", width=130, anchor='center')

        scrollbar = ttk.Scrollbar(self.order_frame, orient="vertical", command=self.order_tree.yview)
        self.order_tree.configure(yscrollcommand=scrollbar.set)

        self.order_tree.pack(side='left', fill='both', expand=True, padx=10, pady=10)
        scrollbar.pack(side='right', fill='y', pady=10)

        self.refresh_orders()

    # ===== HÀM XỬ LÝ DỮ LIỆU =====
    def load_accounts(self):
        return list(load_users().values())

    def save_accounts(self, accounts):
        save_users({acc["username"]: acc for acc in accounts})

    def load_categories(self):
        return load_categories()

    def save_categories(self, categories):
        save_categories(categories)

    def load_products(self):
        return load_products()

    def save_products(self, products):
        save_products(products)

    def load_orders(self):
        return load_orders()

    def save_orders(self, orders):
        save_orders(orders)

    # ===== HÀM LÀM MỚI DỮ LIỆU TRÊN CÁC BẢNG =====
    def refresh_accounts(self):
        for item in self.account_tree.get_children():
            self.account_tree.delete(item)

        accounts = self.load_accounts()
        for acc in accounts:
            self.account_tree.insert("", "end", values=(
                acc["id"],
                acc["username"],
                acc["email"],
                acc["type_acc"]
            ))

    def refresh_categories(self):
        for item in self.category_tree.get_children():
            self.category_tree.delete(item)
        categories = load_categories()
        for cat in categories:
            loai_str = LOAI_HIEN_THI.get(cat["loai"], "Không rõ")
            self.category_tree.insert("", "end", values=(
                cat["type_id"],
                cat["type_name"],
                loai_str
            ))
        # Cập nhật bộ lọc danh mục cho phần quản lý sản phẩm
        categories_for_filter = ["Tất cả"] + [cat["type_name"] for cat in self.load_categories()]
        if hasattr(self, 'category_filter_combobox'):
             self.category_filter_combobox['values'] = categories_for_filter


    def refresh_products(self, product_list=None):
        for item in self.product_tree.get_children():
            self.product_tree.delete(item)

        if product_list is None:
            products = self.load_products()
        else:
            products = product_list

        categories = {str(cat["type_id"]): cat["type_name"] for cat in self.load_categories()}

        for prod in products:
            price = prod.get("price", "0")
            if isinstance(price, str):
                clean_price = ''.join(filter(str.isdigit, price))
                price_value = int(clean_price) if clean_price else 0
            else:
                price_value = price

            category_name = categories.get(str(prod.get("type_id", 0)), "Không xác định")

            self.product_tree.insert("", "end", values=(
                prod["id"],
                prod["product_name"],
                f"{price_value:,} VND",
                category_name
            ))


    def refresh_orders(self):
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)

        orders = self.load_orders()
        for order in orders:
            self.order_tree.insert("", "end", values=(
                order["id"],
                order["customer_name"],
                order["email"],
                f"{order['total_price']:,} VND",
                order["status"]
        ))

    # ===== HÀM QUẢN LÝ TÀI KHOẢN =====
    def add_account(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Thêm tài khoản mới")
        add_window.geometry("450x320")
        center_window(add_window, 450, 320)
        add_window.iconbitmap("images\Logo\Logo.ico")
        add_window.transient(self.root)
        add_window.grab_set()

        main_frame = ttk.Frame(add_window, padding="20", style='TFrame')
        main_frame.pack(fill='both', expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="Thông tin tài khoản", padding="15", style='TFrame')
        input_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(input_frame, text="Tên đăng nhập:", style='TLabel').grid(row=0, column=0, padx=10, pady=8, sticky='w')
        username_entry = ttk.Entry(input_frame, width=35)
        username_entry.grid(row=0, column=1, padx=10, pady=8, sticky='ew')

        ttk.Label(input_frame, text="Mật khẩu:", style='TLabel').grid(row=1, column=0, padx=10, pady=8, sticky='w')
        password_entry = ttk.Entry(input_frame, width=35, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=8, sticky='ew')

        ttk.Label(input_frame, text="Email:", style='TLabel').grid(row=2, column=0, padx=10, pady=8, sticky='w')
        email_entry = ttk.Entry(input_frame, width=35)
        email_entry.grid(row=2, column=1, padx=10, pady=8, sticky='ew')

        ttk.Label(input_frame, text="Loại tài khoản:", style='TLabel').grid(row=3, column=0, padx=10, pady=8, sticky='w')
        type_var = tk.StringVar(value="customer")
        type_combobox = ttk.Combobox(input_frame, textvariable=type_var,
                                    values=["admin", "customer"], state="readonly", width=32)
        type_combobox.grid(row=3, column=1, padx=10, pady=8, sticky='w')

        input_frame.grid_columnconfigure(1, weight=1)

        def save_account():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            email = email_entry.get().strip()
            type_acc = type_var.get()

            if not username or not password or not email:
                messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin", parent=add_window)
                return

            accounts = self.load_accounts()

            if any(acc["username"] == username for acc in accounts):
                messagebox.showerror("Lỗi", "Tên đăng nhập đã tồn tại", parent=add_window)
                return

            new_id = max(acc["id"] for acc in accounts) + 1 if accounts else 1

            new_account = {
                "id": new_id,
                "username": username,
                "password": password,
                "email": email,
                "cart": [],
                "type_acc": type_acc
            }

            accounts.append(new_account)
            self.save_accounts(accounts)
            messagebox.showinfo("Thành công", "Thêm tài khoản thành công", parent=add_window)
            add_window.destroy()
            self.refresh_accounts()

        ttk.Button(main_frame, text="Lưu tài khoản", width=20, command=save_account
                ).pack(pady=20, anchor='center')

    def edit_account(self):
        selected = self.account_tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một tài khoản để sửa")
            return

        item = self.account_tree.item(selected[0])
        account_id = item["values"][0]

        accounts = self.load_accounts()
        account = next((acc for acc in accounts if acc["id"] == account_id), None)

        if not account:
            messagebox.showerror("Lỗi", "Không tìm thấy tài khoản")
            return

        edit_window = tk.Toplevel(self.root)
        edit_window.title("Chỉnh sửa tài khoản")
        edit_window.geometry("450x320")
        center_window(edit_window, 450, 320)
        edit_window.iconbitmap("images\Logo\Logo.ico")
        edit_window.transient(self.root)
        edit_window.grab_set()

        main_frame = ttk.Frame(edit_window, padding="20", style='TFrame')
        main_frame.pack(fill='both', expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="Thông tin tài khoản", padding="15", style='TFrame')
        input_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(input_frame, text="Tên đăng nhập:", style='TLabel').grid(row=0, column=0, padx=10, pady=8, sticky='w')
        username_entry = ttk.Entry(input_frame, width=35)
        username_entry.insert(0, account["username"])
        username_entry.config(state='disabled')
        username_entry.grid(row=0, column=1, padx=10, pady=8, sticky='ew')

        ttk.Label(input_frame, text="Mật khẩu:", style='TLabel').grid(row=1, column=0, padx=10, pady=8, sticky='w')
        password_entry = ttk.Entry(input_frame, width=35, show="*")
        password_entry.insert(0, account["password"])
        password_entry.grid(row=1, column=1, padx=10, pady=8, sticky='ew')

        ttk.Label(input_frame, text="Email:", style='TLabel').grid(row=2, column=0, padx=10, pady=8, sticky='w')
        email_entry = ttk.Entry(input_frame, width=35)
        email_entry.insert(0, account["email"])
        email_entry.grid(row=2, column=1, padx=10, pady=8, sticky='ew')

        ttk.Label(input_frame, text="Loại tài khoản:", style='TLabel').grid(row=3, column=0, padx=10, pady=8, sticky='w')
        type_var = tk.StringVar(value=account["type_acc"])
        type_combobox = ttk.Combobox(input_frame, textvariable=type_var,
                                    values=["admin", "customer"], state="readonly", width=32)
        type_combobox.grid(row=3, column=1, padx=10, pady=8, sticky='w')

        input_frame.grid_columnconfigure(1, weight=1)

        def update_account():
            account["password"] = password_entry.get().strip()
            account["email"] = email_entry.get().strip()
            account["type_acc"] = type_var.get()

            self.save_accounts(accounts)
            messagebox.showinfo("Thành công", "Cập nhật tài khoản thành công", parent=edit_window)
            edit_window.destroy()
            self.refresh_accounts()

        ttk.Button(main_frame, text="Lưu thay đổi", width=20, command=update_account
                ).pack(pady=20, anchor='center')

    def delete_account(self):
        selected = self.account_tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một tài khoản để xóa")
            return

        item = self.account_tree.item(selected[0])
        account_id = item["values"][0]
        username = item["values"][1]

        if username == self.current_user["username"]:
            messagebox.showwarning("Cảnh báo", "Bạn không thể xóa tài khoản của chính mình!")
            return

        if not messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa tài khoản '{username}'?"):
            return

        accounts = self.load_accounts()
        accounts = [acc for acc in accounts if acc["id"] != account_id]

        self.save_accounts(accounts)
        messagebox.showinfo("Thành công", "Đã xóa tài khoản")
        self.refresh_accounts()

    # ===== HÀM QUẢN LÝ DANH MỤC =====
    def add_category(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Thêm danh mục mới")
        add_window.geometry("450x280")
        center_window(add_window, 450, 280)
        add_window.iconbitmap("images\Logo\Logo.ico")
        add_window.transient(self.root)
        add_window.grab_set()

        main_frame = ttk.Frame(add_window, padding="20", style='TFrame')
        main_frame.pack(fill='both', expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="Thông tin danh mục", padding="15", style='TFrame')
        input_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(input_frame, text="Tên danh mục:", style='TLabel').grid(row=0, column=0, padx=10, pady=8, sticky='w')
        name_entry = ttk.Entry(input_frame, width=35)
        name_entry.grid(row=0, column=1, padx=10, pady=8, sticky='ew')

        ttk.Label(input_frame, text="Loại:", style='TLabel').grid(row=1, column=0, padx=10, pady=8, sticky='w')
        type_var = tk.StringVar(value=LOAI_HIEN_THI.get(1)) 
        type_combobox = ttk.Combobox(input_frame, textvariable=type_var, values=list(LOAI_HIEN_THI.values()), state="readonly", width=32)
        type_combobox.grid(row=1, column=1, padx=10, pady=8, sticky='w')

        input_frame.grid_columnconfigure(1, weight=1)

        def save_category():
            name = name_entry.get().strip()
            selected_loai_name = type_var.get()
            
            loai_id = REVERSE_LOAI_HIEN_THI.get(selected_loai_name)

            if not name:
                messagebox.showerror("Lỗi", "Vui lòng nhập tên danh mục", parent=add_window)
                return
            if loai_id is None:
                messagebox.showerror("Lỗi", "Vui lòng chọn loại danh mục hợp lệ", parent=add_window)
                return


            categories = self.load_categories()

            if any(cat["type_name"] == name for cat in categories):
                messagebox.showerror("Lỗi", "Tên danh mục đã tồn tại", parent=add_window)
                return

            new_id = max(cat["type_id"] for cat in categories) + 1 if categories else 1

            new_category = {
                "type_id": new_id,
                "type_name": name,
                "loai": loai_id
            }

            categories.append(new_category)
            self.save_categories(categories)
            messagebox.showinfo("Thành công", "Thêm danh mục thành công", parent=add_window)
            add_window.destroy()
            self.refresh_categories()
            self.refresh_products()

        ttk.Button(main_frame, text="Lưu danh mục", width=20, command=save_category
                ).pack(pady=20, anchor='center')

    def edit_category(self):
        selected = self.category_tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một danh mục để sửa")
            return

        item = self.category_tree.item(selected[0])
        category_id = item["values"][0]

        categories = self.load_categories()
        category = next((cat for cat in categories if cat["type_id"] == category_id), None)

        if not category:
            messagebox.showerror("Lỗi", "Không tìm thấy danh mục")
            return

        edit_window = tk.Toplevel(self.root)
        edit_window.title("Chỉnh sửa danh mục")
        edit_window.geometry("450x280")
        center_window(edit_window, 450, 280)
        edit_window.iconbitmap("images\Logo\Logo.ico")
        edit_window.transient(self.root)
        edit_window.grab_set()

        main_frame = ttk.Frame(edit_window, padding="20", style='TFrame')
        main_frame.pack(fill='both', expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="Thông tin danh mục", padding="15", style='TFrame')
        input_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(input_frame, text="Tên danh mục:", style='TLabel').grid(row=0, column=0, padx=10, pady=8, sticky='w')
        name_entry = ttk.Entry(input_frame, width=35)
        name_entry.insert(0, category["type_name"])
        name_entry.grid(row=0, column=1, padx=10, pady=8, sticky='ew')

        ttk.Label(input_frame, text="Loại:", style='TLabel').grid(row=1, column=0, padx=10, pady=8, sticky='w')
        current_loai_name = LOAI_HIEN_THI.get(category["loai"], "Không rõ")
        type_var = tk.StringVar(value=current_loai_name)
        type_combobox = ttk.Combobox(input_frame, textvariable=type_var, values=list(LOAI_HIEN_THI.values()), state="readonly", width=32)
        type_combobox.grid(row=1, column=1, padx=10, pady=8, sticky='w')
        
        input_frame.grid_columnconfigure(1, weight=1)

        def update_category():
            category_name_updated = name_entry.get().strip()
            selected_loai_name = type_var.get()
            
            loai_id_updated = REVERSE_LOAI_HIEN_THI.get(selected_loai_name)

            if loai_id_updated is None:
                messagebox.showerror("Lỗi", "Vui lòng chọn loại danh mục hợp lệ", parent=edit_window)
                return

            category["type_name"] = category_name_updated
            category["loai"] = loai_id_updated 

            self.save_categories(categories)
            messagebox.showinfo("Thành công", "Cập nhật danh mục thành công", parent=edit_window)
            edit_window.destroy()
            self.refresh_categories()
            self.refresh_products() 

        ttk.Button(main_frame, text="Lưu thay đổi", width=20, command=update_category
                ).pack(pady=20, anchor='center')

    def delete_category(self):
        selected = self.category_tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một danh mục để xóa")
            return

        item = self.category_tree.item(selected[0])
        category_id = item["values"][0]
        category_name = item["values"][1]

        products = self.load_products()
        if any(prod.get("type_id") == category_id for prod in products):
            messagebox.showwarning("Cảnh báo", "Không thể xóa danh mục đang có sản phẩm!")
            return

        if not messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa danh mục '{category_name}'?"):
            return

        categories = self.load_categories()
        categories = [cat for cat in categories if cat["type_id"] != category_id]

        self.save_categories(categories)
        messagebox.showinfo("Thành công", "Đã xóa danh mục")
        self.refresh_categories()
        self.refresh_products() 

    # ===== HÀM QUẢN LÝ SẢN PHẨM =====
    def add_product(self):
        add_window = tk.Toplevel(self.root)
        add_window.title("Thêm sản phẩm mới")
        add_window.geometry("550x500") 
        center_window(add_window, 550, 500)
        add_window.iconbitmap("images\Logo\Logo.ico")
        add_window.transient(self.root)
        add_window.grab_set()

        main_frame = ttk.Frame(add_window, padding="20", style='TFrame')
        main_frame.pack(fill='both', expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="Thông tin sản phẩm", padding="15", style='TFrame')
        input_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(input_frame, text="Tên sản phẩm:", style='TLabel').grid(row=0, column=0, padx=10, pady=8, sticky='w')
        name_entry = ttk.Entry(input_frame, width=40)
        name_entry.grid(row=0, column=1, padx=10, pady=8, sticky='ew')

        ttk.Label(input_frame, text="Giá:", style='TLabel').grid(row=1, column=0, padx=10, pady=8, sticky='w')
        price_entry = ttk.Entry(input_frame, width=40)
        price_entry.grid(row=1, column=1, padx=10, pady=8, sticky='ew')

        ttk.Label(input_frame, text="Mô tả:", style='TLabel').grid(row=2, column=0, padx=10, pady=8, sticky='nw')
        desc_text = tk.Text(input_frame, width=40, height=5, font=('Arial', 10))
        desc_text.grid(row=2, column=1, padx=10, pady=8, sticky='ew')

        ttk.Label(input_frame, text="Danh mục:", style='TLabel').grid(row=3, column=0, padx=10, pady=8, sticky='w')

        categories = self.load_categories()
        category_names = [cat["type_name"] for cat in categories]
        
        category_var = tk.StringVar()
        category_combobox = ttk.Combobox(input_frame, textvariable=category_var,
                                        values=category_names, state="readonly", width=37)
        if category_names:
            category_combobox.set(category_names[0])
        category_combobox.grid(row=3, column=1, padx=10, pady=8, sticky='w')

        # Chọn ảnh chính
        ttk.Label(input_frame, text="Ảnh chính:", style='TLabel').grid(row=4, column=0, padx=10, pady=8, sticky='w')
        
        main_image_selection_frame = ttk.Frame(input_frame, style='TFrame')
        main_image_selection_frame.grid(row=4, column=1, padx=10, pady=8, sticky='ew')
        
        self.selected_main_image_path = tk.StringVar() 
        main_image_status_label = ttk.Label(main_image_selection_frame, textvariable=self.selected_main_image_path, style='TLabel', foreground='gray')
        main_image_status_label.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        def select_main_image():
            file_path = filedialog.askopenfilename(
                title="Chọn ảnh chính",
                filetypes=(("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*"))
            )
            if file_path:
                self.selected_main_image_path.set("1 ảnh đã chọn")
                self.current_main_image_path = file_path 
            else:
                self.selected_main_image_path.set("Chưa có ảnh nào")
                self.current_main_image_path = ""

        select_main_image_btn = ttk.Button(main_image_selection_frame, text="Chọn ảnh", command=select_main_image)
        select_main_image_btn.pack(side='right')
        
        self.selected_main_image_path.set("Chưa có ảnh nào")
        self.current_main_image_path = "" 

        # Chọn ảnh Gallery
        ttk.Label(input_frame, text="Ảnh Gallery:", style='TLabel').grid(row=5, column=0, padx=10, pady=8, sticky='w')
        
        gallery_selection_frame = ttk.Frame(input_frame, style='TFrame')
        gallery_selection_frame.grid(row=5, column=1, padx=10, pady=8, sticky='ew')
        
        self.selected_gallery_image_count = tk.StringVar() 
        gallery_status_label = ttk.Label(gallery_selection_frame, textvariable=self.selected_gallery_image_count, style='TLabel', foreground='gray')
        gallery_status_label.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        self.current_gallery_image_paths = [] 

        def select_gallery_images():
            file_paths = filedialog.askopenfilenames( 
                title="Chọn ảnh Gallery",
                filetypes=(("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*"))
            )
            if file_paths:
                self.current_gallery_image_paths = list(file_paths) 
                self.selected_gallery_image_count.set(f"{len(file_paths)} ảnh đã chọn")
            else:
                self.selected_gallery_image_count.set("Chưa có ảnh nào")
                self.current_gallery_image_paths = [] 
        
        select_gallery_btn = ttk.Button(gallery_selection_frame, text="Chọn ảnh", command=select_gallery_images)
        select_gallery_btn.pack(side='right')

        self.selected_gallery_image_count.set("Chưa có ảnh nào")
        self.current_gallery_image_paths = [] 

        input_frame.grid_columnconfigure(1, weight=1)

        def save_product():
            name = name_entry.get().strip()
            price = price_entry.get().strip()
            desc = desc_text.get("1.0", "end-1c").strip()
            category_name = category_var.get()
            main_image_path = self.current_main_image_path 
            gallery_image_paths = self.current_gallery_image_paths 

            if not name or not price:
                messagebox.showerror("Lỗi", "Vui lòng nhập tên sản phẩm và giá", parent=add_window)
                return

            category_id = None
            for cat in categories:
                if cat["type_name"] == category_name:
                    category_id = cat["type_id"]
                    break

            if not category_id:
                messagebox.showerror("Lỗi", "Vui lòng chọn danh mục", parent=add_window)
                return

            products = self.load_products()

            new_id = max(prod["id"] for prod in products) + 1 if products else 1

            new_product = {
                "id": new_id,
                "product_name": name,
                "price": price,
                "description": desc,
                "type_id": category_id,
                "main_image": main_image_path,
                "gallery_images": gallery_image_paths 
            }

            products.append(new_product)
            self.save_products(products)
            messagebox.showinfo("Thành công", "Thêm sản phẩm thành công", parent=add_window)
            add_window.destroy()
            self.refresh_products()
        ttk.Button(main_frame, text="Lưu sản phẩm", width=20, command=save_product).pack(pady=20, anchor='center')

    def edit_product(self):
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một sản phẩm để sửa")
            return

        item = self.product_tree.item(selected[0])
        product_id = item["values"][0]

        products = self.load_products()
        product = next((prod for prod in products if prod["id"] == product_id), None)

        if not product:
            messagebox.showerror("Lỗi", "Không tìm thấy sản phẩm")
            return

        edit_window = tk.Toplevel(self.root)
        edit_window.title("Chỉnh sửa sản phẩm")
        edit_window.geometry("550x500") 
        center_window(edit_window, 550, 500)
        edit_window.iconbitmap("images\Logo\Logo.ico")
        edit_window.transient(self.root)
        edit_window.grab_set()

        main_frame = ttk.Frame(edit_window, padding="20", style='TFrame')
        main_frame.pack(fill='both', expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="Thông tin sản phẩm", padding="15", style='TFrame')
        input_frame.pack(fill='x', padx=10, pady=10)

        ttk.Label(input_frame, text="Tên sản phẩm:", style='TLabel').grid(row=0, column=0, padx=10, pady=8, sticky='w')
        name_entry = ttk.Entry(input_frame, width=40)
        name_entry.insert(0, product["product_name"])
        name_entry.grid(row=0, column=1, padx=10, pady=8, sticky='ew')

        ttk.Label(input_frame, text="Giá:", style='TLabel').grid(row=1, column=0, padx=10, pady=8, sticky='w')
        price_entry = ttk.Entry(input_frame, width=40)
        price_entry.insert(0, product["price"])
        price_entry.grid(row=1, column=1, padx=10, pady=8, sticky='ew')

        ttk.Label(input_frame, text="Mô tả:", style='TLabel').grid(row=2, column=0, padx=10, pady=8, sticky='nw')
        desc_text = tk.Text(input_frame, width=40, height=5, font=('Arial', 10))
        desc_text.insert("1.0", product["description"])
        desc_text.grid(row=2, column=1, padx=10, pady=8, sticky='ew')

        ttk.Label(input_frame, text="Danh mục:", style='TLabel').grid(row=3, column=0, padx=10, pady=8, sticky='w')

        categories = self.load_categories()
        category_names = [cat["type_name"] for cat in categories]

        current_category = next((cat for cat in categories if cat["type_id"] == product.get("type_id", 0)), None)
        current_category_name = current_category["type_name"] if current_category else ""

        category_var = tk.StringVar(value=current_category_name)
        category_combobox = ttk.Combobox(input_frame, textvariable=category_var,
                                        values=category_names, state="readonly", width=37)
        category_combobox.grid(row=3, column=1, padx=10, pady=8, sticky='w')

        # Chọn ảnh chính
        ttk.Label(input_frame, text="Ảnh chính:", style='TLabel').grid(row=4, column=0, padx=10, pady=8, sticky='w')
        
        main_image_selection_frame = ttk.Frame(input_frame, style='TFrame')
        main_image_selection_frame.grid(row=4, column=1, padx=10, pady=8, sticky='ew')
        
        self.selected_main_image_path = tk.StringVar() 
        main_image_status_label = ttk.Label(main_image_selection_frame, textvariable=self.selected_main_image_path, style='TLabel', foreground='gray')
        main_image_status_label.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        self.current_main_image_path = product.get("main_image", "") 
        if self.current_main_image_path:
            self.selected_main_image_path.set("1 ảnh đã chọn")
        else:
            self.selected_main_image_path.set("Chưa có ảnh nào")

        def select_main_image():
            file_path = filedialog.askopenfilename(
                title="Chọn ảnh chính",
                filetypes=(("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*"))
            )
            if file_path:
                self.selected_main_image_path.set("1 ảnh đã chọn")
                self.current_main_image_path = file_path 
            else:
                if not self.current_main_image_path: 
                     self.selected_main_image_path.set("Chưa có ảnh nào")

        select_main_image_btn = ttk.Button(main_image_selection_frame, text="Chọn ảnh", command=select_main_image)
        select_main_image_btn.pack(side='right')

        # Chọn ảnh Gallery
        ttk.Label(input_frame, text="Ảnh Gallery:", style='TLabel').grid(row=5, column=0, padx=10, pady=8, sticky='w')
        
        gallery_selection_frame = ttk.Frame(input_frame, style='TFrame')
        gallery_selection_frame.grid(row=5, column=1, padx=10, pady=8, sticky='ew')
        
        self.selected_gallery_image_count = tk.StringVar() 
        gallery_status_label = ttk.Label(gallery_selection_frame, textvariable=self.selected_gallery_image_count, style='TLabel', foreground='gray')
        gallery_status_label.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        self.current_gallery_image_paths = product.get("gallery_images", []) 
        if self.current_gallery_image_paths:
            self.selected_gallery_image_count.set(f"{len(self.current_gallery_image_paths)} ảnh đã chọn")
        else:
            self.selected_gallery_image_count.set("Chưa có ảnh nào")

        def select_gallery_images():
            file_paths = filedialog.askopenfilenames( 
                title="Chọn ảnh Gallery",
                filetypes=(("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*"))
            )
            if file_paths:
                self.current_gallery_image_paths = list(file_paths) 
                self.selected_gallery_image_count.set(f"{len(file_paths)} ảnh đã chọn")
            else:
                if not self.current_gallery_image_paths: 
                    self.selected_gallery_image_count.set("Chưa có ảnh nào")

        select_gallery_btn = ttk.Button(gallery_selection_frame, text="Chọn ảnh", command=select_gallery_images)
        select_gallery_btn.pack(side='right')

        input_frame.grid_columnconfigure(1, weight=1)

        def update_product():
            category_id = None
            for cat in categories:
                if cat["type_name"] == category_var.get():
                    category_id = cat["type_id"]
                    break

            if not category_id:
                messagebox.showerror("Lỗi", "Vui lòng chọn danh mục", parent=edit_window)
                return

            product["product_name"] = name_entry.get().strip()
            product["price"] = price_entry.get().strip()
            product["description"] = desc_text.get("1.0", "end-1c").strip()
            product["type_id"] = category_id
            product["main_image"] = self.current_main_image_path 
            product["gallery_images"] = self.current_gallery_image_paths 

            self.save_products(products)
            messagebox.showinfo("Thành công", "Cập nhật sản phẩm thành công", parent=edit_window)
            edit_window.destroy()
            self.refresh_products()

        ttk.Button(main_frame, text="Lưu thay đổi", width=20, command=update_product
                ).pack(pady=20, anchor='center')

    def delete_product(self):
        selected = self.product_tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một sản phẩm để xóa")
            return

        item = self.product_tree.item(selected[0])
        product_id = item["values"][0]
        product_name = item["values"][1]

        if not messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa sản phẩm '{product_name}'?"):
            return

        products = self.load_products()
        products = [prod for prod in products if prod["id"] != product_id]

        self.save_products(products)
        messagebox.showinfo("Thành công", "Đã xóa sản phẩm")
        self.refresh_products()

    # ===== HÀM QUẢN LÝ ĐƠN HÀNG =====
    def view_order_details(self):
        selected = self.order_tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một đơn hàng")
            return

        item = self.order_tree.item(selected[0])
        order_id = item["values"][0]

        orders = self.load_orders()
        order = next((ord for ord in orders if ord["id"] == order_id), None)

        if not order:
            messagebox.showerror("Lỗi", "Không tìm thấy đơn hàng")
            return

        detail_window = tk.Toplevel(self.root)
        detail_window.title(f"Chi tiết đơn hàng #{order_id}")
        detail_window.geometry("700x550")
        center_window(detail_window, 700, 550)
        detail_window.iconbitmap("images\Logo\Logo.ico")
        detail_window.transient(self.root)
        detail_window.grab_set()

        main_frame = ttk.Frame(detail_window, padding="20", style='TFrame')
        main_frame.pack(fill='both', expand=True)

        # Thông tin chung về đơn hàng
        info_frame = ttk.LabelFrame(main_frame, text="Thông tin đơn hàng", padding="15", style='TFrame')
        info_frame.pack(fill='x', padx=10, pady=10)

        # Sử dụng grid để căn chỉnh tốt hơn
        ttk.Label(info_frame, text="Mã đơn hàng:", style='TLabel').grid(row=0, column=0, sticky='w', padx=5, pady=5)
        ttk.Label(info_frame, text=order['id'], font=("Arial", 10, "bold")).grid(row=0, column=1, sticky='w', padx=5, pady=5)

        ttk.Label(info_frame, text="Khách hàng:", style='TLabel').grid(row=0, column=2, sticky='w', padx=5, pady=5)
        ttk.Label(info_frame, text=order['customer_name'], font=("Arial", 10, "bold")).grid(row=0, column=3, sticky='w', padx=5, pady=5)
        
        ttk.Label(info_frame, text="Email:", style='TLabel').grid(row=1, column=0, sticky='w', padx=5, pady=5)
        ttk.Label(info_frame, text=order['email'], font=("Arial", 10, "bold")).grid(row=1, column=1, columnspan=3, sticky='w', padx=5, pady=5)

        ttk.Label(info_frame, text="Tổng tiền:", style='TLabel').grid(row=2, column=0, sticky='w', padx=5, pady=5)
        ttk.Label(info_frame, text=f"{order['total_price']:,} VND", font=("Arial", 10, "bold"), foreground='green').grid(row=2, column=1, sticky='w', padx=5, pady=5)
        
        ttk.Label(info_frame, text="Trạng thái:", style='TLabel').grid(row=2, column=2, sticky='w', padx=5, pady=5)
        ttk.Label(info_frame, text=order['status'], font=("Arial", 10, "bold"), foreground='blue').grid(row=2, column=3, sticky='w', padx=5, pady=5)

        info_frame.grid_columnconfigure(1, weight=1)
        info_frame.grid_columnconfigure(3, weight=1)

        # Danh sách sản phẩm trong đơn hàng
        products_frame = ttk.LabelFrame(main_frame, text="Sản phẩm đã đặt", padding="15", style='TFrame')
        products_frame.pack(fill='both', expand=True, padx=10, pady=10)

        columns = ("product_id", "product_name", "quantity", "price", "total")
        product_tree = ttk.Treeview(products_frame, columns=columns, show="headings")

        product_tree.heading("product_id", text="ID SP")
        product_tree.heading("product_name", text="Tên sản phẩm")
        product_tree.heading("quantity", text="Số lượng")
        product_tree.heading("price", text="Đơn giá")
        product_tree.heading("total", text="Thành tiền")

        product_tree.column("product_id", width=70, anchor='center')
        product_tree.column("product_name", width=220)
        product_tree.column("quantity", width=90, anchor='center')
        product_tree.column("price", width=120, anchor='e')
        product_tree.column("total", width=120, anchor='e')

        scrollbar = ttk.Scrollbar(products_frame, orient="vertical", command=product_tree.yview)
        product_tree.configure(yscrollcommand=scrollbar.set)

        product_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        all_products = self.load_products()
        product_map = {prod["id"]: prod for prod in all_products}

        for item in order["items"]:
            product_id = item["product_id"]
            product = product_map.get(product_id)

            if product:
                price = product["price"]
                if isinstance(price, str):
                    clean_price = ''.join(filter(str.isdigit, price))
                    price_value = int(clean_price) if clean_price else 0
                else:
                    price_value = price

                total = price_value * item["quantity"]

                product_tree.insert("", "end", values=(
                    product_id,
                    product["product_name"],
                    item["quantity"],
                    f"{price_value:,} VND",
                    f"{total:,} VND"
                ))

    def update_order_status(self):
        selected = self.order_tree.selection()
        if not selected:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một đơn hàng")
            return

        item = self.order_tree.item(selected[0])
        order_id = item["values"][0]

        orders = self.load_orders()
        order = next((ord for ord in orders if ord["id"] == order_id), None)

        if not order:
            messagebox.showerror("Lỗi", "Không tìm thấy đơn hàng")
            return

        status_window = tk.Toplevel(self.root)
        status_window.title("Cập nhật trạng thái đơn hàng")
        status_window.geometry("350x220")
        center_window(status_window, 350, 220)
        status_window.iconbitmap("images\Logo\Logo.ico")
        status_window.transient(self.root)
        status_window.grab_set()

        main_frame = ttk.Frame(status_window, padding="20", style='TFrame')
        main_frame.pack(fill='both', expand=True)

        ttk.Label(main_frame, text="Chọn trạng thái mới:", style='TLabel', font=('Arial', 11, 'bold')).pack(pady=15)

        status_var = tk.StringVar(value=order["status"])
        status_options = ttk.Combobox(main_frame, textvariable=status_var,
                                    values=["pending", "processing", "shipped", "delivered", "cancelled"],
                                    state="readonly", width=25)
        status_options.pack(pady=10)

        def save_status():
            order["status"] = status_var.get()
            save_orders(self.orders)
            messagebox.showinfo("Thành công", "Đã cập nhật trạng thái đơn hàng", parent=status_window)
            status_window.destroy()
            self.refresh_orders()

        ttk.Button(main_frame, text="Lưu thay đổi", command=save_status, width=18).pack(pady=20)

    # Hàm đăng xuất
    def logout(self):
        if self.on_return_callback:
            self.on_return_callback()
        self.root.destroy()

# Hàm hiển thị bảng điều khiển admin
def show_admin_panel(current_user, on_return_callback=None):
    root = tk.Toplevel()
    app = AdminDashboard(root, current_user, on_return_callback)
    root.mainloop()