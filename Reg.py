import tkinter as tk
from tkinter import messagebox
from Data_process import load_users, save_users
from Helper import center_window

def show_register_window(login_callback=None):
    bg_dark = "#1A1A2E"
    frame_bg = "#232333"
    card_bg = "#3C3C58"
    text_fg = "white"
    primary_btn_bg = "#00ADB5"
    secondary_btn_bg = "#5C5C78"

    def register():
        username = entry_username.get()
        password = entry_password.get()
        confirm = entry_confirm.get()
        email = entry_email.get()

        if not username or not password or not email or not confirm:
            messagebox.showerror("Lỗi", "Vui lòng điền đầy đủ tất cả các trường.")
            return
            
        if password != confirm:
            messagebox.showerror("Lỗi", "Mật khẩu xác nhận không khớp.")
            return

        users = load_users()
        
        if username in users:
            messagebox.showerror("Lỗi", "Tên người dùng đã tồn tại.")
        else:
            max_id = max(acc["id"] for acc in users.values()) if users else 0
            
            users[username] = {
                "id": max_id + 1,
                "username": username,
                "password": password,
                "email": email,
                "cart": [],
                "type_acc": "customer"
            }
            
            save_users(users)
            messagebox.showinfo("Thành công", "Đăng ký thành công!")
            
            register_root.destroy()
            
            if login_callback:
                login_callback({
                    "id": max_id + 1,
                    "username": username,
                    "email": email,
                    "cart": [],
                    "type_acc": "customer"
                })

    def back_to_login():
        register_root.destroy()
        import Login
        Login.show_login_window(login_callback)

    register_root = tk.Tk()
    register_root.title("Đăng Ký")
    register_root.config(bg=bg_dark)
    center_window(register_root, 300, 350)

    frame = tk.Frame(register_root, bg=frame_bg, bd=1, relief="flat")
    frame.pack(expand=True, padx=20, pady=20)

    tk.Label(frame, text="Tên đăng nhập:", bg=frame_bg, fg=text_fg, font=("Arial", 10)).grid(row=0, column=0, padx=10, pady=5, sticky="e")
    entry_username = tk.Entry(frame, bg=card_bg, fg=text_fg, insertbackground=text_fg, font=("Arial", 10))
    entry_username.grid(row=0, column=1, padx=10, pady=5, sticky="w")

    tk.Label(frame, text="Mật khẩu:", bg=frame_bg, fg=text_fg, font=("Arial", 10)).grid(row=1, column=0, padx=10, pady=5, sticky="e")
    entry_password = tk.Entry(frame, show="*", bg=card_bg, fg=text_fg, insertbackground=text_fg, font=("Arial", 10))
    entry_password.grid(row=1, column=1, padx=10, pady=5, sticky="w")

    tk.Label(frame, text="Xác nhận MK:", bg=frame_bg, fg=text_fg, font=("Arial", 10)).grid(row=2, column=0, padx=10, pady=5, sticky="e")
    entry_confirm = tk.Entry(frame, show="*", bg=card_bg, fg=text_fg, insertbackground=text_fg, font=("Arial", 10))
    entry_confirm.grid(row=2, column=1, padx=10, pady=5, sticky="w")

    tk.Label(frame, text="Email:", bg=frame_bg, fg=text_fg, font=("Arial", 10)).grid(row=3, column=0, padx=10, pady=5, sticky="e")
    entry_email = tk.Entry(frame, bg=card_bg, fg=text_fg, insertbackground=text_fg, font=("Arial", 10))
    entry_email.grid(row=3, column=1, padx=10, pady=5, sticky="w")

    # Nút Đăng Ký
    btn_register = tk.Button(frame, text="Đăng Ký", width=20, command=register,
                            bg=primary_btn_bg, fg=text_fg, font=("Arial", 10, "bold"),
                            bd=0, relief="flat", cursor="hand2", padx=10, pady=5)
    btn_register.grid(row=4, column=0, columnspan=2, pady=10)

    # Nút Quay lại Đăng Nhập
    btn_back = tk.Button(frame, text="Quay lại Đăng Nhập", width=20, command=back_to_login,
                        bg=secondary_btn_bg, fg=text_fg, font=("Arial", 10, "bold"),
                        bd=0, relief="flat", cursor="hand2", padx=10, pady=5)
    btn_back.grid(row=5, column=0, columnspan=2, pady=5)

    register_root.mainloop()