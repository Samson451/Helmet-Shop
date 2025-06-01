import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import json
import time
import re
import os
from pathlib import Path

# Cấu hình
BASE_URL = "https://bikersaigon.net"
DELAY = 1.5  # Thời gian chờ giữa các request (giây)
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
IMAGE_ROOT = "images" 
MAX_RETRIES = 3

def get_soup(url, retry=0):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        if retry < MAX_RETRIES:
            print(f"⚠️ Thử lại ({retry+1}/{MAX_RETRIES}) cho {url}")
            time.sleep(DELAY * 2)
            return get_soup(url, retry + 1)
        print(f"⚠️ Không thể lấy {url} sau {MAX_RETRIES} lần thử: {str(e)}")
        return None

def scrape_menu():
    print("🔍 Đang thu thập danh mục chính sản phẩm...")
    soup = get_soup(BASE_URL)
    if not soup:
        return []

    # Tìm mega_menu bằng id
    mega_menu = soup.find('ul', id='mega_menu')
    if not mega_menu:
        print("⚠️ Không tìm thấy mega menu!")
        return []

    categories = []
    seen_urls = set()

    # Chỉ lấy các li trực tiếp trong mega_menu
    for li in mega_menu.find_all('li', recursive=False):
        # Tìm thẻ a đầu tiên trong li
        link = li.find('a', href=True)
        if not link:
            continue
            
        href = link.get('href')
        if not href or href == '#' or href.startswith('javascript:'):
            continue
            
        # Lấy tên danh mục từ span có class menu-image-title hoặc menu-image-title-after
        name_span = link.find('span', class_=['menu-image-title', 'menu-image-title-after'])
        if name_span:
            category_name = name_span.get_text(strip=True)
        else:
            # Nếu không có span, lấy text trực tiếp từ thẻ a
            category_name = link.get_text(strip=True)
            # Làm sạch tên
            category_name = re.sub(r'\s+', ' ', category_name).strip()
            
        # Bỏ qua nếu không có tên
        if not category_name:
            continue
            
        # Tạo URL tuyệt đối
        category_url = urljoin(BASE_URL, href)
        
        # Kiểm tra URL hợp lệ và chưa tồn tại
        if category_url not in seen_urls:
            seen_urls.add(category_url)
            categories.append({
                "type_name": category_name,
                "url": category_url,
                "type_id": len(categories) + 1
            })
            print(f"✅ Phát hiện danh mục chính: {category_name}")

    return categories

def get_total_pages(soup):
    """Xác định tổng số trang từ phân trang"""
    pagination = soup.select_one('.page-numbers.nav-pagination')
    if not pagination:
        return 1
    
    # Tìm tất cả các trang
    page_links = pagination.find_all('a', class_='page-number')
    max_page = 1
    
    for link in page_links:
        try:
            page_num = int(link.text)
            if page_num > max_page:
                max_page = page_num
        except ValueError:
            pass
    
    # Kiểm tra trang cuối
    last_page_link = pagination.find('a', class_='next')
    if last_page_link and 'href' in last_page_link.attrs:
        last_url = last_page_link['href']
        if '/page/' in last_url:
            try:
                page_num = int(last_url.split('/page/')[1].split('/')[0])
                if page_num > max_page:
                    max_page = page_num
            except:
                pass
    
    return max_page

def scrape_category(category, crawled_urls):
    """Thu thập sản phẩm từ một danh mục, kiểm tra trùng lặp"""
    print(f"\n📂 Đang xử lý danh mục: {category['type_name']}")
    products = []
    page = 1
    total_pages = 1
    
    while True:
        # Tạo URL phân trang
        if page > 1:
            page_url = f"{category['url']}page/{page}/"
        else:
            page_url = category['url']
        
        print(f"📄 Trang {page}: {page_url}")
        
        soup = get_soup(page_url)
        if not soup:
            print("⚠️ Không thể tải trang, bỏ qua")
            break
        
        # Lấy tổng số trang (chỉ lần đầu)
        if page == 1:
            total_pages = get_total_pages(soup)
            print(f"ℹ️ Tổng số trang: {total_pages}")
        
        # Tìm sản phẩm
        product_items = soup.select('div.product-small')
        if not product_items:
            print("ℹ️ Không tìm thấy sản phẩm trên trang này")
            break
        
        for item in product_items:
            try:
                product_link = item.find('a', class_='woocommerce-LoopProduct-link')
                if not product_link or not product_link.get('href'):
                    continue
                    
                product_url = urljoin(page_url, product_link['href'])
                
                # Kiểm tra nếu sản phẩm đã được crawl
                if product_url in crawled_urls:
                    print(f"⏩ Bỏ qua sản phẩm đã thu thập: {product_url}")
                    continue
                    
                # Đánh dấu URL đã crawl
                crawled_urls.add(product_url)
                
                time.sleep(DELAY)
                product_id = len(products) + 1 
                product_data = scrape_product(product_url, category, product_id)
                if product_data:
                    products.append(product_data)
                    print(f"🛒 Đã thu thập: {product_data['product_name']}")
            except Exception as e:
                print(f"⚠️ Lỗi khi xử lý sản phẩm: {str(e)}")
        
        # Kiểm tra nếu đã hết trang
        if page >= total_pages:
            break
            
        page += 1
        time.sleep(DELAY)
    
    print(f"✅ Hoàn thành danh mục: {len(products)} sản phẩm")
    return products

