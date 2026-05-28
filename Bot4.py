from collections import UserDict
from datetime import datetime, date, timedelta


class Field:                        # base class for Name and Phone fields
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):                  # for storing contact names
    def __init__(self, value):
        if not value.strip():
            raise ValueError("Ім'я не може бути порожнім.")
        super().__init__(value)


class Phone(Field):                 # for validation phone numbers
    def __init__(self, value):
        if not value.isdigit() or len(value) != 10:
            raise ValueError(f"Номер '{value}' невалідний. Має містити рівно 10 цифр.")
        super().__init__(value)


class Birthday(Field):              # for validation birthday dates
    def __init__(self, value):
        try:
            self.value = datetime.strptime(value, "%d.%m.%Y") # change to datetime for easier date calculations
        except ValueError:
            raise ValueError("Невірний формат дати. Використовуйте DD.MM.YYYY")

    def __str__(self):
        return self.value.strftime("%d.%m.%Y")


class Record:                       # for storing contact information
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):     # add phone to contact
        self.phones.append(Phone(phone))

    def remove_phone(self, phone):  # remove phone from contact
        target = self.find_phone(phone)
        if target:
            self.phones.remove(target)
            return True
        return False

    def edit_phone(self, old_phone, new_phone): # change phone number in contact
        target = self.find_phone(old_phone)
        if not target:
            raise ValueError(f"Телефон '{old_phone}' не знайдено у контакту.")
        index = self.phones.index(target)
        self.phones[index] = Phone(new_phone)

    def find_phone(self, phone):    # helper method to find a phone in the contact's list
        for p in self.phones:
            if p.value == phone:
                return p
        return None

    def add_birthday(self, birthday):   # add birthday to contact
        self.birthday = Birthday(birthday)

    def __str__(self):
        phones = "; ".join(p.value for p in self.phones)
        birthday = str(self.birthday) if self.birthday else "не вказано"
        return f"Ім'я: {self.name.value}, телефони: {phones}, день народження: {birthday}"


class AddressBook(UserDict):        # for storing all contacts

    def add_record(self, record):   # add new contact to the book
        self.data[record.name.value] = record

    def find(self, name):           # find contact by name
        return self.data.get(name)

    def delete(self, name):         # delete contact by name
        if name in self.data:
            del self.data[name]
            return True
        return False

    def get_upcoming_birthdays(self):   # return list of contacts with birthdays in the next 7 days, adjusting for weekends
        today = date.today()
        upcoming = []

        for record in self.data.values(): #
            if not record.birthday:
                continue

            bday = record.birthday.value.date()
            bday_this_year = bday.replace(year=today.year)

            if bday_this_year < today:
                bday_this_year = bday_this_year.replace(year=today.year + 1)

            days_until = (bday_this_year - today).days
            if 0 <= days_until <= 6:    # check if birthday is within the next 7 days
                weekday = bday_this_year.weekday()
                if weekday == 5:        # saturday
                    bday_this_year += timedelta(days=2)
                elif weekday == 6:      # sunday
                    bday_this_year += timedelta(days=1)

                upcoming.append({
                    "name": record.name.value,
                    "congratulation_date": bday_this_year.strftime("%d.%m.%Y"),
                })

        return upcoming


def input_error(func):              # decorator to handle common user input errors

    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            msg = str(e)
            if "unpack" in msg or not msg:
                return "Введіть ім'я та номер телефону."
            return msg
        except KeyError:
            return "Введіть ім'я користувача."
        except IndexError:
            return "Введіть аргумент для команди."
    return inner


def parse_input(user_input):        # parse user input into command and arguments
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, contacts):    # add new contact to the book
    name, phone, *_ = args          # ValueError if not enough arguments
    record = contacts.find(name)
    if record:                      # adding phone to existing contact
        record.add_phone(phone)
        return f"Телефон {phone} додано до контакту {name}."
    else:
        record = Record(name)       # create new contact if not exists
        record.add_phone(phone)
        contacts.add_record(record)
        return "Контакт додано."


