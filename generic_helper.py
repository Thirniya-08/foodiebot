import re

def get_str_from_food_dict(food_dict: dict):
    return ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])
    return result


def extract_session_id(session_str: str):

    match= re.search(r"/sessions/(.*?)/contexts/", session_str)
    if match:
        extracted_string = match.group(1)
        return extracted_string

    return ""




    #print(extract_session_id("projects/foodie-chatbot-for-food-d-oomg/agent/sessions/123/contexts/ongoing-order"))