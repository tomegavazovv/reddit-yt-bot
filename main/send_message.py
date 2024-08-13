import openai
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support import expected_conditions as EC
from youtube_transcript_api import YouTubeTranscriptApi as yta


driver = webdriver.Chrome()
openai.api_key = 'key'
OPENAI_MODEL = 'text-davinci-003'


class MessageComposer:

    @staticmethod
    def get_transcript(video_id):

        data = yta.get_transcript(video_id)
        transcript = ''

        for value in data:
            for key, val in value.items():
                if key == 'text':
                    transcript += val
                    l = transcript.splitlines()

        return ' '.join(l)[:5000]

    @staticmethod
    def compose_message(transcript, user):
        system_prompt = "I would like for you to assume the role of a Cold Email Expert"
        with open('prompts/test_prompt.txt', 'r') as prompt:
            user_prompt = prompt.read()
        user_prompt = user_prompt.replace(
            '{user}', user).replace('{transcript}', transcript)

        response = openai.chat.completions.create(
            model='gpt-3.5-turbo-16k',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            max_tokens=4096,
            temperature=1
        )

        return response.choices[0].message.content

    @staticmethod
    def compose_reply_message(messages):
        system_prompt = 'I want you to act like me and respond to the message'
        user_prompt = f"""
            These are the chat messages till now: 
            Messages: {messages}
            I want you to write a response message.
            Just continue the messages, don't say hey there how are you today etc.
            The chat is about youtube video. 
            I want you to ask tell him something about the storyline, editing, and/or voiceover that you don't like.
            That he has a potential, but he needs work in some areas.
            Then ask him if the user thinks will a feedback on his video give him value?
            
            Btw, this message was already sent, which you can see from messages, then just continue the conversation.
            Tell him that I have trying to test the interest for platform dedicated to this purpose.
            Then send him a link to growtube.co, where he can learn more. Tell him that he needs some tweaks in his videos.
            
            
            Just please, just continue the conversation. Don't start again with Hey there, don't repeat anything.
            me: msg - is me
            user: msg - is the user
        """

        response = openai.chat.completions.create(
            model='gpt-3.5-turbo-16k',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': user_prompt}
            ],
            max_tokens=4096,
            temperature=1
        )

        return response.choices[0].message.content


class OpenChat:
    @staticmethod
    def open_chat_old_acc():
        driver.find_element(By.XPATH, "//button[contains(., 'Chat')]").click()

    @staticmethod
    def open_chat_new_acc():
        driver.find_element(By.XPATH, "//span[contains(., 'Chat')]").click()


class MessageSender:

    @staticmethod
    def send_message(message):

        driver.execute_script(
            'var textarea = document.querySelector("body > faceplate-app > rs-app").shadowRoot.querySelector("div.container > rs-direct-chat").shadowRoot.querySelector("section > rs-message-composer").shadowRoot.querySelector("form > div > textarea");'
            'textarea.value = arguments[0];'
            'console.log(arguments[0])',
            message
        )
        time.sleep(2)

        driver.execute_script("""
            var form = document.querySelector("body > faceplate-app > rs-app").shadowRoot.querySelector("div.container > rs-direct-chat").shadowRoot.querySelector("section > rs-message-composer").shadowRoot.querySelector("form");
            var submitButton = form.querySelector('.button-send[type="submit"]');
            submitButton.removeAttribute('disabled');
            submitButton.click();
        """)

        time.sleep(2)

    def send_message_chat_room(message):
        print(message)
        driver.execute_script(
            'var textarea = document.querySelector("body > faceplate-app > rs-app").shadowRoot.querySelector("div.container > rs-room-overlay-manager > rs-room").shadowRoot.querySelector("main > rs-message-composer").shadowRoot.querySelector("form > div > textarea");'
            'textarea.value = arguments[0];'
            'console.log(arguments[0])',
            message
        )
        time.sleep(2)
        driver.execute_script("""
            var form = document.querySelector("body > faceplate-app > rs-app").shadowRoot.querySelector("div.container > rs-room-overlay-manager > rs-room").shadowRoot.querySelector("main > rs-message-composer").shadowRoot.querySelector("form");
            var submitButton = form.querySelector('.button-send[type="submit"]');
            submitButton.removeAttribute('disabled');
            submitButton.click();
        """)