@input_error
def change_contact(args, contacts):     # change phone number of existing contact
    name, old_phone, new_phone = args   # ValueError if not 3 arguments
    record = contacts.find(name)
    if not record:
        return "Контакт не знайдено."
    record.edit_phone(old_phone, new_phone)
    return "Контакт оновлено."


@input_error
def remove_phone(args, contacts):   # remove phone from contact
    name, phone = args              # ValueError if not 2 arguments
    record = contacts.find(name)
    if not record:
        return "Контакт не знайдено."
    if record.remove_phone(phone):
        return f"Телефон {phone} видалено."
    return f"Телефон {phone} не знайдено у контакту."


@input_error
def delete_contact(args, contacts): # delete contact completely
    name = args[0]                  # IndexError if args is empty
    if contacts.delete(name):
        return f"Контакт {name} видалено."
    return "Контакт не знайдено."


@input_error
def phone(args, contacts):          # return phone number of contact by name   
    name = args[0]                  # IndexError if args is empty
    record = contacts.find(name)
    if not record:
        return "Контакт не знайдено."
    phones = "; ".join(p.value for p in record.phones)
    return f"{record.name.value}: {phones}"


@input_error
def show_all(contacts):             # return all contacts
    if not contacts.data:
        return "Адресна книга порожня."
    return "\n".join(str(record) for record in contacts.data.values())


@input_error
def add_birthday(args, contacts):   # add birthday to contact
    name, birthday = args           # ValueError if not 2 arguments
    record = contacts.find(name)
    if not record:
        return "Контакт не знайдено."
    record.add_birthday(birthday)
    return f"День народження для {name} додано."


@input_error
def show_birthday(args, contacts):  # show birthday of contact by name
    name = args[0]                  # IndexError if args is empty
    record = contacts.find(name)
    if not record:
        return "Контакт не знайдено."
    if not record.birthday:
        return f"У контакту {name} день народження не вказано."
    return f"{name}: {record.birthday}"


@input_error
def birthdays(args, contacts):      # return birthdays of contacts in the upcoming week
    upcoming = contacts.get_upcoming_birthdays()
    if not upcoming:
        return "Найближчого тижня іменинників немає."
    return "\n".join(
        f"{item['name']}: {item['congratulation_date']}" for item in upcoming
    )


def show_help():                    # return list of available commands
    commands = [
        "hello / hi                           - привітання",
        "add <ім'я> <телефон>                 - додати контакт або телефон",
        "change <ім'я> <старий> <новий>       - змінити номер телефону",
        "remove <ім'я> <телефон>              - видалити телефон контакту",
        "delete <ім'я>                        - видалити контакт повністю",
        "phone <ім'я>                         - показати телефони контакту",
        "all                                  - показати всі контакти",
        "add-birthday <ім'я> <DD.MM.YYYY>     - додати день народження",
        "show-birthday <ім'я>                 - показати день народження",
        "birthdays                            - іменинники на наступному тижні",
        "help                                 - список команд",
        "close / exit / bye                   - завершити роботу",
    ]
    return "Доступні команди:\n" + "\n".join(commands)


def main():
    book = AddressBook()
    print("Ласкаво просимо до бота-помічника! Введіть 'help' для перегляду команд.")

    while True:
        user_input = input("Введіть команду: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit", "bye"]:
            print("До побачення!")
            break
        elif command in ["hello", "hi"]:
            print("Привіт! Як я можу допомогти?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "remove":
            print(remove_phone(args, book))
        elif command == "delete":
            print(delete_contact(args, book))
        elif command == "phone":
            print(phone(args, book))
        elif command == "all":
            print(show_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(birthdays(args, book))
        elif command == "help":
            print(show_help())
        else:
            print("Невідома команда.")


if __name__ == "__main__":
    main()
    