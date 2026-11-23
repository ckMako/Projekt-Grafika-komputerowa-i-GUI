"""Główne okno aplikacji: menu, pasek narzędzi, panele boczne, płótno, pasek statusu."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDockWidget,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QWidget,
)

from canvas import MapScene, MapView

# Obiekty z palety (na razie tylko nazwy, w kolejnym etapie dojdą klasy i grafiki)
OBIEKTY_PALETY = ["Drzewo", "Skrzynia", "Kamień", "Domek", "Woda", "Ziemia"]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Edytor map 2D")
        self.resize(1200, 750)

        # Płótno (scena + widok) jako centralny element okna
        self.scena = MapScene()
        self.widok = MapView(self.scena)
        self.setCentralWidget(self.widok)

        self._utworz_akcje()
        self._utworz_menu()
        self._utworz_pasek_narzedzi()
        self._utworz_panel_obiektow()
        self._utworz_panel_wlasciwosci()
        self._utworz_pasek_statusu()

        # Łączymy sygnały widoku z paskiem statusu
        self.widok.zmieniono_pozycje_myszy.connect(self._pokaz_pozycje)
        self.widok.zmieniono_zoom.connect(self._pokaz_zoom)

        self.widok.resetuj_widok()

    # ------------------------------------------------------------------
    # Akcje (polecenia, które można wywołać z menu, paska narzędzi lub skrótem)
    # ------------------------------------------------------------------
    def _utworz_akcje(self):
        self.akcja_nowy = QAction("Nowy projekt", self)
        self.akcja_nowy.setShortcut(QKeySequence.New)  # Ctrl+N
        self.akcja_nowy.triggered.connect(self._nowy_projekt)

        self.akcja_wyjscie = QAction("Zakończ", self)
        self.akcja_wyjscie.setShortcut(QKeySequence.Quit)  # Ctrl+Q
        self.akcja_wyjscie.triggered.connect(self.close)

        self.akcja_przybliz = QAction("Przybliż", self)
        self.akcja_przybliz.setShortcut(QKeySequence.ZoomIn)  # Ctrl++
        self.akcja_przybliz.triggered.connect(self.widok.przybliz)

        self.akcja_oddal = QAction("Oddal", self)
        self.akcja_oddal.setShortcut(QKeySequence.ZoomOut)  # Ctrl+-
        self.akcja_oddal.triggered.connect(self.widok.oddal)

        self.akcja_reset = QAction("Resetuj widok", self)
        self.akcja_reset.setShortcut("Ctrl+0")
        self.akcja_reset.triggered.connect(self.widok.resetuj_widok)

        self.akcja_o_programie = QAction("O programie", self)
        self.akcja_o_programie.triggered.connect(self._o_programie)

    #akcja esc
        self.akcja_anuluj = QAction("Anuluj narzędzie", self)
        self.akcja_anuluj.setShortcut(QKeySequence(Qt.Key_Escape)) #klawisz esc
        self.akcja_anuluj.triggered.connect(self._anuluj_narzedzie)
        self.addAction(self.akcja_anuluj)   # skrót działa, mimo że akcji nie ma w menu

    def _utworz_menu(self):
        menu_plik = self.menuBar().addMenu("&Plik")
        menu_plik.addAction(self.akcja_nowy)
        menu_plik.addSeparator()
        menu_plik.addAction(self.akcja_wyjscie)

        menu_widok = self.menuBar().addMenu("&Widok")
        menu_widok.addAction(self.akcja_przybliz)
        menu_widok.addAction(self.akcja_oddal)
        menu_widok.addAction(self.akcja_reset)

        menu_pomoc = self.menuBar().addMenu("P&omoc")
        menu_pomoc.addAction(self.akcja_o_programie)

    def _utworz_pasek_narzedzi(self):
        pasek = self.addToolBar("Narzędzia")
        pasek.setMovable(False)
        pasek.addAction(self.akcja_nowy)
        pasek.addSeparator()
        pasek.addAction(self.akcja_przybliz)
        pasek.addAction(self.akcja_oddal)
        pasek.addAction(self.akcja_reset)

    # ------------------------------------------------------------------
    # Panele boczne
    # ------------------------------------------------------------------
    def _utworz_panel_obiektow(self):
        """Lewy panel z paletą obiektów (na razie sama lista, bez działania)."""

        self.lista_obiektow = QListWidget()
        self.lista_obiektow.addItems(OBIEKTY_PALETY)

       # gdy zmieni się wybrana pozycja na liście, powiadom widok o nazwie obiektu
        self.lista_obiektow.currentTextChanged.connect(self.widok.ustaw_aktywny_obiekt)

        panel = QDockWidget("Obiekty", self)
        panel.setWidget(self.lista_obiektow)
        panel.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.LeftDockWidgetArea, panel)

    def _utworz_panel_wlasciwosci(self):
        """Prawy panel z właściwościami zaznaczonego obiektu (na razie nieaktywny)."""
        formularz = QFormLayout()
        self.pole_x = QDoubleSpinBox()
        self.pole_y = QDoubleSpinBox()
        self.pole_skala = QDoubleSpinBox()
        self.pole_obrot = QDoubleSpinBox()
        for pole in (self.pole_x, self.pole_y):
            pole.setRange(-2000, 2000)
        self.pole_skala.setRange(0.1, 10)
        self.pole_skala.setValue(1.0)
        self.pole_obrot.setRange(-360, 360)
        formularz.addRow("X:", self.pole_x)
        formularz.addRow("Y:", self.pole_y)
        formularz.addRow("Skala:", self.pole_skala)
        formularz.addRow("Obrót (°):", self.pole_obrot)

        zawartosc = QWidget()
        zawartosc.setLayout(formularz)
        zawartosc.setEnabled(False)  # włączymy, gdy będzie można zaznaczać obiekty

        panel = QDockWidget("Właściwości", self)
        panel.setWidget(zawartosc)
        panel.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.addDockWidget(Qt.RightDockWidgetArea, panel)

    # ------------------------------------------------------------------
    # Pasek statusu
    # ------------------------------------------------------------------
    def _utworz_pasek_statusu(self):
        self.etykieta_pozycji = QLabel("x: 0   y: 0")
        self.etykieta_zoomu = QLabel("Zoom: 100%")
        self.statusBar().addPermanentWidget(self.etykieta_pozycji)
        self.statusBar().addPermanentWidget(self.etykieta_zoomu)
        self.statusBar().showMessage("Kółko myszy: zoom, środkowy przycisk: przesuwanie widoku")

    def _pokaz_pozycje(self, x: float, y: float):
        self.etykieta_pozycji.setText(f"x: {x:.0f}   y: {y:.0f}")

    def _pokaz_zoom(self, zoom: float):
        self.etykieta_zoomu.setText(f"Zoom: {zoom * 100:.0f}%")

    # ------------------------------------------------------------------
    # Funkcje poleceń
    # ------------------------------------------------------------------
    def _nowy_projekt(self):
        """Na razie tylko czyści scenę i resetuje widok. Później dojdzie pytanie o zapis."""
        self.scena.clear()
        self.widok.resetuj_widok()

    def _o_programie(self):
        QMessageBox.about(
            self,
            "O programie",
            "Edytor map 2D\nProjekt z przedmiotu Grafika Komputerowa i GUI.\n"
            "Python + PySide6 (Qt).",
        )



    def _anuluj_narzedzie(self):
        """Wyłącza narzędzie z palety (wywoływane klawiszem Esc)."""
        # zdejmij podświetlenie z pozycji na liście
        self.lista_obiektow.clearSelection()
        # brak bieżącej pozycji (-1), co wysyła sygnał currentTextChanged z pustym tekstem
        self.lista_obiektow.setCurrentRow(-1)
        # widok przestaje stawiać obiekty, a lewy klik znów zaznacza i przesuwa
        self.widok.ustaw_aktywny_obiekt(None)