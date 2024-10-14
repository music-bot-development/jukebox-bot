import requests
import json

class message:
    def __init__(self, role, message) -> None:
        self.role = role
        self.message = message

        self.full_message = f"{self.role}: {self.message}"

class conversation:
    def __init__(self):
        self.message_list = []

    def add_message(self, msg: message):
        self.message_list.append(msg)
        return self

    def get_conversation_string(self):
        convo_str: str = ""

        for item in self.message_list:
            convo_str += item.full_message + "\n"
        return convo_str

def generate(prompt: str, prev_conversation: conversation):
    url = "http://localhost:11434/api/generate"
    headers = {
        "Content-Type": "application/json"
    }

    prompt_msg = message("User:", prompt)
    updated_conversation = prev_conversation.add_message(prompt_msg)

    data = {
        "model": "mistral:7b",
        "prompt": f"You have been talking wiht a user, this is the conversation, answer the latest message sent by the user:  {updated_conversation.get_conversation_string()}",
        "stream": False
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        data = response.json()
        actual_response = data.get("response", "No response found.")
        ai_message = message("AI:", actual_response)
        return f"You : {prompt}\n{ai_message.full_message} \n||AI's and LLM's can make mistakes, verify important info||", updated_conversation.add_message(ai_message)

    else:
        error_message = f"Error: {response.status_code} - {response.text}"
        print(error_message)