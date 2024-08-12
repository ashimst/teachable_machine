import random
import string

#to generate event url
def generate_event_url(event_name: str) -> str:
    # Generate a random string of alphanumeric characters
    random_string = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    
    # Replace spaces in the event name with hyphens and convert to lowercase
    event_name = event_name.replace(' ', '-').lower()
    
    # Combine the event name with the random string to create the URL
    event_url = f"{event_name}-{random_string}"
    
    return event_url