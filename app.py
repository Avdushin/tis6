import re
import sqlite3
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QMessageBox
)

#@ ФОрма авторизации
class LoginForm(QWidget):
    def __init__(self, on_login_success, parent=None):
        super().__init__(parent)
        self.on_login_success = on_login_success
        self.phonebook_window = None

        self.setWindowTitle("Форма авторизации")

        self.username_label = QLabel("Имя:")
        self.username_entry = QLineEdit()
        self.password_label = QLabel("Пароль:")
        self.password_entry = QLineEdit()
        self.password_entry.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("Войти")
        self.login_button.clicked.connect(self.login)

        layout = QVBoxLayout()
        layout.addWidget(self.username_label)
        layout.addWidget(self.username_entry)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_entry)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def login(self):
        username = self.username_entry.text()
        password = self.password_entry.text()

        #@ Создаем БД и таблицы, если их нет
        with sqlite3.connect('phonebook.db') as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL
                )
            ''')

            cursor = conn.execute('''
                SELECT * FROM users
                WHERE username = ?
            ''', (username,))
            result = cursor.fetchone()

            if result:
                if result[2] == password:
                    if self.on_login_success:
                        self.on_login_success(username)
                else:
                    QMessageBox.warning(self, "Ошибка", "Неверный пароль.")
            else:
                conn.execute('''
                    INSERT INTO users (username, password)
                    VALUES (?, ?)
                ''', (username, password))

                #@ Успешная авторизация
                if self.on_login_success:
                    self.on_login_success(username)

#@ Телефонная книга
class PhoneBookApp(QMainWindow):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Телефонная книга")

        #@ Имя пользователя
        self.username = username

        #@ Подключение к БД
        self.conn = sqlite3.connect('phonebook.db')
        self.create_tables()

        self.contacts = []
        self.contact_list = QListWidget(self)

        self.name_label = QLabel("Имя:")
        self.name_entry = QLineEdit()
        self.phone_label = QLabel("Телефон:")
        self.phone_entry = QLineEdit()
        self.phone_entry.textChanged.connect(self.validate_phone_input)
        self.add_button = QPushButton("Добавить")
        self.add_button.clicked.connect(self.add_contact)
        self.delete_button = QPushButton("Удалить")
        self.delete_button.clicked.connect(self.delete_contact)
        self.search_button = QPushButton("Найти")
        self.search_button.clicked.connect(self.search_contact)

        self.contact_count_label = QLabel("Количество контактов: 0")

        layout = QVBoxLayout()
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_entry)
        layout.addWidget(self.phone_label)
        layout.addWidget(self.phone_entry)
        layout.addWidget(self.add_button)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.search_button)
        layout.addWidget(self.contact_list)
        layout.addWidget(self.contact_count_label)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        self.load_contacts()

    def create_tables(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL
                )
            ''')

            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''')

    def load_contacts(self):
        with self.conn:
            cursor = self.conn.execute('''
                SELECT name, phone FROM contacts
                WHERE user_id = (
                    SELECT id FROM users
                    WHERE username = ?
                )
            ''', (self.username,))

            for row in cursor.fetchall():
                contact = f"{row[0]}: {row[1]}"
                self.contacts.append(contact)
                self.contact_list.addItem(contact)

        self.update_contact_count()

    def validate_phone_input(self):
        text = self.phone_entry.text()
        valid_text = re.sub(r"[^0-9+]", "", text)
        self.phone_entry.setText(valid_text)

    def add_contact(self):
        name = self.name_entry.text()
        phone = self.phone_entry.text()
        if name and phone:
            with self.conn:
                #@ ID пользователя имени
                cursor = self.conn.execute('''
                    SELECT id FROM users
                    WHERE username = ?
                ''', (self.username,))
                user_id = cursor.fetchone()[0]

                self.conn.execute('''
                    INSERT INTO contacts (user_id, name, phone)
                    VALUES (?, ?, ?)
                ''', (user_id, name, phone))

            contact = f"{name}: {phone}"
            self.contacts.append(contact)
            self.contact_list.addItem(contact)
            self.update_contact_count()

    def delete_contact(self):
        selected_item = self.contact_list.currentItem()
        if selected_item:
            index = self.contact_list.row(selected_item)
            del self.contacts[index]
            self.contact_list.takeItem(index)
            self.update_contact_count()

    def search_contact(self):
        search_term = f"{self.name_entry.text()}: {self.phone_entry.text()}"
        for i, contact in enumerate(self.contacts):
            if search_term in contact:
                self.contact_list.setCurrentRow(i)
                return

    def update_contact_count(self):
        count = len(self.contacts)
        self.contact_count_label.setText(f"Количество контактов: {count}")

def main():
    app = QApplication([])

    def on_login_success(username):
        login_form.phonebook_window = PhoneBookApp(username)
        login_form.phonebook_window.show()

    login_form = LoginForm(on_login_success)
    login_form.show()

    app.exec_()

if __name__ == "__main__":
    main()