class ChatBot:

    def __init__(self):
        self.login()

    def login(self):
        username = 'username'
        password = 'password'
        driver.get("https://www.reddit.com/login")
        time.sleep(3)
        driver.find_element(By.ID, "loginUsername").send_keys(username)
        driver.find_element(By.ID, "loginPassword").send_keys(password)
        driver.find_element(By.ID, "loginPassword").send_keys(Keys.RETURN)
        time.sleep(3)

    def load_user_page(self, user):
        driver.get(f"https://www.reddit.com/user/{user}")

    def switch_to_chat_iframe(self):
        iframe = driver.find_element(
            By.CSS_SELECTOR, 'iframe[src="https://chat.reddit.com"]')
        driver.switch_to.frame(iframe)

    def send_message_old_acc(self, user, message):
        self.load_user_page(user)
        time.sleep(3)
        OpenChat.open_chat_old_acc()
        time.sleep(13)
        self.switch_to_chat_iframe()
        time.sleep(2)
        MessageSender.send_message(message)
        time.sleep(2)

    def read_messages(self, room):
        driver.get(f'https://chat.reddit.com{room}')
        time.sleep(10)
        messages = driver.execute_script(
            """ 
            timeline_events = document.querySelector("body > faceplate-app > rs-app").shadowRoot.querySelector("div.container > rs-room-overlay-manager > rs-room").shadowRoot.querySelector("main > rs-timeline").shadowRoot.querySelector("rs-virtual-scroll-dynamic").shadowRoot.querySelectorAll("rs-timeline-event");
            
            var messages = [];
            var me = true;
            timeline_events.forEach(function(message) {
                var text = message.shadowRoot.querySelector("div > div > div").innerText;
                
                if(!message.hasAttribute('compact')){
                    if(me){
                        text = '\\nme:' + text;
                    }else{
                        text = '\\nuser:' + text;
                    }
                    me = !me;
                }
                messages.push(text);
            })
            return messages
            """
        )
        return messages

    def send_follow_up(self):
        driver.get(f'https://chat.reddit.com')
        time.sleep(10)

        driver.execute_script("""
                              virtual_scroll = document.querySelector("body > faceplate-app > rs-app").shadowRoot.querySelector("div.container > rs-rooms-nav").shadowRoot.querySelector("rs-virtual-scroll");
                              virtual_scroll.setAttribute('item-height', '1');
                              """)

        js_code = """
                var rooms = document.querySelector("body > faceplate-app > rs-app").shadowRoot.querySelector("div.container > rs-rooms-nav").shadowRoot.querySelector("rs-virtual-scroll").shadowRoot.querySelectorAll("rs-rooms-nav-room");
                var roomAttributes = [];
                rooms.forEach(function(roomElement) {
                    var roomAttribute = roomElement.getAttribute('room');
                    roomAttributes.push(roomAttribute);
                });
                return roomAttributes;
                """

        rooms = driver.execute_script(js_code)

        for room in rooms:
            driver.get(f'https://chat.reddit.com/room/{room}')
            time.sleep(10)
            messages = driver.execute_script(
                'return document.querySelector("body > faceplate-app > rs-app").shadowRoot.querySelector("div.container > rs-room-overlay-manager > rs-room").shadowRoot.querySelector("main > rs-timeline").shadowRoot.querySelector("rs-virtual-scroll-dynamic").shadowRoot.querySelectorAll("rs-timeline-event");')

            if len(messages) == 1:
                MessageSender.send_message_chat_room('not for you?')

        time.sleep(5)

    def get_new_message_rooms(self):
        driver.get(
            'https://chat.reddit.com/room/!O7yxsz_jXwFalrtpACwd80XXP0ruQLb3ky0jshXiUVw%3Areddit.com')
        time.sleep(8)
        script = """
            var rooms = document.querySelector("rs-app").shadowRoot
                .querySelector("rs-rooms-nav").shadowRoot
                .querySelector("rs-virtual-scroll").shadowRoot
                .querySelectorAll("rs-rooms-nav-room");

            var result = [];

            rooms.forEach(function(room) {
                var links = room.shadowRoot.querySelectorAll("a.has-notifications");

                links.forEach(function(link) {
                    result.push(link.getAttribute('href'));
                });
            });

            return result;
            """

        href_values = driver.execute_script(script)
        return href_values

    def start(self):
        time.sleep(10)
        while True:

            for room_url in self.get_new_message_rooms():
                text = ''
                messages = self.read_messages(room_url)
                for msg in messages:
                    text = text + '\\n' + msg
                MessageSender.send_message_chat_room(
                    MessageComposer.compose_reply_message(text))

            time.sleep(30)

    def send_message_new_acc(self, user, message):
        self.load_user_page(user)
        time.sleep(3)
        OpenChat.open_chat_new_acc()
        time.sleep(6)
        driver.switch_to.window(driver.window_handles[1])
        time.sleep(3)
        MessageSender.send_message(message)
        time.sleep(2)
        driver.close()
        time.sleep(1)
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(1)

    # def extract_messages(self, user):
    #     self.load_user_page(user)
    #     time.sleep(3)
    #     OpenChat.open_chat_old_acc()
    #     time.sleep(10)
    #     self.switch_to_chat_iframe()
    #     time.sleep(2)
    #     messages = driver.execute_script(
    #         'return document.querySelector("body > faceplate-app > rs-app").shadowRoot.querySelector("div.container > rs-room-overlay-manager > rs-room").shadowRoot.querySelector("main > rs-timeline").shadowRoot.querySelector("rs-virtual-scroll-dynamic").shadowRoot.querySelectorAll("rs-timeline-event");')

    #     with open('successful_messages.txt', 'a') as f:
    #         for message in messages:
    #             f.write(message.text + ';/n')


bot = ChatBot()
bot.send_follow_up()

# bot = ChatBot()
# # bot.start()
# time.sleep(8)
# messages = bot.read_messages(
#     '/room/!Skt7gaJpLbQG8gwsnXq4TojA3SWeUX3h09HrUmVbu50%3Areddit.com')

# text = ''
# for msg in messages:
#     text = text + '\\n' + msg

# time.sleep(10)
# MessageSender.send_message_chat_room(
#     MessageComposer.compose_reply_message(text))
