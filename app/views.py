from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import ExampleForm
import os
import xml.etree.ElementTree as ET
import re

def create_or_update_xml_file(data):
    file_path = "output.xml"

    # Проверяем, существует ли файл
    if os.path.exists(file_path):
        # Проверяем, пустой ли файл
        if os.path.getsize(file_path) == 0:
            root = ET.Element("data")  # Создаем корневой элемент, если файл пустой
            tree = ET.ElementTree(root)
        else:
            tree = ET.parse(file_path)  # Загружаем существующий файл
            root = tree.getroot()
    else:
        # Если файла нет, создаём новый корневой элемент
        root = ET.Element("data")
        tree = ET.ElementTree(root)

    # Проверка на наличие дубликатов
    keys = ['name', 'age', 'email', 'what_sells']
    is_duplicate = any(
        all(existing_entry.find(key).text == str(data[key]) for key in keys)
        for existing_entry in root.findall('entry')
    )

    if not is_duplicate:
        # Добавляем новую запись в XML, если она уникальна
        entry = ET.SubElement(root, "entry")
        for key, value in data.items():
            child = ET.SubElement(entry, key)
            child.text = str(value)

        # Форматируем XML с отступами
        ET.indent(tree, space="  ", level=0)

        # Сохраняем обновлённый XML-файл с отступами
        tree.write(file_path, encoding="utf-8", xml_declaration=True)
        return True
    else:
        return False  # Указывает, что запись дублирующая

def xml_form(request):
    form = ExampleForm()
    if request.method == 'POST':
        form = ExampleForm(request.POST)
        if form.is_valid():
            form.save()  # сохраняем в БД
            # Преобразуем данные в формат XML и дополняем существующий файл
            added = create_or_update_xml_file(form.cleaned_data)
            if added:
                return render(request, 'xml_form.html', {'form': form, 'success': True, 'message': "Запись добавлена"})
            else:
                return render(request, 'xml_form.html', {'form': form, 'success': False, 'message': "Дублирующая запись"})
    
    return render(request, 'xml_form.html', {'form': form})

def display_xml_data(request):
    xml_file_path = 'output.xml'  # Путь к XML-файлу
    data = []
    errors = []  # Список для хранения ошибок

    if os.path.exists(xml_file_path) and os.path.getsize(xml_file_path) > 0:
        try:
            # Разбор XML-файла
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            # Проход по элементам и добавление их в список
            for entry in root.findall('entry'):
                field_errors = []  # Для ошибок внутри одной записи

                # Получаем данные полей или указываем None, если данные отсутствуют
                name = entry.find('name').text if entry.find('name') is not None else None
                age = entry.find('age').text if entry.find('age') is not None else None
                email = entry.find('email').text if entry.find('email') is not None else None
                what_sells = entry.find('what_sells').text if entry.find('what_sells') is not None else None

                # Проверяем, какие данные отсутствуют, и добавляем сообщения об ошибке
                if name is None:
                    field_errors.append("Отсутствует имя.")
                if age is None:
                    field_errors.append("Отсутствует возраст.")
                if email is None:
                    field_errors.append("Отсутствует email.")
                if what_sells is None:
                    field_errors.append("Отсутствует информация о том, что продает.")

                # Если есть ошибки в записи, добавляем их в общий список ошибок
                if field_errors:
                    errors.append(f"Ошибка в записи с name={name or 'None'}: " + "; ".join(field_errors))

                # Добавляем запись в таблицу, даже если в ней есть ошибки
                data.append({
                    'name': name,
                    'age': age,
                    'email': email,
                    'what_sells': what_sells,
                })

        except ET.ParseError:
            errors.append("XML-файл повреждён и не может быть разобран.")  # Ошибка при парсинге файла
    else:
        errors.append("XML-файл не найден или пуст.")

    return render(request, 'display_xml_data.html', {'data': data, 'errors': errors})

# Объединённая функция для скачивания и загрузки XML файла


