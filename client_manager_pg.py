import psycopg2

# Настройки подключения к вашей БД
DB_NAME = "your_db_name"
DB_USER = "your_db_user"
DB_PASSWORD = "your_db_password"
DB_HOST = "localhost"
DB_PORT = "5432"

def create_db(conn):
    """Создаёт таблицы clients и phones."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(40) NOT NULL,
                last_name VARCHAR(40) NOT NULL,
                email VARCHAR(80) UNIQUE NOT NULL
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS phones (
                id SERIAL PRIMARY KEY,
                client_id INTEGER NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
                phone VARCHAR(20)
            );
        """)
        conn.commit()

def add_client(conn, first_name, last_name, email, phones=None):
    """Добавляет нового клиента и его телефоны (если есть)."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO clients (first_name, last_name, email) VALUES (%s, %s, %s) RETURNING id;",
            (first_name, last_name, email)
        )
        client_id = cur.fetchone()[0]
        if phones:
            for phone in phones:
                cur.execute(
                    "INSERT INTO phones (client_id, phone) VALUES (%s, %s);",
                    (client_id, phone)
                )
        conn.commit()
    return client_id

def add_phone(conn, client_id, phone):
    """Добавляет телефон для существующего клиента."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO phones (client_id, phone) VALUES (%s, %s);",
            (client_id, phone)
        )
        conn.commit()

def update_client(conn, client_id, first_name=None, last_name=None, email=None):
    """Изменяет данные о клиенте."""
    with conn.cursor() as cur:
        if first_name:
            cur.execute("UPDATE clients SET first_name = %s WHERE id = %s;", (first_name, client_id))
        if last_name:
            cur.execute("UPDATE clients SET last_name = %s WHERE id = %s;", (last_name, client_id))
        if email:
            cur.execute("UPDATE clients SET email = %s WHERE id = %s;", (email, client_id))
        conn.commit()

def delete_phone(conn, client_id, phone):
    """Удаляет телефон клиента."""
    with conn.cursor() as cur:
        cur.execute(
            "DELETE FROM phones WHERE client_id = %s AND phone = %s;",
            (client_id, phone)
        )
        conn.commit()

def delete_client(conn, client_id):
    """Удаляет клиента и все его телефоны."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM clients WHERE id = %s;", (client_id,))
        conn.commit()

def find_client(conn, first_name=None, last_name=None, email=None, phone=None):
    """Находит клиента по имени, фамилии, email или телефону."""
    query = """
        SELECT c.id, c.first_name, c.last_name, c.email, p.phone
        FROM clients c
        LEFT JOIN phones p ON c.id = p.client_id
        WHERE TRUE
    """
    params = []
    if first_name:
        query += " AND c.first_name = %s"
        params.append(first_name)
    if last_name:
        query += " AND c.last_name = %s"
        params.append(last_name)
    if email:
        query += " AND c.email = %s"
        params.append(email)
    if phone:
        query += " AND p.phone = %s"
        params.append(phone)
    with conn.cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()

def print_clients(conn):
    """Печатает всех клиентов и их телефоны."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT c.id, c.first_name, c.last_name, c.email, p.phone
            FROM clients c
            LEFT JOIN phones p ON c.id = p.client_id
            ORDER BY c.id
        """)
        for row in cur.fetchall():
            print(row)

# Демонстрация работы функций
if __name__ == "__main__":
    # Подключение к БД
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

    create_db(conn)

    # Добавление клиентов
    id1 = add_client(conn, "Иван", "Иванов", "ivanov@example.com", ["+79991112233"])
    id2 = add_client(conn, "Петр", "Петров", "petrov@example.com")
    id3 = add_client(conn, "Сидор", "Сидоров", "sidorov@example.com", ["+78889990000", "+78889990001"])

    print("Клиенты после добавления:")
    print_clients(conn)

    # Добавление телефона
    add_phone(conn, id2, "+70000000000")
    print("\nПосле добавления телефона Петру:")
    print_clients(conn)

    # Изменение данных клиента
    update_client(conn, id1, first_name="Иван-Иван")
    print("\nПосле изменения имени Иванова:")
    print_clients(conn)

    # Удаление телефона
    delete_phone(conn, id3, "+78889990000")
    print("\nПосле удаления одного телефона у Сидорова:")
    print_clients(conn)

    # Поиск клиента
    print("\nПоиск по email 'petrov@example.com':")
    print(find_client(conn, email="petrov@example.com"))

    print("\nПоиск по телефону '+79991112233':")
    print(find_client(conn, phone="+79991112233"))

    # Удаление клиента
    delete_client(conn, id2)
    print("\nПосле удаления Петра:")
    print_clients(conn)

    conn.close() 