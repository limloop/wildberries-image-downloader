import os
import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor

def parse_wb_input(user_input):
    # Проверяем, является ли ввод артикулом (только цифры)
    if user_input.isdigit():
        return user_input
    
    # Пытаемся извлечь артикул из URL Wildberries
    match = re.search(r'catalog/(\d+)/', user_input)
    if match:
        return match.group(1)
    
    # Если не удалось распознать ни артикул, ни ссылку
    raise ValueError("Некорректный ввод. Введите артикул или ссылку на Wildberries.")

def get_wb_product_images(article_id, max_images=50, server_range=range(16, 0, -1)):
    images = []
    
    for server_id in server_range:
        server = f"{server_id:02d}"  # Форматируем в двузначный номер (01, 02, ...)
        server_found = False
        
        for img_id in range(1, max_images + 1):
            url = (
                f"https://basket-{server}.wbbasket.ru/"
                f"vol{article_id[:4]}/part{article_id[:6]}/{article_id}/"
                f"images/big/{img_id}.webp"
            )
            
            response = requests.head(url)  # Проверяем существование изображения
            if response.status_code == 200:
                images.append(url)
                server_found = True  # Помечаем, что сервер рабочий
            else:
                break
        
        # Если нашли рабочий сервер, прекращаем поиск других серверов
        if server_found:
            break
    
    return images

def download_wb_product_images(article_id, image_urls):
    # Создаем папку images/{article_id}, если её нет
    save_dir = f"images/{article_id}"
    os.makedirs(save_dir, exist_ok=True)

    def download_image(url, img_id):
        try:
            response = requests.get(url, stream=True, timeout=10)
            response.raise_for_status()  # Проверяем успешность запроса

            # Сохраняем изображение
            image_path = f"{save_dir}/{img_id}.webp"
            with open(image_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception as e:
            print(f"Ошибка при загрузке {url}: {e}")
            return False

    # Загружаем изображения
    def download_task(args):
        url, i = args
        is_downloaded = False
        download_count = 1
        
        while not is_downloaded:
            is_downloaded = download_image(url, i)
            
            download_count += 1
            if download_count == 4:
                print(f"Скачивание изображения пропущено ({url})")
                break

            if not is_downloaded:
                print(f"Повторяю попытку ({download_count}/3) для изображения {i}")
                time.sleep(3)

    # Создаем пул потоков
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(download_task, [(url, i) for i, url in enumerate(image_urls)])

    print(f"Все изображения сохранены в {save_dir}/")


def main():
    user_input = input("Введите артикул или ссылку на товар Wildberries: ")
    try:
        article_id = parse_wb_input(user_input)
    except ValueError as e:
        print(e)

    image_urls = get_wb_product_images(article_id)
    download_wb_product_images(article_id, image_urls)

if __name__ == '__main__':
    main()