def manage_xml(request):
    errors = []  # Список для хранения сообщений об ошибках
    success_message = None  # Сообщение об успешном выполнении
    file_path = "output.xml"  # Путь к XML файлу

    # Регулярное выражение для проверки формата email
    email_regex = re.compile(r'^[^@]+@[^@]+\.[^@]+$')

    # Обрабатываем запрос на скачивание файла
    # Проверяем, был ли запрос на скачивание файла через GET-запрос
    if request.method == 'GET' and 'download' in request.GET:
        # Проверяем, существует ли файл output.xml
        if os.path.exists(file_path):
            # Если файл существует, открываем его для чтения в двоичном режиме
            with open(file_path, 'rb') as xml_file:
                # Создаем ответ, возвращая содержимое файла как HTTP-ответ
                response = HttpResponse(xml_file.read(), content_type='application/xml')
                # Устанавливаем заголовок для скачивания файла (Content-Disposition)
                response['Content-Disposition'] = 'attachment; filename="output.xml"'
                # Возвращаем ответ для скачивания файла
                return response
            
        else:
            errors.append("XML-файл не найден для скачивания.")

    # Обрабатываем запрос на загрузку файла
    if request.method == 'POST' and 'upload' in request.FILES:
        uploaded_file = request.FILES['upload']  # Получаем загруженный файл

        try:
            tree = ET.parse(uploaded_file)  # Пробуем разобрать XML файл
            root = tree.getroot()

            # Проверяем, что корневой элемент правильный (должен быть <data>)
            if root.tag != 'data':
                errors.append("Неверный формат XML файла. Ожидается корневой элемент <data>.")
            else:
                # Загружаем существующий XML файл, если он существует
                if os.path.exists(file_path):
                    existing_tree = ET.parse(file_path)
                    existing_root = existing_tree.getroot()
                else:
                    existing_root = ET.Element("data")
                    existing_tree = ET.ElementTree(existing_root)

                keys = ['name', 'age', 'email', 'what_sells']
                records_added = 0  # Счётчик добавленных записей

                for entry in root.findall('entry'):
                    new_entry_data = {key: entry.find(key).text if entry.find(key) is not None else None for key in keys}

                    # Проверяем, что все ключи присутствуют в новой записи
                    if any(new_entry_data[key] is None for key in keys):
                        errors.append(f"Неполные данные в записи: {new_entry_data}")
                        continue  # Пропускаем неполные записи

                    # Список для хранения ошибок для текущей записи
                    entry_errors = []

                    # Проверка возраста (должен быть неотрицательным числом)
                    try:
                        if int(new_entry_data['age']) < 0:
                            entry_errors.append(f"Ошибка: возраст не может быть отрицательным.")
                    except (ValueError, TypeError):
                        entry_errors.append(f"Ошибка: некорректное значение возраста.")

                    # Проверка формата email
                    if not email_regex.match(new_entry_data['email']):
                        entry_errors.append(f"Ошибка: некорректный формат email.")

                    # Если есть ошибки для текущей записи, добавляем их в общий список ошибок
                    if entry_errors:
                        # Добавляем запись с ошибками в общий список ошибок
                        errors.append(f"Запись с ошибками: {new_entry_data}.{', '.join(entry_errors)}")
                        continue  # Пропускаем запись с ошибками

                    # Проверяем, нет ли такой записи уже в существующем файле
                    is_duplicate = any(
                        all(existing_entry.find(key).text == new_entry_data[key] for key in keys)
                        for existing_entry in existing_root.findall('entry')
                    )

                    # Если запись уникальна, добавляем её
                    if not is_duplicate:
                        new_entry = ET.SubElement(existing_root, "entry")
                        for key, value in new_entry_data.items():
                            child = ET.SubElement(new_entry, key)
                            child.text = value
                        records_added += 1  # Увеличиваем счетчик добавленных записей
                    else:
                        # Если запись является дубликатом, добавляем информацию об этом в список ошибок
                        errors.append(f"Дублирующая запись: {new_entry_data}")

                # Если хотя бы одна запись была добавлена, сохраняем файл с форматированием
                if records_added > 0:
                    # Добавляем отступы для форматирования
                    ET.indent(existing_tree, space="  ", level=0)
                    existing_tree.write(file_path, encoding="utf-8", xml_declaration=True)
                    success_message = f"Добавлено {records_added} новых записей в XML файл."
                else:
                    success_message = "Новые записи не были добавлены, так как все записи были дубликатами или содержали ошибки."

        except ET.ParseError:
            errors.append("Ошибка парсинга XML файла. Файл поврежден или не является корректным XML.")

    return render(request, 'upload_download_xml.html', {'errors': errors, 'success_message': success_message})
