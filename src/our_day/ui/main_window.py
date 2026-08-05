from PySide6.QtWidgets import QHBoxLayout,QMainWindow,QStackedWidget,QWidget
from our_day.repositories.entry_repository import EntryRepository
from our_day.repositories.task_repository import TaskRepository
from our_day.repositories.guest_repository import GuestRepository
from our_day.repositories.guest_table_repository import GuestTableRepository
from our_day.repositories.preference_repository import PreferenceRepository
from our_day.repositories.invitation_group_repository import InvitationGroupRepository
from our_day.ui.pages.dashboard_page import DashboardPage
from our_day.ui.pages.entries_page import EntriesPage
from our_day.ui.pages.tasks_page import TasksPage
from our_day.ui.pages.guests_page import GuestsPage
from our_day.ui.pages.settings_page import SettingsPage
from our_day.ui.pages.placeholder_page import PlaceholderPage
from our_day.ui.widgets.sidebar import Sidebar


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Our Day"); self.resize(1280,820)
        self.entry_repo=EntryRepository(); self.task_repo=TaskRepository(); self.guest_repo=GuestRepository(); self.table_repo=GuestTableRepository(); self.preference_repo=PreferenceRepository(); self.group_repo=InvitationGroupRepository()
        self.pages=QStackedWidget()
        self.dashboard=DashboardPage(self.entry_repo,self.task_repo,self.guest_repo)
        self.entries=EntriesPage(self.entry_repo)
        self.services=EntriesPage(self.entry_repo,"Szolgáltatások","Helyszín, fotós, zenekar és további szolgáltatók.","Szolgáltatás")
        self.tasks=TasksPage(self.task_repo)
        self.lists=GuestsPage(
            self.guest_repo,
            self.table_repo,
            self.preference_repo,
            self.group_repo,
        )
        self.settings=SettingsPage(
            self.table_repo,
            self.preference_repo,
        )
        for p in (self.dashboard,self.entries,self.services,self.tasks,self.lists,self.settings): self.pages.addWidget(p)
        self.sidebar=Sidebar(); self.sidebar.page_selected.connect(self._change)
        self.entries.data_changed.connect(self._refresh); self.services.data_changed.connect(self._refresh); self.tasks.data_changed.connect(self._refresh); self.lists.data_changed.connect(self._refresh); self.settings.data_changed.connect(self._refresh)
        self.dashboard.create_entry_requested.connect(self.entries.open_create_dialog)
        root=QWidget(); l=QHBoxLayout(root); l.setContentsMargins(0,0,0,0); l.addWidget(self.sidebar); l.addWidget(self.pages,1); self.setCentralWidget(root)
        self.setStyleSheet("""
        QWidget{font-family:'Segoe UI';font-size:14px;color:#222;background:#F6F7FB}
        QFrame#sidebar{background:white;border-right:1px solid #E7E8EE}
        QLabel#appTitle{font-size:26px;font-weight:700;background:transparent;padding:8px 4px 24px}
        QPushButton#navButton{border:none;border-radius:10px;text-align:left;padding:12px 16px;background:transparent}
        QPushButton#navButton:checked{background:#E9E3F5;color:#5B3F8C;font-weight:600}
        QLabel#pageTitle{font-size:30px;font-weight:700;background:transparent}
        QLabel#pageSubtitle{color:#707070;background:transparent}
        QLabel#sectionTitle{font-size:17px;font-weight:700;background:transparent}
        QFrame#statCard,QFrame#contentCard{background:white;border:1px solid #E7E8EE;border-radius:14px}
        QLabel#statTitle{color:#777;background:transparent} QLabel#statValue{font-size:24px;font-weight:700;background:transparent}
        QPushButton#primaryButton{background:#6B4EA0;color:white;border:none;border-radius:10px;padding:11px 18px;font-weight:600}
        QPushButton#secondaryButton{background:white;border:1px solid #D9D9DF;border-radius:9px;padding:9px 14px}
        QPushButton#dangerButton{background:#FFF1F1;color:#A32B2B;border:1px solid #EFCCCC;border-radius:9px;padding:9px 14px}
        QLineEdit,QTextEdit,QComboBox,QDoubleSpinBox,QDateEdit{background:white;color:#222;border:1px solid #D6D7DE;border-radius:9px;padding:9px}
        
        QListWidget {
            background: #FFFFFF;
            border: 1px solid #E7E8EE;
            border-radius: 10px;
            padding: 6px;
            outline: none;
        }

        QListWidget::item {
            border-radius: 8px;
            padding: 10px 12px;
            margin: 2px 0;
        }

        QListWidget::item:hover {
            background: #F4F1FA;
        }

        QListWidget::item:selected {
            background: #E9E3F5;
            color: #5B3F8C;
            font-weight: 600;
        }

        QTableWidget {
            background: #FFFFFF;
            alternate-background-color: #FAFAFC;
            border: 1px solid #E7E8EE;
            border-radius: 12px;
            gridline-color: #F0F0F3;
        }
    
        QHeaderView::section{background:#F7F7FA;padding:10px;font-weight:600}
        """)
        self._refresh()

    def _change(self,index): self.pages.setCurrentIndex(index); self._refresh()
    def _refresh(self): self.dashboard.refresh(); self.entries.refresh(); self.services.refresh(); self.tasks.refresh(); self.lists.refresh(); self.settings.refresh()
