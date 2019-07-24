import email
import imaplib
import time
from itertools import chain

# library import
from bs4 import BeautifulSoup
from loguru import logger


class EmailChecker(object):
    def __init__(self, user_email: str, password: str, server: str):
        self.user_email = user_email
        self.password = password
        self.server = server  # 'smtp.gmail.com'
        self.ssl_port = 993
        self.criteria = {
            "FROM": "registrations@mail.instagram.com",
            "SUBJECT": "Welcome! Confirm your email.",
        }
        self.url_pattern = "https://instagram.com/accounts/confirm_email"

    def verify_email(self):
        time.sleep(5)
        # Waiting 5 seconds before checking email
        session = imaplib.IMAP4_SSL(self.server, self.ssl_port)
        try:
            session.login(self.user_email, self.password)
            logger.info("Logged in to: " + self.user_email)
            session.list()
            result, data = session.select("INBOX")
            if result == "OK":
                logger.info("Processing mailbox...")
                self._search_link(session)
                session.close()
            session.logout()
        except imaplib.IMAP4.error:
            logger.info(
                "Unable to login to: " + self.user_email + ". Was not verified\n"
            )

    def searching_string(self):
        """ Produce search string in IMAP format:
            e.g. (FROM "me@gmail.com" SUBJECT "abcde" ) """
        c = list(map(lambda t: (t[0], '"' + str(t[1]) + '"'), self.criteria.items()))
        return "(%s)" % " ".join(chain(*c))

    @staticmethod
    def get_html_body(email_message):
        if email_message.is_multipart():
            for payload in email_message.get_payload():
                for part in email_message.walk():
                    if (part.get_content_type() == "text/html") and (
                        part.get("Content-Disposition") is None
                    ):
                        return part.get_payload(decode=True)

    def _search_link(self, session):
        result, data = session.uid("search", None, "ALL")
        if result != "OK":
            logger.info("No message found")
            return
        else:
            start_time = time.clock()
            for num in data[0].split():
                if (time.clock() - start_time) > 30:
                    logger.info(
                        "It has been more than 30 seconds. "
                        "Please use an email address with an empty inbox."
                    )
                result, email_data = session.uid("fetch", num, "(RFC822)")

                if result != "OK":
                    logger.info("Error getting message.")
                result, email_data = session.uid("search", num, self.searching_string())

                if result != "OK":
                    logger.info("Not instagram message")
                    return

                raw_email = email_data[0][1].decode("UTF-8")
                email_message = email.message_from_string(raw_email)
                html_text = self.get_html_body(email_message)

                soup = BeautifulSoup(html_text, "html.parser")
                for i in range(len(soup.findAll("a"))):
                    one_a_tag = soup.findAll("a")[i]
                    if one_a_tag.get("href"):
                        link = one_a_tag.get("href")
                        if link.startswith(self.url_pattern):

                            session.close()
                            session.logout()

                            return link
