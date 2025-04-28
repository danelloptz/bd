from fastapi import FastAPI, HTTPException, Depends
from sshtunnel import SSHTunnelForwarder
import pymssql
from pydantic import BaseModel
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
import time
from datetime import date
from decimal import Decimal
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from fastapi.responses import FileResponse
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

# Конфигурация SSH и базы данных
ssh_host = 'kappa.cs.petrsu.ru'
ssh_port = 22
ssh_user = 'vasilenk'       # Имя пользователя для SSH
ssh_password = 'Co6aegui'   # Пароль для SSH

db_server = '192.168.112.103'
db_port = 1433
db_name = 'db22207'
db_user = 'User086'        # Логин для базы данных
db_password = 'User086};73'    # Пароль для базы данных

app = FastAPI(
    title="Проживание API",
    description="API для получения данных о проживании клиентов из таблицы tblVisit.",
    version="1.0.0"
)

# Настройка CORS
origins = [
    "http://localhost:5173",  # Разрешаем запросы с этого адреса
    "http://127.0.0.1:5173",  # Альтернативный адрес
    "http://localhost:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Список разрешенных источников
    allow_credentials=True,  # Разрешаем отправлять cookies
    allow_methods=["*"],  # Разрешаем все HTTP-методы (GET, POST и т.д.)
    allow_headers=["*"],  # Разрешаем все заголовки
)

