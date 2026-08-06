from PySide6.QtWidgets import QFileDialog,QHBoxLayout,QMainWindow,QMessageBox,QStackedWidget,QWidget
from our_day.repositories.entry_repository import EntryRepository
from our_day.repositories.task_repository import TaskRepository
from our_day.repositories.guest_repository import GuestRepository
from our_day.repositories.guest_table_repository import GuestTableRepository
from our_day.repositories.preference_repository import PreferenceRepository
from our_day.repositories.invitation_group_repository import InvitationGroupRepository
from our_day.repositories.wedding_repository import WeddingRepository
from our_day.ui.pages.dashboard_page import DashboardPage
from our_day.ui.pages.entries_page import EntriesPage
from our_day.ui.pages.tasks_page import TasksPage
from our_day.ui.pages.guests_page import GuestsPage
from our_day.ui.pages.settings_page import SettingsPage
from our_day.ui.pages.statistics_page import StatisticsPage
from our_day.ui.pages.seating_page import SeatingPage
from our_day.ui.pages.placeholder_page import PlaceholderPage
from our_day.ui.widgets.sidebar import Sidebar
from our_day.services.database_service import DatabaseService


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__(); self.setWindowTitle("Our Day"); self.resize(1280,820)
        self.entry_repo=EntryRepository(); self.task_repo=TaskRepository(); self.guest_repo=GuestRepository(); self.table_repo=GuestTableRepository(); self.preference_repo=PreferenceRepository(); self.group_repo=InvitationGroupRepository(); self.wedding_repo=WeddingRepository()
        self.pages=QStackedWidget()
        self.dashboard=DashboardPage(
            self.entry_repo,
            self.task_repo,
            self.guest_repo,
            self.group_repo,
            self.wedding_repo,
        )
        self.entries=EntriesPage(self.entry_repo)
        self.services=EntriesPage(self.entry_repo,"Szolgáltatások","Helyszín, fotós, zenekar és további szolgáltatók.","Szolgáltatás")
        self.tasks=TasksPage(self.task_repo)
        self.lists=GuestsPage(
            self.guest_repo,
            self.table_repo,
            self.preference_repo,
            self.group_repo,
        )
        self.seating=SeatingPage(
            self.guest_repo,
            self.table_repo,
            self.preference_repo,
        )
        self.statistics=StatisticsPage(
            self.guest_repo,
            self.group_repo,
        )
        self.settings=SettingsPage(
            self.table_repo,
            self.preference_repo,
            self.wedding_repo,
        )
        for p in (self.dashboard,self.entries,self.services,self.tasks,self.lists,self.seating,self.statistics,self.settings): self.pages.addWidget(p)
        self.sidebar=Sidebar(); self.sidebar.page_selected.connect(self._change)
        self.entries.data_changed.connect(self._refresh); self.services.data_changed.connect(self._refresh); self.tasks.data_changed.connect(self._refresh); self.lists.data_changed.connect(self._refresh); self.seating.data_changed.connect(self._refresh); self.settings.data_changed.connect(self._refresh)
        self.dashboard.create_service_requested.connect(
            self.services.open_create_dialog
        )
        self.dashboard.create_task_requested.connect(
            self.tasks.open_create_dialog
        )
        self.dashboard.create_guest_requested.connect(
            self.lists._create_guest
        )
        self.dashboard.create_group_requested.connect(
            self.lists._create_group
        )
        self.dashboard.export_guests_requested.connect(
            self.lists._export_excel
        )
        self.dashboard.backup_requested.connect(
            self._create_dashboard_backup
        )
        self.dashboard.open_page_requested.connect(
            self._change
        )
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
        QFrame#weddingHero{background:#F1ECFA;border:1px solid #D8C8EF;border-radius:18px}
        QLabel#weddingTitle{font-size:30px;font-weight:700;color:#4F347D;background:transparent}
        QLabel#weddingCountdown{font-size:17px;font-weight:600;color:#6B4EA0;background:transparent}
        QLabel#weddingLocation{color:#6F6480;background:transparent}
        QLabel#weddingProgress{color:#5F5470;background:transparent;font-weight:500}
        QLabel#dashboardDetail{background:transparent;font-size:15px;line-height:1.4}
        QLabel#emptyState{background:#FAFAFC;color:#73737A;border:1px dashed #D8D8DF;border-radius:10px;padding:14px}
        QLabel#alertBadge{background:#FFF0F0;color:#B42318;border:1px solid #E8B6B6;border-radius:14px;padding:4px 8px;font-weight:700}
        QFrame#timelineItem{background:#FAFAFC;border:1px solid #ECECF1;border-radius:10px}
        QFrame#seatingTableCard{background:white;border:1px solid #E1E1E8;border-radius:14px}
        QLabel#seatingTableTitle{font-size:18px;font-weight:700;background:transparent}
        QLabel#successBadge{background:#ECFDF3;color:#067647;border:1px solid #ABEFC6;border-radius:10px;padding:4px 8px;font-weight:650}
        QLabel#warningBadge{background:#FFF8E1;color:#8A6500;border:1px solid #E9D58A;border-radius:10px;padding:4px 8px;font-weight:650}
        QLabel#dangerBadge{background:#FFF0F0;color:#B42318;border:1px solid #E8B6B6;border-radius:10px;padding:4px 8px;font-weight:650}
        QLabel#seatingWarnings{background:#FFF8E1;color:#735A00;border:1px solid #E9D58A;border-radius:10px;padding:10px;font-weight:600}
        QProgressBar#seatingProgress::chunk{background:#6B4EA0;border-radius:6px}
        QProgressBar#dangerProgress::chunk{background:#C83E3E;border-radius:6px}
        QLabel#timelineDate{background:#EEEAF5;color:#5B3F8C;border-radius:8px;padding:8px 5px;font-weight:700}
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
    
        
        QHeaderView::section {
            background: #F7F7FA;
            padding: 10px;
            font-weight: 600;
            border: none;
            border-bottom: 1px solid #E7E8EE;
        }

        QProgressBar {
            background: #EEEAF5;
            border: none;
            border-radius: 10px;
            text-align: center;
            color: #4B3A64;
            font-weight: 600;
        }

        QProgressBar::chunk {
            background: #6B4EA0;
            border-radius: 10px;
        }
    
        """)
        self._refresh()

    def _change(self, index):
        self.pages.setCurrentIndex(index)
        self._refresh()

    def _create_dashboard_backup(self):
        default_name = (
            f"our_day_backup_{__import__('datetime').date.today().isoformat()}.db"
        )
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Biztonsági mentés készítése",
            default_name,
            "Our Day adatbázis (*.db)",
        )
        if not file_path:
            return
        try:
            exported = DatabaseService.export_database(file_path)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Mentési hiba",
                f"A biztonsági mentés nem sikerült.\n\n{error}",
            )
            return
        QMessageBox.information(
            self,
            "Biztonsági mentés elkészült",
            f"Az adatbázis mentése elkészült:\n{exported}",
        )

    def _refresh(self):
        self.dashboard.refresh()
        self.entries.refresh()
        self.services.refresh()
        self.tasks.refresh()
        self.lists.refresh()
        self.seating.refresh()
        self.statistics.refresh()
        self.settings.refresh()
