from datetime import date
from PySide6.QtCore import QDate
from PySide6.QtWidgets import *
from our_day.models.task import Task


class TaskDialog(QDialog):
    def __init__(self, parent=None, task: Task|None=None):
        super().__init__(parent); self.task=task
        self.setWindowTitle("Feladat szerkesztése" if task else "Új feladat")
        self.resize(600,520)
        layout=QVBoxLayout(self); layout.setContentsMargins(26,24,26,20)
        title=QLabel(self.windowTitle()); title.setObjectName("pageTitle"); layout.addWidget(title)
        form=QFormLayout()
        self.title_input=QLineEdit(); self.description_input=QTextEdit()
        self.due_enabled=QCheckBox("Megadva"); self.due_input=QDateEdit(QDate.currentDate())
        self.due_input.setCalendarPopup(True); self.due_input.setDisplayFormat("yyyy.MM.dd."); self.due_input.setEnabled(False)
        self.due_enabled.toggled.connect(self.due_input.setEnabled)
        due=QWidget(); dlay=QHBoxLayout(due); dlay.setContentsMargins(0,0,0,0); dlay.addWidget(self.due_enabled); dlay.addWidget(self.due_input)
        self.priority_input=QComboBox(); self.priority_input.addItems(("Alacsony","Közepes","Magas"))
        self.status_input=QComboBox(); self.status_input.addItems(("Teendő","Folyamatban","Elkészült"))
        for label,w in (("Cím *",self.title_input),("Leírás",self.description_input),("Határidő",due),("Prioritás",self.priority_input),("Állapot",self.status_input)): form.addRow(label,w)
        layout.addLayout(form)
        buttons=QHBoxLayout(); cancel=QPushButton("Mégse"); save=QPushButton("Mentés")
        cancel.setObjectName("secondaryButton"); save.setObjectName("primaryButton")
        cancel.clicked.connect(self.reject); save.clicked.connect(self._save)
        buttons.addStretch(); buttons.addWidget(cancel); buttons.addWidget(save); layout.addLayout(buttons)
        if task:
            self.title_input.setText(task.title); self.description_input.setPlainText(task.description)
            self.priority_input.setCurrentText(task.priority); self.status_input.setCurrentText(task.status)
            if task.due_date:
                self.due_enabled.setChecked(True); self.due_input.setDate(QDate(task.due_date.year,task.due_date.month,task.due_date.day))

    def _save(self):
        if not self.title_input.text().strip():
            QMessageBox.warning(self,"Hiányzó cím","A cím kötelező."); return
        self.accept()

    def get_task(self):
        due=None
        if self.due_enabled.isChecked():
            q=self.due_input.date(); due=date(q.year(),q.month(),q.day())
        return Task(self.task.id if self.task else None,self.title_input.text().strip(),
                    self.description_input.toPlainText().strip(),due,
                    self.priority_input.currentText(),self.status_input.currentText())
