import psycopg2
from psycopg2.sql import SQL, Identifier

# 1.Функция, создающая структуру БД (таблицы).

def create_db(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clients(
                id SERIAL PRIMARY KEY,
                name VARCHAR(40) NOT NULL,
                surname VARCHAR(40) NOT NULL,
                email VARCHAR(320) UNIQUE NOT NULL,
                CONSTRAINT proper_email CHECK (email ~* '^[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+[.][A-Za-z]+$')
            );
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS telephones(
                id SERIAL PRIMARY KEY,
                number INTEGER UNIQUE NOT NULL,
                client INTEGER NOT NULL REFERENCES clients (id) ON DELETE CASCADE
            );
        """)
        conn.commit()

# 2.Функция, позволяющая добавить нового клиента.

def add_client(name, surname, email):
    with conn.cursor() as cur:
        cur.execute("""
                SELECT email 
                  FROM clients 
                 WHERE email = %s;
                """, (email,))
        if len(cur.fetchall()) > 0:
            print('Клиент с таким email уже существует')
            return
    with conn.cursor() as cur:
        cur.execute("""
                    INSERT INTO clients (name, surname, email) 
                    VALUES (%s, %s, %s) RETURNING id
                    """, (name, surname, email))
        print(f'ID созданного клиента:',cur.fetchone())

# 3.Функция, позволяющая добавить телефон для существующего клиента.

def add_phone(number, client):
    with conn.cursor() as cur:
        cur.execute("""
                SELECT number 
                  FROM telephones 
                 WHERE number = %s;
                """, (number,))
        if len(cur.fetchall()) > 0:
            print('Указанный телефон уже существует')
            return
    with conn.cursor() as cur:
        cur.execute("""
                        SELECT id 
                          FROM clients 
                         WHERE id = %s;
                        """, (client,))
        if len(cur.fetchall()) == 0:
            print('Указанный клиент отсутствует в базе клиентов')
            return
    with conn.cursor() as cur:
        cur.execute("""
                    INSERT INTO telephones(number, client) 
                    VALUES (%s, %s) RETURNING id;
                    """, (number, client))
        print(f'ID созданной записи телефона:',cur.fetchone())

# 4.Функция, позволяющая изменить данные о клиенте.

def change_client(client_id, name=None, surname=None, email=None):
    with conn.cursor() as cur:
        cur.execute("""
                SELECT id 
                  FROM clients 
                 WHERE id = %s;
                """, (client_id,))
        if len(cur.fetchall()) == 0:
            print('Клиент с таким id не существует')
            return
    atributes_client = {'name' : name, 'surname' : surname, 'email' : email}
    for key, value in atributes_client.items():
        if value:
            with conn.cursor() as cur:
                cur.execute(SQL("UPDATE clients SET {} = %s WHERE id = %s").format(Identifier(key)), (value, client_id))
                conn.commit()
    with conn.cursor() as cur:
        cur.execute("""
                        SELECT id, name, surname, email
                          FROM clients
                         WHERE id = %s;
                        """, (client_id,))
        print(f'Обновленная запись клиента:', cur.fetchone())

# 5.Функция, позволяющая удалить телефон для существующего клиента.

def delete_phone(client_id, number):
    with conn.cursor() as cur:
        cur.execute("""
                   SELECT number 
                     FROM telephones 
                    WHERE number = %s and client = %s;
                   """, (number, client_id))
        if len(cur.fetchall()) == 0:
            print('Записи номера клиента с таким телефоном не существует. Проверьте данные.')
            return
    with conn.cursor() as cur:
        cur.execute("""
                   DELETE FROM telephones 
                         WHERE number = %s and client = %s;
                   """, (number, client_id))
        conn.commit()
        print(f'Телефон {number} у клиента {client_id} удален')

# 6.Функция, позволяющая удалить существующего клиента.

def delete_client(client_id):
    with conn.cursor() as cur:
        cur.execute("""
                SELECT id 
                  FROM clients 
                 WHERE id = %s;
                """, (client_id,))
        if len(cur.fetchall()) == 0:
            print('Клиент с таким id не существует')
            return
    with conn.cursor() as cur:
        cur.execute("""
                    DELETE FROM clients 
                          WHERE id = %s;
                    """, (client_id,))
        conn.commit()
        print(f'Клиент {client_id} и его телефоны удалены')

# 7. Функция, позволяющая найти клиента по его данным: имени, фамилии, email или телефону.

def find_client(name = None, surname = None, email = None, number = None):
    with conn.cursor() as cur:
        cur.execute("""
                   SELECT c.*, t.number
                     FROM clients c 
                     FUll OUTER JOIN telephones t ON c.id = t.client
                    WHERE (name = %(name)s or %(name)s is NULL) 
                          and (surname = %(surname)s or %(surname)s is NULL)
                          and (email = %(email)s or %(email)s is NULL)
                          and (number = %(number)s or %(number)s is NULL);
                   """, {'name':name, 'surname':surname, 'email':email, 'number':number})
        print(f'Найденная запись клиента:', cur.fetchall())



if __name__ == '__main__':
    with psycopg2.connect(database="clients_db", user="postgres", password="2573544") as conn:
        create_db(conn)
        add_client('Ivan', 'Ivanov', 'iivanov@ya.ru')
        add_client('Petr', 'Petrov', 'ppetrov@ya.ru')
        add_client('Nikolay', 'Petrov', 'npetrov@ya.ru')
        add_phone('777', 1)
        add_phone('888', 1)
        add_phone('999', 2)
        change_client(2, name='Степан', surname=None, email='spetrov@ya.ru')
        delete_phone(1, 777)
        delete_client(1)
        find_client(None,'Petrov', None, None)
