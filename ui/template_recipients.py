"""Edit saved automatic BCC recipients for a template."""
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QListWidget, QListWidgetItem, QDialogButtonBox, QLineEdit, QMessageBox)
from core.template_recipients import normalize_template_recipients
from core.send_preflight import _looks_like_email


class TemplateRecipientsDialog(QDialog):
    def __init__(self, parent, name, selected, contacts):
        super().__init__(parent)
        self.setWindowTitle('Koppla mottagare – ' + name)
        self.resize(560, 440)
        self.contacts = contacts
        layout = QVBoxLayout(self)
        info = QLabel('Spara alla mottagare för denna mall. De visas automatiskt i Bcc-listan när mallen väljs och skickas som hemliga kopior. Ta bort en sparad koppling här för att utesluta den.')
        info.setWordWrap(True)
        layout.addWidget(info)
        row = QHBoxLayout()
        self.combo = QComboBox()
        self.combo.setEditable(True)
        self.combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo.addItem('')
        for email, display in contacts:
            self.combo.addItem(f'{display} <{email}>' if display != email else email, email)
        row.addWidget(self.combo, 1)
        add = QPushButton('Lägg till adress')
        add.clicked.connect(self.add_from_combo)
        row.addWidget(add)
        layout.addLayout(row)
        addressbook = QPushButton('Adressbok…')
        addressbook.clicked.connect(self.open_address_book)
        layout.addWidget(addressbook)
        self.choices = QListWidget()
        layout.addWidget(self.choices, 1)
        for email in selected:
            self.add_email(email)
        remove = QPushButton('Ta bort markerad koppling')
        remove.clicked.connect(self.remove_selected)
        layout.addWidget(remove)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        from ui.screen_fit import fit_window
        fit_window(self)

    def add_email(self, email):
        if not _looks_like_email(email):
            return False
        if email.lower() not in {self.choices.item(i).text().lower() for i in range(self.choices.count())}:
            self.choices.addItem(email)
        return True

    def add_from_combo(self):
        text = self.combo.currentText().strip()
        index = self.combo.currentIndex()
        email = self.combo.itemData(index) if index >= 0 and text == self.combo.itemText(index) else text
        if not self.add_email(email or ''):
            QMessageBox.warning(self, 'Ogiltig e-post', 'Välj en adress eller skriv en giltig e-postadress.')
            return
        self.combo.setEditText('')

    def remove_selected(self):
        for item in self.choices.selectedItems():
            self.choices.takeItem(self.choices.row(item))

    def emails(self):
        return normalize_template_recipients({'template': [self.choices.item(i).text() for i in range(self.choices.count())]}).get('template', [])

    def open_address_book(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Adressbok – välj mallens mottagare')
        dialog.resize(520, 400)
        layout = QVBoxLayout(dialog)
        search = QLineEdit()
        search.setPlaceholderText('Sök namn eller e-post…')
        layout.addWidget(search)
        choices = QListWidget()
        for email, display in self.contacts:
            item = QListWidgetItem(f'{display} <{email}>' if display != email else email)
            item.setData(Qt.ItemDataRole.UserRole, email)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Unchecked)
            choices.addItem(item)
        layout.addWidget(choices)
        def filter_contacts(text):
            for i in range(choices.count()):
                choices.item(i).setHidden(text.casefold() not in choices.item(i).text().casefold())
        search.textChanged.connect(filter_contacts)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            for i in range(choices.count()):
                item = choices.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    self.add_email(item.data(Qt.ItemDataRole.UserRole))