def connect_with_ssh_tunnel():
    """Создает SSH-туннель и подключение к базе данных."""
    try:
        # Создаем SSH-туннель
        tunnel = SSHTunnelForwarder(
            (ssh_host, ssh_port),
            ssh_username=ssh_user,
            ssh_password=ssh_password,
            remote_bind_address=(db_server, db_port)
        )
        tunnel.start()
        print(f"SSH туннель открыт на порту: {tunnel.local_bind_port}")

        # Добавляем задержку для стабилизации туннеля
        time.sleep(1)

        # Подключаемся к базе данных через туннель
        connection = pymssql.connect(
            server='127.0.0.1',
            port=tunnel.local_bind_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = connection.cursor()
        print("Подключение к базе данных успешно!")

        return connection, cursor, tunnel
    except Exception as e:
        print(f"Ошибка подключения: {e}")
        if 'tunnel' in locals():
            tunnel.stop()
        return None, None, None

class ResidenceData(BaseModel):
    """Модель данных для отображения в Swagger."""
    intVisitId: int  # Идентификатор факта проживания в гостинице (визит)
    intClientId: int  # Клиент
    intRoomNumber: int  # Комната
    datBegin: date  # Дата приезда
    datEnt: date  # Дата отъезда
    fltroomSum: Decimal  # Стоимость проживания
    fltServiceSum: Decimal  # Стоимость оказанных услуг
    ФИО_клиента: str  # Полное имя клиента
    Этаж: int  # Этаж комнаты

class AddVisitRequest(BaseModel):
    """Модель для входных данных POST-запроса."""
    datBegin: date  # Дата приезда
    datEnt: date  # Дата отъезда
    ФИО_клиента: str  # Полное имя клиента
    Номер_комнаты: int  # Номер комнаты

@app.get("/api/residence", response_model=List[ResidenceData], tags=["Проживание"])
async def get_residence_data():
    """
    Получить данные о проживании клиентов.
    """
    conn, cursor, tunnel = connect_with_ssh_tunnel()
    if not conn:
        raise HTTPException(status_code=500, detail="Не удалось подключиться к базе данных")

    try:
        query = """
        SELECT 
            v.intVisitId,
            v.intClientId,
            v.intRoomNumber,
            v.datBegin,
            v.datEnt,
            v.fltroomSum,
            v.fltServiceSum,
            c.txtClientSurname + ' ' + c.txtClientName + ' ' + ISNULL(c.txtClientSecondName, '') AS ClientFullName,
            r.intFlor AS Flor
        FROM tblVisit v
        JOIN tblClient c ON v.intClientId = c.intClientId
        JOIN tblRoom r ON v.intRoomNumber = r.intRoomNumber
        ORDER BY v.datBegin DESC
        """
        print("Выполняется запрос:", query)
        cursor.execute(query)
        rows = cursor.fetchall()
        print("Запрос выполнен успешно")

        data = [
            ResidenceData(
                intVisitId=row[0],
                intClientId=row[1],
                intRoomNumber=row[2],
                datBegin=row[3],
                datEnt=row[4],
                fltroomSum=row[5],
                fltServiceSum=row[6],
                ФИО_клиента=row[7],
                Этаж=row[8]
            )
            for row in rows
        ]

        return data
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса: {e}")
    finally:
        if conn:
            conn.close()
            print("Соединение с базой данных закрыто")
        if tunnel:
            tunnel.stop()
            print("SSH туннель закрыт")

@app.post("/api/visit/add_visit", tags=["Проживание"])
async def add_visit(data: AddVisitRequest):
    """
    Добавить новую запись о проживании клиента.
    """
    conn, cursor, tunnel = connect_with_ssh_tunnel()
    if not conn:
        raise HTTPException(status_code=500, detail="Не удалось подключиться к базе данных")

    try:
        # Разбиваем ФИО клиента на фамилию, имя и отчество
        parts = data.ФИО_клиента.split(' ')
        surname = parts[0]
        name = parts[1] if len(parts) > 1 else ''
        second_name = parts[2] if len(parts) > 2 else ''

        # Проверяем, существует ли клиент в таблице tblClient
        check_client_query = """
        SELECT intClientId FROM tblClient
        WHERE txtClientSurname = %s AND txtClientName = %s AND ISNULL(txtClientSecondName, '') = %s
        """
        cursor.execute(check_client_query, (surname, name, second_name))
        client_row = cursor.fetchone()

        if client_row:
            intClientId = client_row[0]
        else:
            raise HTTPException(status_code=500, detail=f"Нет такого клиента")

        # Проверяем, существует ли комната в таблице tblRoom
        check_room_query = """
        SELECT intRoomNumber FROM tblRoom
        WHERE intRoomNumber = %s
        """
        cursor.execute(check_room_query, (data.Номер_комнаты))
        room_row = cursor.fetchone()

        if not room_row:
            raise HTTPException(status_code=500, detail=f"Нет такой комнаты")

        # Получаем цену комнаты
        get_room_price = """
        SELECT fltRoomPrice FROM tblRoom
        WHERE intRoomNumber = %s
        """
        cursor.execute(get_room_price, (data.Номер_комнаты))
        room_price = cursor.fetchone()

        room_price = room_price[0] if room_price else 0

        # Добавляем новую запись в таблицу tblVisit
        add_visit_query = """
        INSERT INTO tblVisit (intClientId, intRoomNumber, datBegin, datEnt, fltroomSum, fltServiceSum)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(add_visit_query, (
            intClientId,
            data.Номер_комнаты,
            data.datBegin,
            data.datEnt,
            room_price,  # Стоимость проживания
            0   # Заглушка для стоимости услуг
        ))
        conn.commit()

        return {"status": "Успешно"}
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса: {e}")
    finally:
        if conn:
            conn.close()
            print("Соединение с базой данных закрыто")
        if tunnel:
            tunnel.stop()
            print("SSH туннель закрыт")


@app.get("/api/client/services/{client_id}/{visit_id}", tags=["Клиенты"])
async def get_client_services(client_id: int, visit_id: int):
    """
    Получить данные об услугах для заданного клиента и визита.
    """
    conn, cursor, tunnel = connect_with_ssh_tunnel()
    if not conn:
        raise HTTPException(status_code=500, detail="Не удалось подключиться к базе данных")

    try:
        query = """
        SELECT 
            st.txtServiceTypeName AS Наименование_услуги,
            s.intServiceCount AS Количество,
            s.fltServiceSum AS Сумма,
            s.datServiceDate AS Дата_оказания,
            st.fltServiceTypePrice AS Стоимость
        FROM tblService s
        JOIN tblServiceType st ON s.intServiceTypeId = st.intServiceTypeId
        JOIN tblVisit v ON s.intVisitId = v.intVisitId
        WHERE v.intClientId = %s AND v.intVisitId = %s
        """
        cursor.execute(query, (client_id, visit_id))
        rows = cursor.fetchall()

        # Преобразуем данные в список словарей
        data = [
            {
                "Наименование_услуги": row[0],
                "Количество": row[1],
                "Сумма": row[2],
                "Дата_оказания": row[3],
                "Стоимость": row[4]
            }
            for row in rows
        ]

        return data
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса: {e}")
    finally:
        if conn:
            conn.close()
            print("Соединение с базой данных закрыто")
        if tunnel:
            tunnel.stop()
            print("SSH туннель закрыт")


@app.get("/api/service/types", tags=["Услуги"])
async def get_service_types():
    """
    Получить список типов услуг с их стоимостью.
    """
    conn, cursor, tunnel = connect_with_ssh_tunnel()
    if not conn:
        raise HTTPException(status_code=500, detail="Не удалось подключиться к базе данных")

    try:
        query = """
        SELECT 
            intServiceTypeId AS id,
            txtServiceTypeName AS name,
            fltServiceTypePrice AS price
        FROM tblServiceType
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        # Преобразуем данные в список словарей
        data = [
            {
                "id": row[0],
                "name": row[1],
                "price": float(row[2])  # Преобразуем Decimal в float для JSON
            }
            for row in rows
        ]

        return data
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса: {e}")
    finally:
        if conn:
            conn.close()
            print("Соединение с базой данных закрыто")
        if tunnel:
            tunnel.stop()
            print("SSH туннель закрыт")


class AddServiceRequest(BaseModel):
    """Модель для входных данных POST-запроса."""
    service_type_id: int  # ID типа услуги
    visit_id: int         # ID визита
    service_count: int    # Количество услуг
    service_sum: float    # Сумма за услуги
    service_date: date    # Дата оказания
@app.post("/api/service/add_service", tags=["Услуги"])
async def add_service(data: AddServiceRequest):
    """
    Добавить новую услугу для клиента.
    """
    conn, cursor, tunnel = connect_with_ssh_tunnel()
    if not conn:
        raise HTTPException(status_code=500, detail="Не удалось подключиться к базе данных")

    try:
        # Добавляем новую услугу в таблицу tblService
        add_service_query = """
        INSERT INTO tblService (intServiceTypeId, intVisitId, intServiceCount, fltServiceSum, datServiceDate)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(add_service_query, (
            data.service_type_id,
            data.visit_id,
            data.service_count,
            data.service_sum,
            data.service_date
        ))

        # Обновляем данные в таблице tblVisit
        update_visit_query = """
        UPDATE tblVisit
        SET 
            fltServiceSum = fltServiceSum + %s
        WHERE intVisitId = %s
        """
        cursor.execute(update_visit_query, (
            data.service_sum,  # Сумма новой услуги
            data.visit_id      # ID визита
        ))

        conn.commit()

        return {"status": "Успешно"}
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса: {e}")
    finally:
        if conn:
            conn.close()
            print("Соединение с базой данных закрыто")
        if tunnel:
            tunnel.stop()
            print("SSH туннель закрыт")


@app.get("/api/report/clients", tags=["Отчеты"])
async def generate_clients_report():
    """
    Генерация PDF-отчета "Клиенты".
    """
    conn, cursor, tunnel = connect_with_ssh_tunnel()
    if not conn:
        raise HTTPException(status_code=500, detail="Не удалось подключиться к базе данных")
    try:
        # Загрузка шрифта DejaVuSans
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
        # Получаем данные из базы данных
        query = """
        SELECT 
            c.intClientId AS client_id,
            c.txtClientSurname + ' ' + c.txtClientName + ' ' + ISNULL(c.txtClientSecondName, '') AS client_full_name,
            c.txtClientAddress AS client_address,
            c.txtClientPassportNumber AS client_passport,
            v.intVisitId AS visit_id,
            v.datBegin AS dat_begin,
            v.datEnt AS dat_end,
            v.intRoomNumber AS room_number,
            s.intServiceId AS service_id,
            st.txtServiceTypeName AS service_name,
            s.intServiceCount AS service_count,
            s.fltServiceSum AS service_sum,
            s.datServiceDate AS service_date
        FROM tblClient c
        LEFT JOIN tblVisit v ON c.intClientId = v.intClientId
        LEFT JOIN tblService s ON v.intVisitId = s.intVisitId
        LEFT JOIN tblServiceType st ON s.intServiceTypeId = st.intServiceTypeId
        ORDER BY c.intClientId, v.intVisitId, s.intServiceId;
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        # Группируем данные по клиентам
        clients_data = {}
        for row in rows:
            client_id = row[0]
            client_full_name = row[1]
            client_address = row[2]
            client_passport = row[3]
            visit_id = row[4]
            dat_begin = row[5]
            dat_end = row[6]
            room_number = row[7]
            service_id = row[8]
            service_name = row[9]
            service_count = row[10]
            service_sum = row[11]
            service_date = row[12]

            if client_id not in clients_data:
                clients_data[client_id] = {
                    "full_name": client_full_name,
                    "address": client_address,
                    "passport": client_passport,
                    "visits": {},
                    "total_spent": 0
                }

            if visit_id and visit_id not in clients_data[client_id]["visits"]:
                clients_data[client_id]["visits"][visit_id] = {
                    "dat_begin": dat_begin,
                    "dat_end": dat_end,
                    "room_number": room_number,
                    "services": [],
                    "total_services_cost": 0,
                    "total_services_count": 0
                }

            if service_id:
                clients_data[client_id]["visits"][visit_id]["services"].append({
                    "service_name": service_name,
                    "service_count": service_count,
                    "service_sum": service_sum,
                    "service_date": service_date
                })
                clients_data[client_id]["visits"][visit_id]["total_services_cost"] += service_sum
                clients_data[client_id]["visits"][visit_id]["total_services_count"] += service_count

        # Генерация PDF
        file_path = "Клиенты.pdf"
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()

        # Создаем новый стиль с использованием шрифта DejaVuSans
        normal_style = styles['Normal']
        normal_style.fontName = 'DejaVuSans'
        heading2_style = styles['Heading2']
        heading2_style.fontName = 'DejaVuSans'
        title_style = styles['Title']
        title_style.fontName = 'DejaVuSans'

        story = []

        # Заголовок отчета
        title = Paragraph("Отчет: Клиенты", title_style)
        story.append(title)
        story.append(Spacer(1, 12))

        # Добавляем данные по каждому клиенту
        for client_id, data in clients_data.items():
            # Информация о клиенте
            client_header = Paragraph(f"Клиент: {data['full_name']}", heading2_style)
            address = Paragraph(f"Адрес: {data['address']}", normal_style)
            passport = Paragraph(f"Номер паспорта: {data['passport']}", normal_style)
            story.append(client_header)
            story.append(address)
            story.append(passport)
            story.append(Spacer(1, 12))

            # Добавляем данные по каждому визиту
            for visit_id, visit_data in data["visits"].items():
                visit_header = Paragraph(
                    f"Визит: {visit_data['dat_begin']} - {visit_data['dat_end']}, "
                    f"Комната: {visit_data['room_number']}",
                    heading2_style
                )
                story.append(visit_header)

                # Таблица услуг
                table_data = [
                    ["Наименование услуги", "Дата оказания", "Количество", "Стоимость"]
                ]
                for service in visit_data["services"]:
                    table_data.append([
                        Paragraph(service["service_name"], normal_style),
                        Paragraph(service["service_date"].strftime("%Y-%m-%d"), normal_style),
                        Paragraph(str(service["service_count"]), normal_style),
                        Paragraph(f"{service['service_sum']:.2f} руб.", normal_style)
                    ])

                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans'),  # Указываем шрифт для заголовков таблицы
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)

                # Итоги по визиту
                total_services_text = Paragraph(
                    f"Общая стоимость услуг: {visit_data['total_services_cost']:.2f} руб., "
                    f"Количество услуг: {visit_data['total_services_count']}",
                    normal_style
                )
                story.append(total_services_text)
                story.append(Spacer(1, 12))

            # Итоги по клиенту
            total_spent_text = Paragraph(
                f"Общая сумма, потраченная клиентом: {data['total_spent']:.2f} руб.",
                normal_style
            )
            story.append(total_spent_text)
            story.append(Spacer(1, 12))
            story.append(Paragraph("-" * 80, normal_style))
            story.append(Spacer(1, 12))

        # Сохраняем PDF
        doc.build(story)

        # Возвращаем файл пользователю
        return FileResponse(file_path, media_type="application/pdf", filename="Клиенты.pdf")
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса: {e}")
    finally:
        if conn:
            conn.close()
            print("Соединение с базой данных закрыто")
        if tunnel:
            tunnel.stop()
            print("SSH туннель закрыт")


