import mysql.connector
import os
from dotenv import load_dotenv


load_dotenv()

# Fetch the values from the .env file
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
PORT = int(os.getenv("PORT"))


def get_db_connection():
    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=PORT
    )
    return connection

async def get_next_order_id():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT MAX(order_id) FROM orders")
    max_order_id = cursor.fetchone()[0]
    connection.close()
    return max_order_id + 1 if max_order_id else 1

async def insert_order_item(food_item: str, quantity: int, order_id: int):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO orders (item_id, quantity, total_price, order_id) "
            "SELECT item_id, %s, (f.price * %s), %s FROM food_items f WHERE f.name = %s",
            (quantity, quantity, order_id, food_item)
        )
        connection.commit()
        connection.close()
        return 0  # success
    except Exception as e:
        print(f"Error inserting order item: {e}")
        return -1  # error


async def insert_order_tracking(order_id: int, status: str):
    try:
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)",
            (order_id, status)
        )
        connection.commit()
        connection.close()
    except Exception as e:
        print(f"Error inserting order tracking: {e}")

async def get_order_status(order_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT status FROM order_tracking WHERE order_id = %s", (order_id,))
    result = cursor.fetchone()
    connection.close()
    return result[0] if result else None


async def get_total_order_price(order_id: int):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        "SELECT SUM(o.quantity * f.price) FROM orders o "
        "JOIN food_items f ON o.item_id = f.item_id "
        "WHERE o.order_id = %s", (order_id,)
    )
    result = cursor.fetchone()
    connection.close()
    return result[0] if result else 0
