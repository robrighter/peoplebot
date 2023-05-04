
import openai
import json
import os


class ChatGPTWrap:
    def __init__(self, name='Radar'):
        self.GPT_SYSTEM_ROLE_PROMPT = ("You're name is  "+name+". You are either speaking with a person you have never met or"
                          " continuing a conversation with an existing friend. Your goal"
                          " is to learn as much as possible about the person and be a good friend."
                          " THIS IS VERY IMPORTANT: Each time you respond only reply with a JSON object that has 4"
                          " properties: 'reply' which is your conversational reply in the conversation,"
                          " 'name' which is the name of the person you are talking to if you know it (otherwise null),"
                          " 'should_end' which is a boolean value that is true if the conversation"
                          " has come to a reasonable stopping point, and 'summary' which is a full summary"
                          " of what you know about the person. This summary will be used to remember details about this"
                          " person the next time you speak with them.")
        openai.api_key = os.getenv("OPENAI_API_KEY")

        
    def chat_with_gpt(self, conversation_history, user_input):
        if not conversation_history:
            conversation_history.append({
                "role": "system",
                "content": self.GPT_SYSTEM_ROLE_PROMPT 
            })

        conversation_history.append({"role": "user", "content": user_input})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=150,
            n=1,
            stop=None,
            temperature=0.5,
        )
        message = response.choices[0].message["content"]
        print("GOT BACK THIS MESSAGE:")
        print(message)
        parsedDict = json.loads(message)
        conversation_history.append({"role": "assistant", "content": message })
        return parsedDict

