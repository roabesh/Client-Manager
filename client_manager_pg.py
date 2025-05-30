import psycopg2
from psycopg2.sql import SQL, Identifier
import re

# Настройки подключения к вашей БД
DB_NAME = "your_db_name"
DB_USER = "your_db_user"
DB_PASSWORD = "your_db_password"
DB_HOST = "localhost"
DB_PORT = "5432"

EMAIL_REGEX = re.compile(r'^[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]+$')

def create_db(conn):
    """Создаёт таблицы clients и telephones с валидацией email."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                name VARCHAR(40) NOT NULL,
                surname VARCHAR(40) NOT NULL,
                email VARCHAR(320) UNIQUE NOT NULL,
                CONSTRAINT proper_email CHECK (email ~* '^[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$')
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS telephones (
                id SERIAL PRIMARY KEY,
                number INTEGER UNIQUE,
                client INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE
            );
        """)
        conn.commit()

def add_client(conn, name, surname, email, phones=None):
    if not EMAIL_REGEX.match(email):
        print(f"Ошибка: Некорректный email '{email}'")
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM clients WHERE email = %s;", (email,))
        if cur.fetchone():
            print(f"Ошибка: Клиент с email '{email}' уже существует.")
            return None
        cur.execute(
            "INSERT INTO clients (name, surname, email) VALUES (%s, %s, %s) RETURNING id;",
            (name, surname, email)
        )
        client_id = cur.fetchone()[0]
        if phones:
            for phone in phones:
                add_phone(conn, client_id, phone)
        conn.commit()
        print(f"Клиент '{name} {surname}' добавлен с id {client_id}")
        return client_id

def add_phone(conn, client_id, number):
    try:
        number = int(number)
    except ValueError:
        print(f"Ошибка: Телефон должен быть числом, получено '{number}'")
        return None
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM clients WHERE id = %s;", (client_id,))
        if not cur.fetchone():
            print(f"Ошибка: Клиент с id {client_id} не найден.")
            return None
        cur.execute("SELECT id FROM telephones WHERE number = %s;", (number,))
        if cur.fetchone():
            print(f"Ошибка: Телефон {number} уже существует.")
            return None
        cur.execute(
            "INSERT INTO telephones (number, client) VALUES (%s, %s) RETURNING id;",
            (number, client_id)
        )
        phone_id = cur.fetchone()[0]
        conn.commit()
        print(f"Телефон {number} добавлен клиенту {client_id} (id записи {phone_id})")
        return phone_id

def update_client(conn, client_id, name=None, surname=None, email=None):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM clients WHERE id = %s;", (client_id,))
        if not cur.fetchone():
            print(f"Ошибка: Клиент с id {client_id} не найден.")
            return
        updates = {}
        if name:
            updates['name'] = name
        if surname:
            updates['surname'] = surname
        if email:
            if not EMAIL_REGEX.match(email):
                print(f"Ошибка: Некорректный email '{email}'")
                return
            updates['email'] = email
        for key, value in updates.items():
            cur.execute(SQL("UPDATE clients SET {} = %s WHERE id = %s;").format(Identifier(key)), (value, client_id))
        conn.commit()
        print(f"Клиент {client_id} обновлён: {updates}")

def delete_phone(conn, client_id, number):
    try:
        number = int(number)
    except ValueError:
        print(f"Ошибка: Телефон должен быть числом, получено '{number}'")
        return
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM telephones WHERE number = %s AND client = %s;", (number, client_id))
        if not cur.fetchone():
            print(f"Ошибка: Телефон {number} у клиента {client_id} не найден.")
            return
        cur.execute("DELETE FROM telephones WHERE number = %s AND client = %s;", (number, client_id))
        conn.commit()
        print(f"Телефон {number} у клиента {client_id} удалён.")

def delete_client(conn, client_id):
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM clients WHERE id = %s;", (client_id,))
        if not cur.fetchone():
            print(f"Ошибка: Клиент с id {client_id} не найден.")
            return
        cur.execute("DELETE FROM clients WHERE id = %s;", (client_id,))
        conn.commit()
        print(f"Клиент {client_id} и его телефоны удалены.")

def find_client(conn, name=None, surname=None, email=None, number=None):
    query = SQL('''
        SELECT c.id, c.name, c.surname, c.email, t.number
        FROM clients c
        FULL OUTER JOIN telephones t ON c.id = t.client
        WHERE (%(name)s IS NULL OR c.name = %(name)s)
          AND (%(surname)s IS NULL OR c.surname = %(surname)s)
          AND (%(email)s IS NULL OR c.email = %(email)s)
          AND (%(number)s IS NULL OR t.number = %(number)s)
    ''')
    params = {'name': name, 'surname': surname, 'email': email, 'number': int(number) if number else None}
    with conn.cursor() as cur:
        cur.execute(query, params)
        results = cur.fetchall()
        print("Результаты поиска:")
        for row in results:
            print(row)
        return results

def print_clients(conn):
    with conn.cursor() as cur:
        cur.execute('''
            SELECT c.id, c.name, c.surname, c.email, t.number
            FROM clients c
            LEFT JOIN telephones t ON c.id = t.client
            ORDER BY c.id
        ''')
        for row in cur.fetchall():
            print(row)

# Демонстрация работы функций
if __name__ == "__main__":
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    create_db(conn)

    # Добавление клиентов
    id1 = add_client(conn, "Иван", "Иванов", "ivanov@example.com", [777])
    id2 = add_client(conn, "Петр", "Петров", "petrov@example.com")
    id3 = add_client(conn, "Сидор", "Сидоров", "sidorov@example.com", [888, 999])

    print("\nКлиенты после добавления:")
    print_clients(conn)

    # Добавление телефона
    add_phone(conn, id2, 70000000000)
    print("\nПосле добавления телефона Петру:")
    print_clients(conn)

    # Изменение данных клиента
    update_client(conn, id1, name="Иван-Иван")
    print("\nПосле изменения имени Иванова:")
    print_clients(conn)

    # Удаление телефона
    delete_phone(conn, id3, 888)
    print("\nПосле удаления одного телефона у Сидорова:")
    print_clients(conn)

    # Поиск клиента
    print("\nПоиск по email 'petrov@example.com':")
    find_client(conn, email="petrov@example.com")

    print("\nПоиск по телефону 777:")
    find_client(conn, number=777)

    # Удаление клиента
    delete_client(conn, id2)
    print("\nПосле удаления Петра:")
    print_clients(conn)

    conn.close() 