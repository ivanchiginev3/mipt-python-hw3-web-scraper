"""
Парсер для сайта books.toscrape.com.

Этот модуль предоставляет функции для сбора данных о книгах с сайта Books to Scrape.
"""

import re
import time
import json

import requests
import schedule
from bs4 import BeautifulSoup
from tqdm import tqdm


def get_book_data(book_url: str) -> dict:
    """
    Извлекает данные о книге с сайта Books to Scrape.
    
    Парсит информацию о книге включая название, рейтинг, цену, наличие и другие характеристики из таблицы продукта.
    
    Args:
        book_url (str): URL страницы книги на сайте books.toscrape.com
        
    Returns:
        dict: Словарь с данными о книге в формате:
            {
                'name': 'Название книги',
                'rating': '5',  # от 1 до 5
                'Price': '£51.77',
                'Availability': '22',
                'UPC': 'a897fe39b1053632',
                ...
            }
        None: в случае ошибки запроса или парсинга
        
    Raises:
        requests.RequestException: при ошибках сетевого запроса
        Exception: при ошибках парсинга HTML
    """
    try:
        # HTTP-запрос и базовая валидация
        response = requests.get(book_url, timeout=10)
        response.encoding = 'utf-8'
        response.raise_for_status()
        
        # Инициализация парсера и словаря
        soup = BeautifulSoup(response.text, "html.parser")
        item = {}
        
        # Парсинг названия книги
        product_main = soup.find("div", class_="col-sm-6 product_main")
        if product_main:
            h1_element = product_main.find("h1")
            if h1_element:
                item['name'] = h1_element.get_text(strip=True)
            else:
                item['name'] = "Название не найдено"
        else:
            item['name'] = "Блок продукта не найден"
        
        # Парсинг рейтинга
        rating_element = soup.find('p', class_='star-rating')
        if rating_element:
            classes_str = ' '.join(rating_element.get('class', []))
            rating_match = re.findall(r'One|Two|Three|Four|Five', classes_str)
            if rating_match:
                rating_map = {'One': '1', 'Two': '2', 'Three': '3', 'Four': '4', 'Five': '5'}
                item['rating'] = rating_map.get(rating_match[0], 'Unknown')
            else:
                item['rating'] = "Рейтинг не распознан"
        else:
            item['rating'] = "Элемент рейтинга не найден"
        
        # Табличные данные
        table = soup.find('table', class_='table table-striped')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                headers = [x.get_text(' ', strip=True) for x in row.find_all('th')]
                values = [x.get_text(' ', strip=True) for x in row.find_all('td')]
                
                if headers and values:
                    key = headers[0]
                    value = values[0]
                    item[key] = value
            
            # Обработка числа книг в наличии
            if "Availability" in item:
                numbers = re.findall(r'\d+', item["Availability"])
                item["Availability"] = numbers[0] if numbers else "0"
        else:
            print("Таблица не найдена")
     
        return item
       
    except requests.RequestException as e:
        print(f"Ошибка запроса: {e}")
        return None
    
    except Exception as e: 
        print(f"Ошибка парсинга: {e}")
        return None
    
    
def scrape_books(save_to_file: bool = False) -> list:
    """
    Парсит все книги с сайта Books to Scrape.
    
    Args:
        save_to_file: Если True, сохраняет данные в JSON файл
        
    Returns:
        List[dict]: Список словарей с данными о книгах
    """
    start_time = time.time()
    all_books_data = []
    page_number = 1
    
    while True:
        try:
            url = f'http://books.toscrape.com/catalogue/page-{page_number}.html'
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            if response.status_code == 404:
                break
                
            soup = BeautifulSoup(response.text, "html.parser")
            books = soup.find_all('article', class_='product_pod')
            all_books_href = []
            
            for book in books:
                all_books_href.append(book.find('h3').find('a')['href'])
                
            for href in tqdm(all_books_href, desc=f"Страница {page_number}", leave=False):
                try:
                    books_url = f'http://books.toscrape.com/catalogue/{href}'
                    book_data = get_book_data(books_url)
                    if book_data:
                        all_books_data.append(book_data)
                except Exception as e:  # pylint: disable=broad-exception-caught
                    print(f"Ошибка парсинга книги {href}: {e}")
                    continue
                    
            page_number += 1
            
        except requests.HTTPError as e:
            if e.response.status_code == 404:
                break
            print(f"HTTP ошибка на странице {page_number}: {e}")
            page_number += 1
        except requests.RequestException as e:
            print(f"Ошибка запроса страницы {page_number}: {e}")
            page_number += 1
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Ошибка на странице {page_number}: {e}")
            page_number += 1
    
    total_time = time.time() - start_time
    minutes = int(total_time // 60)
    seconds = int(total_time % 60)
    
    print(f"Общее время: {minutes} мин {seconds} сек")
            
    if save_to_file:
        try:
            with open("books_data.json", "w", encoding='utf-8') as f:
                json.dump(all_books_data, f, indent=2, ensure_ascii=False)
            print("Данные сохранены в books_data.json")
        except Exception as e:  # pylint: disable=broad-exception-caught
            print(f"Ошибка сохранения файла: {e}")
                
    return all_books_data


def main():
    """Основная функция для запуска парсера по расписанию."""
    while True:
        schedule.every().day.at('19:00').do(scrape_books, save_to_file=True)
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    main()