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
# Async function to get price for item
async def get_price_for_item(food_item: str):
    try:
        async with await get_db_connection() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT price FROM food_items WHERE name = %s", (food_item,))
                result = await cursor.fetchone()
        return result[0] if result else -1  # Return -1 if item not found
    except Exception as e:
        print(f"Error fetching price for {food_item}: {e}")
        return -1

# Async function to get total price for order
async def get_total_order_price(order_id: int):
    try:
        async with await get_db_connection() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    "SELECT SUM(o.quantity * f.price) FROM orders o "
                    "JOIN food_items f ON o.item_id = f.item_id "
                    "WHERE o.order_id = %s", (order_id,)
                )
                result = await cursor.fetchone()
        return result[0] if result else -1  # Return -1 if no order found
    except Exception as e:
        print(f"Error fetching total price for order {order_id}: {e}")
        return -1

# Async function to insert order item
async def insert_order_item(food_item: str, quantity: int, order_id: int):
    try:
        async with await get_db_connection() as connection:
            async with connection.cursor() as cursor:
                # Get item_id and price for the food item
                await cursor.execute("SELECT item_id FROM food_items WHERE name = %s", (food_item,))
                item_id_result = await cursor.fetchone()
                if item_id_result is None:
                    print(f"Item {food_item} not found!")
                    return -1  # If item not found, return error code

                item_id = item_id_result[0]
                price = await get_price_for_item(food_item)  # Get the price from the earlier function

                if price == -1:
                    print(f"Item {food_item} not found!")
                    return -1  # If price is -1, the item doesn't exist

                # Calculate total price
                total_price = price * quantity

                # Insert order item into the orders table
                await cursor.execute(
                    "INSERT INTO orders (order_id, item_id, quantity, total_price) "
                    "VALUES (%s, %s, %s, %s)",
                    (order_id, item_id, quantity, total_price)
                )
            await connection.commit()
        return 0  # success
    except Exception as e:
        print(f"Error inserting order item: {e}")
        return -1  # error

# Async function to get a list of food items
async def get_food_items():
    try:
        async with await get_db_connection() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT * FROM food_items")
                food_items = await cursor.fetchall()
        return food_items
    except Exception as e:
        print(f"Error fetching food items: {e}")
        return None

async def insert_order_tracking(order_id: int, status: str):
    try:
        async with await get_db_connection() as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(
                    "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)",
                    (order_id, status)
                )
            await connection.commit()
    except Exception as e:
        print(f"Error inserting order tracking: {e}")

async def get_order_status(order_id: int):
    async with await get_db_connection() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute(
                "SELECT status FROM order_tracking WHERE order_id = %s",
                (order_id,)
            )
            result = await cursor.fetchone()
    return result[0] if result else None

# Async function to get the next order ID
async def get_next_order_id():
    async with await get_db_connection() as connection:
        async with connection.cursor() as cursor:
            await cursor.execute("SELECT MAX(order_id) FROM orders")
            result = await cursor.fetchone()
            max_order_id = result[0] if result else None
    return max_order_id + 1 if max_order_id else 1

          
    return result[0] if result else 0
