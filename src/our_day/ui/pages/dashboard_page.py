from datetime import date
from PySide6.QtCore import Signal
from PySide6.QtWidgets import *
from our_day.services.formatting import format_currency
from our_day.ui.widgets.statistic_card import StatisticCard


class DashboardPage(QWidget):
    create_entry_requested=Signal()
    def __init__(self,entry_repo,task_repo):
        super().__init__(); self.entry_repo=entry_repo; self.task_repo=task_repo
        l=QVBoxLayout(self); l.setContentsMargins(36,30,36,30)
        h=QHBoxLayout(); tx=QVBoxLayout(); t=QLabel("Áttekintés"); t.setObjectName("pageTitle"); s=QLabel("Esküvői tervek, költségek és feladatok egy helyen."); s.setObjectName("pageSubtitle")
        tx.addWidget(t); tx.addWidget(s); add=QPushButton("+ Új bejegyzés"); add.setObjectName("primaryButton"); add.clicked.connect(self.create_entry_requested.emit)
        h.addLayout(tx); h.addStretch(); h.addWidget(add); l.addLayout(h)
        grid=QGridLayout()
        self.cards=[StatisticCard(x,"0") for x in ("Teljes tervezett költség","Aktív foglalók","Rendezett összegek","Fennmaradó összeg","Szolgáltatások száma","Elvégzett feladatok")]
        for i,c in enumerate(self.cards): grid.addWidget(c,i//3,i%3)
        l.addLayout(grid)
        card=QFrame(); card.setObjectName("contentCard"); cl=QVBoxLayout(card); title=QLabel("Közelgő határidők"); title.setObjectName("sectionTitle"); cl.addWidget(title); self.deadlines=QVBoxLayout(); cl.addLayout(self.deadlines); l.addWidget(card); l.addStretch()

    def refresh(self):
        s=self.entry_repo.get_financial_summary("Szolgáltatás"); entries=self.entry_repo.list_all("Szolgáltatás"); ts=self.task_repo.get_summary()
        vals=(format_currency(s["total"]),format_currency(s["deposits"]),format_currency(s["paid"]),format_currency(s["remaining"]),str(len(entries)),f"{ts['done']} / {ts['total']}")
        for c,v in zip(self.cards,vals): c.set_value(v)
        while self.deadlines.count():
            item=self.deadlines.takeAt(0); w=item.widget()
            if w:w.deleteLater()
        items=[(d["title"]+" — "+d["kind"],d["date"]) for d in self.entry_repo.get_upcoming_deadlines()]
        items += [(t.title+" — Feladat",t.due_date) for t in self.task_repo.get_upcoming()]
        if not items: self.deadlines.addWidget(QLabel("Nincs 10 napon belüli vagy lejárt határidő."))
        for text,due in sorted(items,key=lambda x:x[1]):
            days=(due-date.today()).days; label=QLabel(f"{text} | {due.strftime('%Y.%m.%d.')} | " + (f"{abs(days)} napja lejárt" if days<0 else ("Ma esedékes" if days==0 else f"{days} nap múlva")))
            label.setStyleSheet("padding:10px;background:#FFF9E8;border:1px solid #E8D79A;border-radius:8px;")
            self.deadlines.addWidget(label)
