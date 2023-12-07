from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time

driver = webdriver.Chrome()


class OpenChat:
    @staticmethod
    def open_chat_old_acc():
        driver.find_element(By.XPATH, "//button[contains(., 'Chat')]").click()

    @staticmethod
    def open_chat_new_acc():
        driver.find_element(By.XPATH, "//span[contains(., 'Chat')]").click()


class MessageSender:

    @staticmethod
    def send_message(user, message):
        driver.execute_script(
            'var textarea = document.querySelector("body > faceplate-app > rs-app").shadowRoot.querySelector("div.container > rs-direct-chat").shadowRoot.querySelector("section > rs-message-composer").shadowRoot.querySelector("form > div > textarea");'
            'textarea.value = arguments[0];',
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

        with open('sent_messages.txt', 'a') as sent_messages_file:
            sent_messages_file.write(user + ':' + message + ';')
            sent_messages_file.close()


class ChatBot:

    def __init__(self):
        self.login()

    def login(self):
        username = 'BackgroundProper6340'
        password = 'dekasibe223'
        driver.get("https://www.reddit.com/login")
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
        time.sleep(3)
        self.load_user_page(user)
        time.sleep(3)
        OpenChat.open_chat_old_acc()
        time.sleep(6)
        self.switch_to_chat_iframe()
        time.sleep(2)
        MessageSender.send_message(user, message)
        time.sleep(2)
