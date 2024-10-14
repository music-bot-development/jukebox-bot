from ollama import generate

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



def generate_answer(prompt: str, prev_conversation: conversation, username: str, botuser: str):
    answer = ""
    for part in generate('mistral:7b', f'This has been the previous conversation: {prev_conversation.get_conversation_string()}. Answer this in a short, elegant way: {prompt}', stream=True):
        answer += part['response']
    
    ai_message = message(f"{username}:{prompt}\n\n{botuser}", answer + "\n\n||AI's and LLM's can make mistakes, verify important info||")
    
    updated_conversation = prev_conversation.add_message(ai_message)
    
    return ai_message.full_message, updated_conversation 