@app.get("/api/report/rooms/{room_number}", tags=["Отчеты"])
async def generate_rooms_report(room_number: int):
    """
    Генерация PDF-отчета "Комнаты".
    """
    conn, cursor, tunnel = connect_with_ssh_tunnel()
    if not conn:
        raise HTTPException(status_code=500, detail="Не удалось подключиться к базе данных")

    try:
        # Загрузка шрифта DejaVuSans
        pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))

        # Получаем данные из базы данных
        query = """
        SELECT 
            r.intRoomNumber AS room_number,
            r.intFlor AS floor,
            r.fltRoomPrice AS price,
            r.txtRoomDescription AS description,
            c.txtClientSurname + ' ' + c.txtClientName + ' ' + ISNULL(c.txtClientSecondName, '') AS client_full_name,
            c.txtClientAddress AS client_address,
            c.txtClientPassportNumber AS client_passport,
            v.datBegin AS dat_begin,
            v.datEnt AS dat_end,
            st.txtServiceTypeName AS service_name,
            s.intServiceCount AS service_count,
            s.fltServiceSum AS service_sum,
            s.datServiceDate AS service_date
        FROM tblRoom r
        LEFT JOIN tblVisit v ON r.intRoomNumber = v.intRoomNumber
        LEFT JOIN tblClient c ON v.intClientId = c.intClientId
        LEFT JOIN tblService s ON v.intVisitId = s.intVisitId
        LEFT JOIN tblServiceType st ON s.intServiceTypeId = st.intServiceTypeId
        WHERE r.intRoomNumber = %s
        ORDER BY s.datServiceDate;
        """
        cursor.execute(query, (room_number,))
        rows = cursor.fetchall()

        # Проверяем, есть ли данные для указанной комнаты
        if not rows:
            raise HTTPException(status_code=404, detail=f"Комната с номером {room_number} не найдена.")

        # Группируем данные по комнате и клиентам
        room_data = {
            "room_number": rows[0][0],
            "floor": rows[0][1],
            "price": rows[0][2],
            "description": rows[0][3],
            "clients": []
        }

        for row in rows:
            client_full_name = row[4]
            client_address = row[5]
            client_passport = row[6]
            dat_begin = row[7]
            dat_end = row[8]
            service_name = row[9]
            service_count = row[10]
            service_sum = row[11]
            service_date = row[12]

            # Добавляем клиента, если его еще нет в списке
            client_exists = False
            for client in room_data["clients"]:
                if client["client_full_name"] == client_full_name and client["dat_begin"] == dat_begin:
                    client_exists = True
                    break

            if not client_exists and client_full_name:
                room_data["clients"].append({
                    "client_full_name": client_full_name,
                    "client_address": client_address,
                    "client_passport": client_passport,
                    "dat_begin": dat_begin,
                    "dat_end": dat_end,
                    "services": []
                })

            # Добавляем услуги для клиента
            if service_name:
                for client in room_data["clients"]:
                    if client["client_full_name"] == client_full_name and client["dat_begin"] == dat_begin:
                        client["services"].append({
                            "service_name": service_name,
                            "service_count": service_count,
                            "service_sum": service_sum,
                            "service_date": service_date
                        })

        # Генерация PDF
        file_path = f"Комната_{room_number}.pdf"
        doc = SimpleDocTemplate(file_path, pagesize=A4)
        styles = getSampleStyleSheet()

        # Создаем новый стиль с использованием шрифта DejaVuSans
        normal_style = styles['Normal']
        normal_style.fontName = 'DejaVuSans'
        heading2_style = styles['Heading2']
        heading2_style.fontName = 'DejaVuSans'
        title_style = styles['Title']
        title_style.fontName = 'DejaVuSans'

        story = []

        # Заголовок отчета
        title = Paragraph(f"Отчет: Комната №{room_number}", title_style)
        story.append(title)
        story.append(Spacer(1, 12))

        # Информация о комнате
        room_info = Paragraph(
            f"Этаж: {room_data['floor']}, "
            f"Стоимость: {room_data['price']} руб., "
            f"Описание: {room_data['description']}",
            normal_style
        )
        story.append(room_info)
        story.append(Spacer(1, 12))

        # Добавляем данные по каждому клиенту
        for client in room_data["clients"]:
            # Информация о клиенте
            client_header = Paragraph(
                f"Клиент: {client['client_full_name']}, "
                f"Адрес: {client['client_address']}, "
                f"Паспорт: {client['client_passport']}, "
                f"Дата приезда: {client['dat_begin']}, "
                f"Дата отъезда: {client['dat_end']}",
                heading2_style
            )
            story.append(client_header)

            # Таблица услуг
            table_data = [
                ["Наименование услуги", "Дата оказания", "Количество", "Стоимость"]
            ]
            for service in client["services"]:
                table_data.append([
                    Paragraph(service["service_name"], normal_style),
                    Paragraph(service["service_date"].strftime("%Y-%m-%d"), normal_style),
                    Paragraph(str(service["service_count"]), normal_style),
                    Paragraph(f"{service['service_sum']:.2f} руб.", normal_style)
                ])

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'DejaVuSans'),  # Указываем шрифт для заголовков таблицы
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)

            story.append(Spacer(1, 12))

        # Сохраняем PDF
        doc.build(story)

        # Возвращаем файл пользователю
        return FileResponse(file_path, media_type="application/pdf", filename=f"Комната_{room_number}.pdf")
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса: {e}")
    finally:
        if conn:
            conn.close()
            print("Соединение с базой данных закрыто")
        if tunnel:
            tunnel.stop()
            print("SSH туннель закрыт")

