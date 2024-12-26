
from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper
app = FastAPI()

inprogress_orders= {}

@app.post("/")
async def handle_request(request: Request):
    
    payload = await request.json()
   
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_id = generic_helper.extract_session_id(output_contexts[0]['name'])

    context_name = output_contexts[0]['name'] 
    project_id = context_name.split('/')[1] 
    session_id = context_name.split('/')[3]  

    # Print the project-id and session-id to the terminal
    print(f"Project ID: {project_id}")
    print(f"Session ID: {session_id}")
    # Define a dictionary that maps intents to their corresponding handler functions
    intent_handler_dict = {
        'order.add - context: ongoing-order': add_to_order,
        'order.remove - context: ongoing-order': remove_from_order,
        'order.complete - context: ongoing-order': complete_order,
        'track.order - context: ongoing-tracking': track_order
    }

    # Call the appropriate function for the intent
    handler_function = intent_handler_dict.get(intent)
    if handler_function:
        return await handler_function(parameters, session_id)
    else:
        return JSONResponse(content={"fulfillmentText": "Sorry, I couldn't understand the request."})


async def save_to_db(order: dict):
    next_order_id = await db_helper.get_next_order_id()

    # Insert individual items along with quantity in the orders table
    for food_item, quantity in order.items():
        rcode = await db_helper.insert_order_item(food_item, quantity, next_order_id)  
        if rcode == -1:
            return -1

    # Insert order tracking status
    await db_helper.insert_order_tracking(next_order_id, "in progress")
    return next_order_id



# Complete order function
async def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = "I'm having trouble finding your order. Can you place a new one?"
    else:
        order = inprogress_orders[session_id]
        order_id = await save_to_db(order)
        if order_id == -1:
            fulfillment_text = "Sorry, we couldn't process your order due to a backend error. Please try again."
        else:
            order_total = await db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Awesome! Your order has been placed. Order ID: {order_id}. Total: {order_total}."

        # Clear the in-progress order
        del inprogress_orders[session_id]

    return JSONResponse(content={"fulfillmentText": fulfillment_text})



async def add_to_order(parameters: dict, session_id: str):
    food_items = parameters["food-item"]
    quantities = parameters["number"]

    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry, I didn't understand. Could you specify the food items and quantities clearly?"
    else:
        new_food_dict = dict(zip(food_items, quantities))

        if session_id in inprogress_orders:
            current_food_dict = inprogress_orders[session_id]
            current_food_dict.update(new_food_dict)
            inprogress_orders[session_id] = current_food_dict
        else:
            inprogress_orders[session_id] = new_food_dict

        order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
        fulfillment_text = f"So far, you have: {order_str}. Do you need anything else?"

    return JSONResponse(content={"fulfillmentText": fulfillment_text})


async def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I can't find your order. Can you place a new one?"
        })

    food_items = parameters["food-item"]
    current_order = inprogress_orders[session_id]

    removed_items = []
    no_such_items = []

    for item in food_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]

    fulfillment_text = ""
    if removed_items:
        fulfillment_text += f"Removed {', '.join(removed_items)} from your order!"
    if no_such_items:
        fulfillment_text += f" Your order doesn't have {', '.join(no_such_items)}."
    if not current_order:
        fulfillment_text += " Your order is empty!"
    else:
        order_str = generic_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f" Here's what's left in your order: {order_str}"

    return JSONResponse(content={"fulfillmentText": fulfillment_text})


async def track_order(parameters: dict, session_id: str):
    order_id = int(parameters['order_id'])
    order_status = await db_helper.get_order_status(order_id)
    if order_status:
        fulfillment_text = f"Your order status for order ID {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with ID: {order_id}"

    return JSONResponse(content={"fulfillmentText": fulfillment_text})