def scrape_product(product_url, category):
    """Thu thập chi tiết sản phẩm"""
    soup = get_soup(product_url)
    if not soup:
        return None

    # Lấy tên sản phẩm
    name_tag = soup.find('h1', class_='product-title')
    if not name_tag:
        return None
    product_name = name_tag.get_text(strip=True)
    
    # Lấy giá
    price_tag = soup.find('p', class_='price')
    price = price_tag.get_text(strip=True) if price_tag else "Liên hệ"
    
    # Lấy mô tả
    desc_tag = soup.find('div', class_='product-short-description')
    description = desc_tag.get_text(strip=True) if desc_tag else ""
    
    # Lấy ảnh chính
    main_img_tag = soup.select_one('div.product-images img')
    main_img_url = ""
    if main_img_tag:
        main_img_url = main_img_tag.get('data-src') or main_img_tag.get('src')
        if main_img_url and main_img_url.startswith('//'):
            main_img_url = 'https:' + main_img_url
    
    # Tạo thư mục lưu ảnh (trong thư mục "images")
    safe_name = re.sub(r'[\\/*?:"<>|]', '', product_name).strip()
    product_dir = Path(IMAGE_ROOT) / safe_name
    product_dir.mkdir(parents=True, exist_ok=True)
    
    # Tải ảnh chính
    main_img_path = ""
    if main_img_url and not main_img_url.startswith('data:'):
        try:
            # Xác định phần mở rộng của ảnh
            img_ext = os.path.splitext(main_img_url)[1]
            if not img_ext or len(img_ext) > 5:  # Nếu không có hoặc phần mở rộng quá dài
                img_ext = ".jpg"
                
            img_name = "main" + img_ext
            img_path = product_dir / img_name
            response = requests.get(main_img_url, headers=HEADERS, stream=True, timeout=10)
            if response.status_code == 200:
                with open(img_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                # SỬA: Sử dụng dấu \ và thêm "images\" vào đường dẫn
                main_img_path = f"images\\{safe_name}\\{img_name}"
        except Exception as e:
            print(f"⚠️ Không tải được ảnh chính: {e}")
    
    # Lấy ảnh gallery
    gallery_images = []
    gallery = soup.find('div', class_='product-thumbnails')
    if gallery:
        for i, img in enumerate(gallery.find_all('img'), 1):
            img_url = img.get('data-src') or img.get('src')
            if img_url and not img_url.startswith('data:'):
                if img_url.startswith('//'):
                    img_url = 'https:' + img_url
                try:
                    # Xác định phần mở rộng của ảnh
                    img_ext = os.path.splitext(img_url)[1]
                    if not img_ext or len(img_ext) > 5:  # Nếu không có hoặc phần mở rộng quá dài
                        img_ext = ".jpg"
                        
                    img_name = f"gallery_{i}{img_ext}"
                    img_path = product_dir / img_name
                    response = requests.get(img_url, headers=HEADERS, stream=True, timeout=10)
                    if response.status_code == 200:
                        with open(img_path, 'wb') as f:
                            for chunk in response.iter_content(1024):
                                f.write(chunk)
                        # SỬA: Sử dụng dấu \ và thêm "images\" vào đường dẫn
                        gallery_images.append(f"images\\{safe_name}\\{img_name}")
                except Exception as e:
                    print(f"⚠️ Không tải được ảnh gallery: {e}")
    
    return {
        "type_id": category['type_id'],
        "type_name": category['type_name'],
        "product_name": product_name,
        "price": price,
        "description": description,
        "main_image": main_img_path,
        "gallery_images": gallery_images,
        "product_url": product_url
    }

def save_data(data, filename):
    """Lưu dữ liệu vào file JSON"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã lưu {len(data)} mục vào {filename}")
    except Exception as e:
        print(f"⚠️ Lỗi khi lưu file {filename}: {str(e)}")

def main():
    start_time = time.time()
    
    # Tạo thư mục hình ảnh
    Path(IMAGE_ROOT).mkdir(exist_ok=True)
    
    # Bước 1: Thu thập danh mục chính
    categories = scrape_menu()
    
    # Tạo danh sách chỉ chứa id và tên để lưu vào JSON
    categories_for_json = [
        {"type_id": cat["type_id"], "type_name": cat["type_name"]} 
        for cat in categories
    ]
    save_data(categories_for_json, "product_types.json")
    
    if not categories:
        print("❌ Không tìm thấy danh mục sản phẩm!")
        return
    
    # Bước 2: Thu thập sản phẩm từng danh mục
    all_products = []
    crawled_urls = set()  # Tập hợp lưu các URL sản phẩm đã crawl
    
    for category in categories:
        products = scrape_category(category, crawled_urls)
        all_products.extend(products)
        save_data(all_products, "products.json")  # Lưu tạm sau mỗi danh mục
    
    # Bước 3: Lưu kết quả cuối cùng
    save_data(all_products, "products.json")
    
    # Thống kê
    total_time = (time.time() - start_time) / 60
    print(f"\n✅ Hoàn thành trong {total_time:.2f} phút")
    print(f"📊 Tổng số danh mục chính: {len(categories)}")
    print(f"🛍️ Tổng số sản phẩm: {len(all_products)}")
    print(f"📁 Thư mục ảnh: {IMAGE_ROOT}")

if __name__ == "__main__":
    main()