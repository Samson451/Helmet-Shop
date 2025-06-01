import tkinter as tk
from tkinter import messagebox
from Reg import show_register_window
from Data_process import load_users
from Helper import center_window

def show_login_window(login_callback=None):
    bg_dark = "#1A1A2E"
    frame_bg = "#232333"
    card_bg = "#3C3C58"
    text_fg = "white"
    primary_btn_bg = "#00ADB5"
    secondary_btn_bg = "#5C5C78"

    def login():
        username = entry_username.get()
        password = entry_password.get()
        users = load_users()
        
        if username in users:
            if users[username]["password"] == password:
                label_result.config(text="Đăng nhập thành công!", fg="green")
                root.destroy()
                return {
                    "id": users[username]["id"],
                    "username": username,
                    "email": users[username]["email"],
                    "cart": users[username]["cart"],
                    "type_acc": users[username]["type_acc"]
                }
            else:
                label_result.config(text="Mật khẩu không đúng!", fg="red")
        else:
            label_result.config(text="Tên người dùng không tồn tại!", fg="red")
        return None

    def on_login_click():
        user_info = login()
        if user_info and login_callback:
            login_callback(user_info)

    def open_register():
        root.destroy()
        show_register_window(login_callback)

    root = tk.Tk()
    root.title("Đăng Nhập")
    root.config(bg=bg_dark)
    center_window(root, 300, 260)

    frame = tk.Frame(root, bg=frame_bg, bd=1, relief="flat")
    frame.pack(expand=True, padx=20, pady=20)

    tk.Label(frame, text="Tên đăng nhập:", bg=frame_bg, fg=text_fg, font=("Arial", 10)).grid(row=0, column=0, padx=10, pady=10, sticky="e")
    entry_username = tk.Entry(frame, bg=card_bg, fg=text_fg, insertbackground=text_fg, font=("Arial", 10))
    entry_username.grid(row=0, column=1, padx=10, pady=10, sticky="w")

    tk.Label(frame, text="Mật khẩu:", bg=frame_bg, fg=text_fg, font=("Arial", 10)).grid(row=1, column=0, padx=10, pady=10, sticky="e")
    entry_password = tk.Entry(frame, show="*", bg=card_bg, fg=text_fg, insertbackground=text_fg, font=("Arial", 10))
    entry_password.grid(row=1, column=1, padx=10, pady=10, sticky="w")

    # Nút Đăng Nhập
    btn_login = tk.Button(frame, text="Đăng Nhập", width=20, command=on_login_click,
                         bg=primary_btn_bg, fg=text_fg, font=("Arial", 10, "bold"),
                         bd=0, relief="flat", cursor="hand2", padx=10, pady=5)
    btn_login.grid(row=2, column=0, columnspan=2, pady=10)

    label_result = tk.Label(frame, text="", justify='center', bg=frame_bg, font=("Arial", 10))
    label_result.grid(row=3, column=0, columnspan=2)

    # Nút Đăng Ký
    btn_register = tk.Button(frame, text="Đăng Ký", width=20, command=open_register,
                            bg=secondary_btn_bg, fg=text_fg, font=("Arial", 10, "bold"),
                            bd=0, relief="flat", cursor="hand2", padx=10, pady=5)
    btn_register.grid(row=4, column=0, columnspan=2, pady=5)
    
    root.mainloop()

