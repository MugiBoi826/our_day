from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import *
from our_day.repositories.entry_repository import EntryRepository
from our_day.services.formatting import format_currency
from our_day.ui.dialogs.entry_dialog import EntryDialog


class EntriesPage(QWidget):
    data_changed=Signal()
    def __init__(self,repo,title="Bejegyzések",subtitle="Az összes rögzített esküvői bejegyzés.",entry_type_filter=None):
        super().__init__(); self.repo=repo; self.filter=entry_type_filter
        l=QVBoxLayout(self); l.setContentsMargins(36,30,36,30)
        h=QHBoxLayout(); tx=QVBoxLayout(); t=QLabel(title); t.setObjectName("pageTitle"); s=QLabel(subtitle); s.setObjectName("pageSubtitle")
        tx.addWidget(t); tx.addWidget(s); add=QPushButton("+ Új szolgáltatás"); add.setObjectName("primaryButton"); add.clicked.connect(self.open_create_dialog)
        h.addLayout(tx); h.addStretch(); h.addWidget(add); l.addLayout(h)
        a=QHBoxLayout()
        for text,slot,obj in (("Szerkesztés",self._edit,"secondaryButton"),("Törlés",self._delete,"dangerButton")):
            b=QPushButton(text); b.setObjectName(obj); b.clicked.connect(slot); a.addWidget(b)
        a.addStretch(); l.addLayout(a)
        self.table=QTableWidget(0,8); self.table.setHorizontalHeaderLabels(["Cím","Állapot","Kapcsolattartó","Foglaló","Teljes","Fennmaradó","Határidő","ID"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setEditTriggers(QAbstractItemView.NoEditTriggers); self.table.setColumnHidden(7,True)
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch); self.table.doubleClicked.connect(self._edit); l.addWidget(self.table)

    def refresh(self):
        entries=self.repo.list_all(self.filter); self.table.setRowCount(len(entries))
        for r,e in enumerate(entries):
            vals=(e.title,e.status,e.contact_name,format_currency(e.deposit_amount),format_currency(e.total_amount),
                  format_currency(e.remaining_amount),e.payment_due_date.strftime("%Y.%m.%d.") if e.payment_due_date else "—",str(e.id))
            for c,v in enumerate(vals): self.table.setItem(r,c,QTableWidgetItem(v))

    def open_create_dialog(self):
        d=EntryDialog(self)
        if d.exec(): self.repo.create(d.get_entry()); self.data_changed.emit()

    def _id(self):
        rows=self.table.selectionModel().selectedRows()
        if not rows: QMessageBox.information(self,"Nincs kiválasztás","Válassz ki egy sort."); return None
        return int(self.table.item(rows[0].row(),7).text())

    def _edit(self):
        i=self._id()
        if i is None:return
        e=self.repo.get_by_id(i); d=EntryDialog(self,e)
        if d.exec(): self.repo.update(d.get_entry()); self.data_changed.emit()

    def _delete(self):
        i=self._id()
        if i is None:return
        if QMessageBox.question(self,"Törlés","Biztosan törlöd?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            self.repo.delete(i); self.data_changed.emit()
