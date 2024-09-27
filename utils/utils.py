import re
import time
    
def format_phone_number(phone_number):
    # Remove any non-digit characters
    cleaned_number = re.sub(r'\D', '', phone_number)
    
    # Check if the number already starts with +1
    if cleaned_number.startswith('1') and len(cleaned_number) == 11:
        return f'+{cleaned_number}'
    elif len(cleaned_number) == 10:
        return f'+1{cleaned_number}'
    
def get_rdbl_time():
    """Returns current time in a readable format"""
    return time.strftime("%I:%M %p, %b %d, %Y")
    