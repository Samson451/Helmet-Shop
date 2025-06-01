def show_product_popup(product):
    popup = tk.Toplevel()
    popup.title("Chi Tiết Sản Phẩm")
    popup.geometry("800x550") 
    popup.resizable(False, False)
    popup.configure(bg="white")

    # GẮN DANH SÁCH ẢNH VÀO CỬA SỔ POPUP ĐỂ TRÁNH GARBAGE COLLECTION
    popup.gallery_photos = [] # <-- THÊM DÒNG NÀY (hoặc thay thế gallery_photos = [] nếu đã có)

    # Biến để giữ tham chiếu ảnh chính, tránh bị garbage collection
    main_photo_ref = {"photo": None} 
    main_img_label_ref = {"label": None}

    main_img_size = (300, 300) 

    # Hàm để cập nhật ảnh chính khi click vào thumbnail
    def update_main_image(new_image_path):
        try:
            if os.path.exists(new_image_path):
                new_img = Image.open(new_image_path).resize(main_img_size, Image.LANCZOS)
                new_photo = ImageTk.PhotoImage(new_img)
                
                if main_img_label_ref["label"]:
                    main_img_label_ref["label"].config(image=new_photo)
                    main_photo_ref["photo"] = new_photo # Giữ tham chiếu ảnh chính
            else:
                messagebox.showerror("Lỗi Ảnh", f"Không thể tìm thấy ảnh: {new_image_path}")
        except Exception as e:
            messagebox.showerror("Lỗi Ảnh", f"Lỗi khi tải ảnh: {new_image_path}\n{e}")

    # === HIỂN THỊ ẢNH CHÍNH ===
    product_main_image_path = product.get("main_image", "").replace("\\", "/")
    
    try:
        if product_main_image_path and os.path.exists(product_main_image_path):
            img = Image.open(product_main_image_path).resize(main_img_size, Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            img_label = tk.Label(image_frame, image=photo, bg="white")
            img_label.image = photo # Giữ tham chiếu ảnh cho Label
            main_photo_ref["photo"] = photo 
            main_img_label_ref["label"] = img_label 
        else:
            img_label = tk.Label(image_frame, text="[Không có ảnh]", bg="white", 
                                 width=int(main_img_size[0]/10), height=int(main_img_size[1]/10),
                                 relief="solid", bd=1)
    except Exception as e:
        img_label = tk.Label(image_frame, text=f"[Lỗi tải ảnh: {str(e)}]", bg="white", 
                             width=int(main_img_size[0]/10), height=int(main_img_size[1]/10),
                             relief="solid", bd=1)
    
    img_label.pack(pady=10)

    # === KHUNG CHỨA CÁC HÌNH ẢNH NHỎ (GALLERY THUMBNAILS) ===
    gallery_frame = tk.Frame(image_frame, bg="white") 
    gallery_frame.pack(pady=(0, 10)) 

    thumbnail_size = (80, 80) 
    
    gallery_images = product.get("gallery_images", []) 
    
    max_thumbnails_to_show = 5 
    for i, img_rel_path in enumerate(gallery_images):
        if i >= max_thumbnails_to_show:
            break 

        full_path = img_rel_path.replace("\\", "/") 

        print(f"DEBUG: Kiểm tra ảnh gallery {i+1}: '{full_path}', os.path.exists() trả về: {os.path.exists(full_path)}")

        try:
            if os.path.exists(full_path):
                thumb_img = Image.open(full_path).resize(thumbnail_size, Image.LANCZOS)
                thumb_photo = ImageTk.PhotoImage(thumb_img)
                
                # THAY ĐỔI DÒNG NÀY: Sử dụng popup.gallery_photos
                popup.gallery_photos.append(thumb_photo) # <-- THAY ĐỔI Ở ĐÂY
                
                thumb_label = tk.Label(gallery_frame, image=thumb_photo, bg="white", cursor="hand2", bd=1, relief="solid")
                thumb_label.image = thumb_photo # Giữ thêm một tham chiếu trực tiếp trên label
                
                # Kích hoạt sự kiện click để thay đổi ảnh chính
                thumb_label.bind("<Button-1>", lambda e, p=full_path: update_main_image(p)) 
                
                thumb_label.pack(side="left", padx=2, pady=2)
            else:
                print(f"LỖI (ngoài dự kiến): os.path.exists() trả về False cho: {full_path}")
                tk.Label(gallery_frame, text="[FILE KHÔNG TỒN TẠI]", font=("Arial", 7), bg="#f0f0f0", 
                         width=int(thumbnail_size[0]/10), height=int(thumbnail_size[1]/10), 
                         bd=1, relief="solid").pack(side="left", padx=2, pady=2)
        except Exception as e:
            print(f"LỖI KHI TẢI HOẶC HIỂN THỊ ẢNH GALLERY '{full_path}': {type(e).__name__}: {e}")
            tk.Label(gallery_frame, text=f"[LỖI TẢI: {type(e).__name__}]", font=("Arial", 7), bg="#f0f0f0", 
                     width=int(thumbnail_size[0]/10), height=int(thumbnail_size[1]/10), 
                     bd=1, relief="solid").pack(side="left", padx=2, pady=2)

    # === HIỂN THỊ CHI TIẾT SẢN PHẨM ===
    # ... (phần còn lại của code hiển thị chi tiết sản phẩm và nút bấm, không thay đổi) ...
def show_admin_panel(current_user, on_return_callback=None):
    root = tk.Toplevel()
    app = AdminDashboard(root, current_user, on_return_callback)
    root.mainloop()