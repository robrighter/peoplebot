
import openai
import json
import os
import google.generativeai as palm



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
        self.GPT_GOOGLE_ROLE_PROMPT = ("You're name is  "+name+". You are either speaking with a person you have never met or"
                          " continuing a conversation with an existing friend. Your goal"
                          " is to learn as much as possible about the person and be a good friend."
                          " THIS IS VERY IMPORTANT: Each time you respond only reply with a JSON object that has 4"
                          " properties: 'reply' which is your conversational reply in the conversation,"
                          " 'name' which is the name of the person you are talking to if you know it (otherwise null),"
                          " 'should_end' which is a boolean value that is true if the conversation"
                          " has come to a reasonable stopping point, and 'summary' which is a text summary of the conversation you have"
                          " had with this person so far. This summary will be used to remember details about this person the next time you speak with them."
                          )
        openai.api_key = os.getenv("OPENAI_API_KEY")
        palm.configure(api_key=os.getenv("GOOGLEPALM_API_KEY"))
        self.previous_google_summary = None
        self.determined_name = None


        self.CHAT_VENDOR = "openai"

    def parse_json(self, message):
        try:
            parsed_dict = json.loads(message)
            parsed_dict["error"] = False
        except json.JSONDecodeError:
            # Attempt to fix the JSON by appending string termination and object termination
            fixed_message = message.rstrip() + '"}'
            
            try:
                parsed_dict = json.loads(fixed_message)
                parsed_dict["error"] = False
            except json.JSONDecodeError:
                parsed_dict = {"error": True}
        return parsed_dict

    def chat_with_gpt(self, conversation_history, user_input):
        if self.CHAT_VENDOR == "google":
            return self.chat_with_google(conversation_history, user_input)
        elif self.CHAT_VENDOR == "openai":
            return self.chat_with_openai(conversation_history,user_input)

    def chat_with_openai(self, conversation_history, user_input):
        if not conversation_history:
            conversation_history.append({
                "role": "system",
                "content": self.GPT_SYSTEM_ROLE_PROMPT 
            })

        conversation_history.append({"role": "user", "content": user_input})

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation_history,
            max_tokens=350,
            n=1,
            stop=None,
            temperature=0.5,
        )
        message = response.choices[0].message["content"]
        print("GOT BACK THIS MESSAGE:")
        print(message)
        parsedDict = self.parse_json(message)
        conversation_history.append({"role": "assistant", "content": message })
        return parsedDict
    
    def make_the_google_prompt(self):
        ret = self.GPT_GOOGLE_ROLE_PROMPT
        if bool(self.determined_name):
            ret = ret + " So far you have determined that this person's name is "+ self.determined_name+"."
        else:
            ret = ret + " So far you have not determined this person's name."
        
        if bool(self.previous_google_summary):
            ret = ret + "The summary of the conversation so far is: "+self.previous_google_summary
        else:
           ret = ret + "The conversation just started."

        ret = ret + "Now continue the conversation and grow your friendship"
        return ret 

    
    def chat_with_google(self, conversation_history, user_input):
        if not conversation_history:
            conversation_history.append({
                "role": "system",
                "content": self.GPT_SYSTEM_ROLE_PROMPT 
            })
        defaults = {
            'model': 'models/text-bison-001',
            'temperature': 0.7,
            'candidate_count': 1,
            'top_k': 40,
            'top_p': 0.95,
            'max_output_tokens': 1024,
            'stop_sequences': [],
        }

        #prompt = json.dumps(conversation_history)
        prompt = self.make_the_google_prompt()
        response = palm.generate_text( **defaults ,prompt=prompt)
        message = response.result
        print("GOT BACK THIS MESSAGE:")
        print(message)
        parsedDict = self.parse_json(message)
        if parsedDict['should_end']:
            self.previous_google_summary = ""
            self.determined_name = ""
        else:
            self.previous_google_summary = parsedDict['summary']
            if bool(parsedDict['name']):
                self.determined_name = parsedDict['name']

        conversation_history.append({"role": "assistant", "content": message })
        return parsedDict

