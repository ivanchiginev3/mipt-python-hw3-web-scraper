import pytest
import json
import sys
import os


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import get_book_data

class TestBookScraper:
    """Тесты для функций парсинга книг"""
    
    # Тестовые URL
    TEST_BOOK_URL = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    TEST_BOOK_URL_2 = "https://books.toscrape.com/catalogue/tipping-the-velvet_999/index.html"
    
    def test_scrape_book_data_returns_dict(self):
        """Тест 1: Проверяем, что функция возвращает словарь"""
        result = get_book_data(self.TEST_BOOK_URL)
        
        assert result is not None, "Функция вернула None"
        assert isinstance(result, dict), f"Ожидался dict, получен {type(result)}"
        assert len(result) > 0, "Словарь пустой"
        
    def test_scrape_book_data_has_required_keys(self):
        """Тест 2: Проверяем наличие обязательных ключей в данных книги"""
        result = get_book_data(self.TEST_BOOK_URL)
        
        required_keys = ['name', 'rating']
        for key in required_keys:
            assert key in result, f"Ключ '{key}' отсутствует в результате"
        
        # Проверяем, что есть хотя бы некоторые ключи из таблицы
        table_keys = ['UPC', 'Price', 'Availability']
        has_table_data = any(key in result for key in table_keys)
        assert has_table_data, "Отсутствуют данные из таблицы"
    
    def test_scrape_books_returns_correct_number_of_books(self):
        """Тест 3: количество собранных книг соответствует ожиданиям"""
        # Загружаем данные из JSON файла
        with open('artifacts/books_data.json', 'r', encoding='utf-8') as f:
            books_data = json.load(f)
        
        # Ожидаемое количество книг с сайта books.toscrape.com
        expected_count = 1000
        
        # Фактическое количество книг в JSON
        actual_count = len(books_data)
        
        # Проверяем что количество совпадает
        assert actual_count == expected_count, \
            f"Ожидалось {expected_count} книг, но в JSON {actual_count} книг"
        
        
    def test_scrape_book_data_field_values_correct(self):
        """Тест 4: Проверяем корректность значений полей"""
        result = get_book_data(self.TEST_BOOK_URL)
        
        # Проверяем название
        assert 'name' in result
        assert result['name'] == 'A Light in the Attic'
        
        # Проверяем рейтинг (должен быть от 1 до 5)
        assert 'rating' in result
        assert result['rating'] in ['1', '2', '3', '4', '5', 'Unknown']
        
        # Проверяем, что Availability содержит только цифры
        if 'Availability' in result:
            assert result['Availability'].isdigit(), f"Availability должен содержать только цифры: {result['Availability']}"
            
if __name__ == "__main__":
    pytest.main([__file__, "-v"])