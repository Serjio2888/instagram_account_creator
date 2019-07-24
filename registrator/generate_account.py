import imaplib
from time import sleep
from typing import Dict

# library import
from loguru import logger
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from insta_pb2_grpc import InstaDataStub
from serializers.serializer import GrpcSerializer
from utils.email_cheker import EmailChecker
from utils.get_identity import Identity


class AccountCreator(object):
    def __init__(
        self,
        login: str,
        password: str,
        server: str,
        quantity_account: int,
        stub: InstaDataStub,
    ):
        self.status = 0
        try:
            self.email = EmailChecker(login, password, server)
        except imaplib.IMAP4.error:
            self.status = 2

        self.account_info = Identity()
        self.count = quantity_account

        # grps task params
        self.completed = False
        self.to_abort = False
        self.task_percentage = 0

        # storage for new accounts
        self.stub = stub

        # selenium options
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        self.driver = webdriver.Chrome(chrome_options=options)

    def _get_account(self) -> Dict[str, str]:
        url = "https://www.instagram.com/?hl=en"

        # todo proxy list for create new account
        # todo add in account proxy and ip-address

        self.driver.maximize_window()
        self.driver.get(url)
        sleep(5)

        account = self.account_info.get_identity()

        action_chains = ActionChains(self.driver)
        sleep(5)

        # fill the email value
        email_field = self.driver.find_element_by_name("emailOrPhone")
        action_chains.move_to_element(email_field)
        email_field.send_keys(account.get("email"))
        logger.info(f"fill the email value {account.get('email')}")
        sleep(2)

        # fill the fullname value
        fullname_field = self.driver.find_element_by_name("fullName")
        action_chains.move_to_element(fullname_field)
        fullname_field.send_keys(account.get("name"))
        logger.info(f"fill the fullname {account.get('name')}")
        sleep(2)

        # fill username value
        username_field = self.driver.find_element_by_name("username")
        action_chains.move_to_element(username_field)
        username_field.send_keys(account.get("username"))
        logger.info(f"fill the username {account.get('username')}")
        sleep(2)

        # fill password value
        password_field = self.driver.find_element_by_name("password")
        action_chains.move_to_element(password_field)
        password_field.send_keys(account.get("password"))
        logger.info(f"fill the password {account.get('password')}")
        sleep(2)

        try:
            WebDriverWait(self.driver, 4).until(
                expected_conditions.visibility_of_element_located(
                    (By.CLASS_NAME, "coreSpriteInputError")
                )
            )
            logger.error(f"Search instagram Sprite Error")
        except TimeoutException:
            pass
        else:
            account["username"] = self.account_info._generate_new_username(
                account.get("username")
            )
            username_field = self.driver.find_element_by_name("username")
            action_chains.move_to_element(username_field)
            username_field.send_keys(account.get("username"))
            logger.info(f"fill the new username {account.get('username')}")
            sleep(2)

        finally:
            submit = self.driver.find_element_by_xpath(
                '//*[@id="react-root"]/section/main/article/div[2]/div[1]/div/form/div[7]/div/button'
            )
            action_chains.move_to_element(submit)
            sleep(2)
            submit.click()
            sleep(3)

        try:
            age_button = self.driver.find_element_by_xpath(
                "//input[@name='ageRadio' and @value='above_18']"
            )
            age_button.click()

            sleep(2)
            next_button = self.driver.find_elements_by_xpath('//button[text()="Next"]')[
                1
            ]
            next_button.click()
        except TimeoutException:
            pass

        sleep(4)

        # todo go to the mail for activate link with instagram
        # Activate the account
        confirm_link = self.email.verify_email()
        self.driver.get(confirm_link)
        self.driver.quit()

        return account

    async def get_accounts(self):
        self.task_percentage = 0
        confirmed_accounts = []
        self.to_abort = False
        for i in range(self.count):
            self.completed = False
            if not self.to_abort:
                # account = self._get_account()
                account = self.account_info.get_identity()
                confirmed_accounts.append(account)
                self.task_percentage = i / self.count * 100

        self.completed = True
        self.stub.StoreAccountCredentials(
            GrpcSerializer.prepare_new_account(confirmed_accounts)
        )
