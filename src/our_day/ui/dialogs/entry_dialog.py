from datetime import date
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import *
from our_day.models.entry import Entry


class EntryDialog(QDialog):
    STATUSES=("Ötlet","Kapcsolatfelvétel","Ajánlatkérés","Lefoglalva","Részben fizetve","Kifizetve","Lemondva")
    def __init__(self,parent=None,entry:Entry|None=None):
        super().__init__(parent); self.entry=entry; self.resize(700,760)
        self.setWindowTitle("Szolgáltatás szerkesztése" if entry else "Új szolgáltatás")
        layout=QVBoxLayout(self); form=QFormLayout()
        self.title_input=QLineEdit(); self.description_input=QTextEdit(); self.contact_input=QLineEdit()
        self.phone_input=QLineEdit(); self.email_input=QLineEdit()
        self.deposit_input=QDoubleSpinBox(); self.total_input=QDoubleSpinBox()
        for w in (self.deposit_input,self.total_input):
            w.setRange(0,1_000_000_000); w.setDecimals(0); w.setSuffix(" Ft"); w.setGroupSeparatorShown(True)
        self.status_input=QComboBox(); self.status_input.addItems(self.STATUSES)
        self.date_controls=[]
        for _ in range(3):
            cb=QCheckBox("Megadva"); de=QDateEdit(QDate.currentDate()); de.setCalendarPopup(True); de.setDisplayFormat("yyyy.MM.dd."); de.setEnabled(False); cb.toggled.connect(de.setEnabled)
            container=QWidget(); h=QHBoxLayout(container); h.setContentsMargins(0,0,0,0); h.addWidget(cb); h.addWidget(de)
            self.date_controls.append((cb,de,container))
        fields=(("Cím *",self.title_input),("Állapot",self.status_input),("Leírás",self.description_input),
                ("Kapcsolattartó",self.contact_input),("Telefon",self.phone_input),("E-mail",self.email_input),
                ("Foglaló",self.deposit_input),("Foglaló határidő",self.date_controls[0][2]),
                ("Foglaló kifizetésének dátuma",self.date_controls[1][2]),("Teljes költség",self.total_input),
                ("Fizetési határidő",self.date_controls[2][2]))
        for l,w in fields: form.addRow(l,w)
        layout.addLayout(form)
        b=QHBoxLayout(); cancel=QPushButton("Mégse"); save=QPushButton("Mentés")
        cancel.setObjectName("secondaryButton"); save.setObjectName("primaryButton")
        cancel.clicked.connect(self.reject); save.clicked.connect(self._save); b.addStretch(); b.addWidget(cancel); b.addWidget(save); layout.addLayout(b)
        if entry: self._load(entry)

    def _load(self,e):
        self.title_input.setText(e.title); self.description_input.setPlainText(e.description); self.contact_input.setText(e.contact_name)
        self.phone_input.setText(e.phone); self.email_input.setText(e.email); self.deposit_input.setValue(e.deposit_amount)
        self.total_input.setValue(e.total_amount); self.status_input.setCurrentText(e.status)
        for value,(cb,de,_) in zip((e.deposit_due_date,e.deposit_paid_date,e.payment_due_date),self.date_controls):
            if value: cb.setChecked(True); de.setDate(QDate(value.year,value.month,value.day))

    def _save(self):
        if not self.title_input.text().strip(): QMessageBox.warning(self,"Hiányzó cím","A cím kötelező."); return
        if self.deposit_input.value()>self.total_input.value(): QMessageBox.warning(self,"Hiba","A foglaló nem lehet nagyobb a teljes összegnél."); return
        self.accept()

    def _get_date(self,index):
        cb,de,_=self.date_controls[index]
        if not cb.isChecked(): return None
        q=de.date(); return date(q.year(),q.month(),q.day())

    def get_entry(self):
        return Entry(self.entry.id if self.entry else None,"Szolgáltatás",self.title_input.text().strip(),
                     self.description_input.toPlainText().strip(),self.contact_input.text().strip(),
                     self.phone_input.text().strip(),self.email_input.text().strip(),
                     float(self.deposit_input.value()),float(self.total_input.value()),
                     self.status_input.currentText(),self._get_date(0),self._get_date(1),self._get_date(2))