@app.get("/api/rooms", tags=["Комнаты"])
async def get_rooms():
    """
    Получить список всех комнат.
    """
    conn, cursor, tunnel = connect_with_ssh_tunnel()
    if not conn:
        raise HTTPException(status_code=500, detail="Не удалось подключиться к базе данных")

    try:
        query = """
        SELECT 
            intRoomNumber AS intRoomNumber,
            intFlor AS intFlor,
            fltRoomPrice AS fltRoomPrice
        FROM tblRoom
        ORDER BY intRoomNumber;
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        # Преобразуем данные в список словарей
        data = [
            {
                "intRoomNumber": row[0],
                "intFlor": row[1],
                "fltRoomPrice": row[2]
            }
            for row in rows
        ]

        return data
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса: {e}")
    finally:
        if conn:
            conn.close()
            print("Соединение с базой данных закрыто")
        if tunnel:
            tunnel.stop()
            print("SSH туннель закрыт")


@app.post("/api/trigger/create", tags=["Триггеры"])
async def create_trigger():
    """
    Создать триггер для проверки дубликатов услуг.
    """
    conn, cursor, tunnel = connect_with_ssh_tunnel()
    if not conn:
        raise HTTPException(status_code=500, detail="Не удалось подключиться к базе данных")

    try:
        # SQL-запрос для создания триггера
        query = """
        CREATE TRIGGER trg_CheckDuplicateServices
        ON tblService
        INSTEAD OF INSERT
        AS
        BEGIN
            SET NOCOUNT ON;

            -- Проверяем, есть ли дубликаты
            IF EXISTS (
                SELECT 1
                FROM inserted i
                JOIN tblService s
                    ON i.intServiceTypeId = s.intServiceTypeId
                    AND i.intVisitId = s.intVisitId
                    AND i.datServiceDate = s.datServiceDate
            )
            BEGIN
                RAISERROR('Услуга данного типа уже была оказана в этот день.', 16, 1);
                RETURN;
            END

            -- Если проверка пройдена, вставляем данные
            INSERT INTO tblService (
                intServiceTypeId,
                intVisitId,
                intServiceCount,
                fltServiceSum,
                datServiceDate
            )
            SELECT 
                intServiceTypeId,
                intVisitId,
                intServiceCount,
                fltServiceSum,
                datServiceDate
            FROM inserted;
        END;
        """
        cursor.execute(query)
        conn.commit()

        return {"status": "Триггер успешно создан"}
    except Exception as e:
        print(f"Ошибка выполнения запроса: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка выполнения запроса: {e}")
    finally:
        if conn:
            conn.close()
            print("Соединение с базой данных закрыто")
        if tunnel:
            tunnel.stop()
            print("SSH туннель закрыт")