

from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import (MessageEvent,
                             TextMessage,
                             TextSendMessage)

from openai import OpenAI
import time
import shelve


client = OpenAI(
  api_key="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",
)

model_use = "gpt-4-1106-preview"
channel_secret = "1985c78ee77004c9965a5cbe3d5c3e09"
channel_access_token = "SkkGnd3WPBfS1FisUNxHv7UZxu+d/m8zpFMYkA0S50OcDIkL/BY27TUrIcs8v2d7TCriPKhVOz+iDY8+VpMfKaugyYM+6kV7Y+MX3TC0e4C+biG7LbW865S8NAY8vqEKsdsZLGtfsuapEVCs/mS1JAdB04t89/1O/w1cDnyilFU="

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

app = Flask(__name__)

@app.route("/", methods=["GET","POST"])
def home():
    try:
        signature = request.headers["X-Line-Signature"]
        body = request.get_data(as_text=True)
        handler.handle(body, signature)
    except:
        pass

    return "Hello Line Chatbot6"

def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)

# Function to store a new thread ID for a given wa_id
def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id

def generate_response(message_body, wa_id, name):
    thread_id = check_if_thread_exists(wa_id)
    if thread_id is None:
        # Create a new thread and store its ID
        thread = client.beta.threads.create()
        store_thread(wa_id, thread.id)
        thread_id = thread.id
    else:
        # Use the existing thread ID
        print('------------------')
        thread = client.beta.threads.retrieve(thread_id)
        print(thread.id)

    print('+-+-+-')

    messages = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=message_body,
    )

    print(messages)
    print(thread)

    new_message = run_assistant(thread)
    return new_message

def run_assistant(thread):

    assistant = client.beta.assistants.retrieve("asst_VxLyiwJfPqYts9olDmkYzXIO")

    run = client.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id,
    )

    while run.status != "completed":
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
        print('__++++__')
        print(run.status)

    #retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    return new_message


@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):

    text = event.message.text
    wa_id = event.source.user_id
    profile = line_bot_api.get_profile(wa_id)
    user_name = profile.display_name

    print(wa_id)
    print('++++++++++++++++++++++')
    # wa_id = wa_id.userId
    print(event)
    print('--------------------')
    print(text)
    print(f"Message from {user_name} (ID: {wa_id}): {text}")

    new_message = generate_response(text,wa_id,user_name)

    line_bot_api.reply_message(event.reply_token,
                              TextSendMessage(text=new_message))



if __name__ == "__main__":
    app.run()
