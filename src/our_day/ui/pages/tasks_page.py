from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import *
from our_day.ui.dialogs.task_dialog import TaskDialog


class TasksPage(QWidget):
    data_changed=Signal()
    def __init__(self,repo):
        super().__init__(); self.repo=repo
        l=QVBoxLayout(self); l.setContentsMargins(36,30,36,30)
        h=QHBoxLayout(); tx=QVBoxLayout(); t=QLabel("Feladatok"); t.setObjectName("pageTitle"); s=QLabel("Esküvői checklist, határidők és prioritások."); s.setObjectName("pageSubtitle")
        tx.addWidget(t); tx.addWidget(s); add=QPushButton("+ Új feladat"); add.setObjectName("primaryButton"); add.clicked.connect(self.open_create_dialog)
        h.addLayout(tx); h.addStretch(); h.addWidget(add); l.addLayout(h)
        a=QHBoxLayout()
        for text,slot,obj in (("Szerkesztés",self._edit,"secondaryButton"),("Készre jelölés",self._done,"secondaryButton"),("Törlés",self._delete,"dangerButton")):
            b=QPushButton(text); b.setObjectName(obj); b.clicked.connect(slot); a.addWidget(b)
        a.addStretch(); l.addLayout(a)
        self.table=QTableWidget(0,6); self.table.setHorizontalHeaderLabels(["Cím","Leírás","Határidő","Prioritás","Állapot","ID"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows); self.table.setEditTriggers(QAbstractItemView.NoEditTriggers); self.table.setColumnHidden(5,True)
        self.table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch); self.table.horizontalHeader().setSectionResizeMode(1,QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._edit); l.addWidget(self.table)

    def refresh(self):
        tasks=self.repo.list_all(); self.table.setRowCount(len(tasks))
        for r,t in enumerate(tasks):
            vals=(t.title,t.description,t.due_date.strftime("%Y.%m.%d.") if t.due_date else "—",t.priority,t.status,str(t.id))
            for c,v in enumerate(vals):
                item=QTableWidgetItem(v)
                if t.status=="Elkészült":
                    f=item.font(); f.setStrikeOut(True); item.setFont(f); item.setForeground(Qt.gray)
                self.table.setItem(r,c,item)

    def open_create_dialog(self):
        d=TaskDialog(self)
        if d.exec(): self.repo.create(d.get_task()); self.data_changed.emit()

    def _id(self):
        rows=self.table.selectionModel().selectedRows()
        if not rows: QMessageBox.information(self,"Nincs kiválasztás","Válassz ki egy feladatot."); return None
        return int(self.table.item(rows[0].row(),5).text())

    def _edit(self):
        i=self._id()
        if i is None:return
        t=self.repo.get_by_id(i); d=TaskDialog(self,t)
        if d.exec(): self.repo.update(d.get_task()); self.data_changed.emit()

    def _done(self):
        i=self._id()
        if i is None:return
        t=self.repo.get_by_id(i); t.status="Elkészült"; self.repo.update(t); self.data_changed.emit()

    def _delete(self):
        i=self._id()
        if i is None:return
        if QMessageBox.question(self,"Törlés","Biztosan törlöd?",QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            self.repo.delete(i); self.data_changed.emit()
