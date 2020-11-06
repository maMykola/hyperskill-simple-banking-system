import os, sqlite3
from random import randint
from math import ceil


class DataBase:
    def __init__(self, filename='card.s3db'):
        db_exist = os.access(filename, os.F_OK)
        self.conn = sqlite3.connect(filename)
        self.cursor = self.conn.cursor()
        if not db_exist:
            self.cursor.execute(self.table_card_create())
            self.conn.commit()

    @staticmethod
    def table_card_create():
        return """
            CREATE TABLE card (
                id INTEGER,
                number TEXT,
                pin TEXT,
                balance INTEGER DEFAULT 0
            );
            """

    def save_card(self, card):
        self.delete_card(card)
        self.insert_card(card)

    def delete_card(self, card):
        self.cursor.execute(f"""
            DELETE FROM card
            WHERE number = "{card.number}"
        """)
        self.conn.commit()

    def insert_card(self, card):
        self.cursor.execute(f"""
            INSERT INTO card (number, pin, balance)
            VALUES("{card.number}", "{card.pin}", {card.balance});
        """)
        self.conn.commit()

    def find_card_by_number(self, number):
        self.cursor.execute(f"""
            SELECT *
            FROM card
            WHERE number = "{number}"
        """)
        data = self.cursor.fetchone()

        if data:
            return Card(data[1], data[2], data[3])

        return None


class LuhnAlgorithm:
    @staticmethod
    def checksum(number):
        """calculate checksum for the given number by Luhn Algorithm"""
        digits = [int(x) for x in number]
        odd_numbers = [x * 2 for x in digits[::2]]
        even_numbers = digits[1::2]
        total = sum([x if x < 10 else x - 9 for x in odd_numbers] + even_numbers)
        return ceil(total / 10) * 10 - total

    @staticmethod
    def check_card_number(number):
        """check if the given number is valid using Luhn Algorithm"""
        return int(number[-1]) == LuhnAlgorithm.checksum(number[:-1])


class Card:

    def __init__(self, number=None, pin=None, balance=0):
        self.number = number or Card.generate_number()
        self.pin = pin or str(randint(0, 9999)).zfill(4)
        self.balance = balance

    @staticmethod
    def generate_number():
        number = '400000' + str(randint(0, 999999999)).zfill(9)
        return number + str(LuhnAlgorithm.checksum(number))

    def display_info(self):
        print("Your card number:")
        print(self.number)
        print("Your card PIN:")
        print(self.pin)

    def is_valid_pin(self, pin):
        return self.pin == pin

    def add_income(self, amount):
        self.balance += amount

    def transfer(self, amount, card):
        if self.balance < amount:
            return False

        self.balance -= amount
        card.add_income(amount)

        return True


class BankingSystem:
    STATE_GENERAL = 'general'
    STATE_ACCOUNT = 'account'
    STATE_SHUTDOWN = 'exit'

    EXIT = "0"

    CREATE = "1"
    LOGIN = "2"

    BALANCE = "1"
    ADD_INCOME = "2"
    DO_TRANSFER = "3"
    CLOSE_ACCOUNT = "4"
    LOGOUT = "5"

    ALLOWED_ACTIONS = {
        STATE_GENERAL: (CREATE, LOGIN, EXIT),
        STATE_ACCOUNT: (BALANCE, ADD_INCOME, DO_TRANSFER, CLOSE_ACCOUNT, LOGOUT, EXIT)
    }

    MESSAGES = {
        STATE_GENERAL: [
            (CREATE, "Create an account"),
            (LOGIN, "Log into account"),
            (EXIT, "Exit")
        ],
        STATE_ACCOUNT: [
            (BALANCE, "Balance"),
            (ADD_INCOME, "Add income"),
            (DO_TRANSFER, "Do transfer"),
            (CLOSE_ACCOUNT, "Close account"),
            (LOGOUT, "Log out"),
            (EXIT, "Exit")
        ]
    }

    state = STATE_GENERAL
    card = None

    def __init__(self, db):
        self.db = db

    def display(self):
        """display the proper commands that can be executed in current state"""
        for parts in self.MESSAGES[self.state]:
            print(*parts, sep='. ')

    def is_up(self):
        """Return True if banking system is working"""
        return self.state != BankingSystem.STATE_SHUTDOWN

    def do_action(self, action):
        """try to execute user selected action"""
        if action not in self.ALLOWED_ACTIONS[self.state]:
            print("Unknown action")
        elif self.state == self.STATE_GENERAL:
            self.general_action(action)
        elif self.state == self.STATE_ACCOUNT:
            self.account_action(action)

    def general_action(self, action):
        """process actions for the general menu"""
        if action == self.CREATE:
            self.create_card()
        elif action == self.LOGIN:
            self.login()
        elif action == self.EXIT:
            self.exit()

    def account_action(self, action):
        """process actions for the account menu"""
        if action == self.BALANCE:
            self.balance()
        elif action == self.ADD_INCOME:
            self.add_income()
        elif action == self.DO_TRANSFER:
            self.do_transfer()
        elif action == self.CLOSE_ACCOUNT:
            self.close_account()
        elif action == self.LOGOUT:
            self.logout()
        elif action == self.EXIT:
            self.exit()

    def create_card(self):
        """get information for the new card and add it to the database"""
        card = Card()
        self.db.save_card(card)
        print("Your card has been created")
        card.display_info()

    def balance(self):
        """display the balance for the current card"""
        print("Balance:", self.card.balance)

    def add_income(self):
        print('Enter income:')
        self.card.add_income(int(input()))
        self.db.save_card(self.card)
        print('Income was added')

    def do_transfer(self):
        print("Transfer")
        print("Enter card number:")
        number = input()
        if not LuhnAlgorithm.check_card_number(number):
            print("Probably you made mistake in card number. Please try again!")
            return

        card = self.db.find_card_by_number(number)
        if not card:
            print("Such a card does not exists.")

        print("Enter how much money you want to transfer:")
        money = int(input())
        if self.card.transfer(money, card):
            self.db.save_card(self.card)
            self.db.save_card(card)
            print("Success!")
        else:
            print("Not enough money!")

    def close_account(self):
        self.db.delete_card(self.card)
        self.state = self.STATE_GENERAL

        print("The account has been closed!")

    def login(self):
        """try to login for the card with given credentials"""
        print('Enter your card number:')
        number = input()
        print('Enter your PIN:')
        pin = input()

        card = self.db.find_card_by_number(number)
        if card and card.is_valid_pin(pin):
            self.state = self.STATE_ACCOUNT
            self.card = card
            print("You have successfully logged in!")
        else:
            print("Wrong card number or PIN!")

    def logout(self):
        """Log out from the current card"""
        self.state = self.STATE_GENERAL
        print("You have successfully logged out!")

    def exit(self):
        """shutdown the system"""
        self.state = self.STATE_SHUTDOWN
        print('Bye!')


system = BankingSystem(DataBase())

while system.is_up():
    system.display()
    system.do_action(input())
