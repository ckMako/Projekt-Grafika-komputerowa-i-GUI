"""Płótno edytora: scena z siatką (QGraphicsScene) i widok z zoomem (QGraphicsView).

Układ współrzędnych: punkt (0, 0) jest na środku sceny, oś X rośnie w prawo,
oś Y rośnie w dół (tak jak w większości bibliotek graficznych).
"""

from PySide6.QtCore import QPointF, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QGraphicsScene, QGraphicsView
from obiekt import utworz_obiekt

ROZMIAR_SIATKI = 50          # odległość między liniami siatki (w jednostkach sceny)
ROZMIAR_SCENY = 4000         # scena ma wymiary 4000 x 4000, od -2000 do +2000
ZOOM_KROK = 1.15             # o ile powiększamy / pomniejszamy jednym ruchem kółka
ZOOM_MIN = 0.2
ZOOM_MAX = 5.0


class MapScene(QGraphicsScene):
    """Scena, na której później będą leżały obiekty (drzewa, skrzynie itd.)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        pol = ROZMIAR_SCENY / 2
        self.setSceneRect(-pol, -pol, ROZMIAR_SCENY, ROZMIAR_SCENY)

        # Kolory siatki (zmienimy je przy motywach)
        self.kolor_tla = QColor("#dfe9d3")
        self.kolor_siatki = QColor("#b9c7ab")
        self.kolor_osi = QColor("#6b7d5a")

    def ustaw_kolory(self, tlo: str, siatka: str, osie: str):
        """Zmienia kolory płótna (przyda się przy motywach) i odświeża widok."""
        self.kolor_tla = QColor(tlo)
        self.kolor_siatki = QColor(siatka)
        self.kolor_osi = QColor(osie)
        self.update()

    def drawBackground(self, painter: QPainter, rect):
        """Rysuje tło i siatkę. Qt woła tę metodę samo, gdy trzeba odświeżyć widok."""
        painter.fillRect(rect, self.kolor_tla)

        # Pierwsza linia siatki "przed" widocznym obszarem (zaokrąglona w dół do kroku)
        lewo = int(rect.left()) - (int(rect.left()) % ROZMIAR_SIATKI)
        gora = int(rect.top()) - (int(rect.top()) % ROZMIAR_SIATKI)

        pioro_siatki = QPen(self.kolor_siatki)
        pioro_siatki.setWidth(0)  # 0 = zawsze linia o grubości 1 piksela (niezależnie od zoomu)
        painter.setPen(pioro_siatki)

        x = lewo
        while x < rect.right():
            painter.drawLine(x, int(rect.top()), x, int(rect.bottom()))
            x += ROZMIAR_SIATKI
        y = gora
        while y < rect.bottom():
            painter.drawLine(int(rect.left()), y, int(rect.right()), y)
            y += ROZMIAR_SIATKI

        # Osie X i Y (przechodzą przez punkt 0,0) rysujemy grubiej
        pioro_osi = QPen(self.kolor_osi)
        pioro_osi.setWidth(2)
        pioro_osi.setCosmetic(True)
        painter.setPen(pioro_osi)
        painter.drawLine(int(rect.left()), 0, int(rect.right()), 0)
        painter.drawLine(0, int(rect.top()), 0, int(rect.bottom()))


class MapView(QGraphicsView):
    """Widok sceny: zoom kółkiem myszy, przesuwanie widoku środkowym przyciskiem."""

    # Sygnały: informują okno główne (np. żeby pokazać współrzędne na pasku statusu)
    zmieniono_pozycje_myszy = Signal(float, float)   # x, y w układzie sceny
    zmieniono_zoom = Signal(float)                   # aktualny zoom (1.0 = 100%)

    def __init__(self, scena: MapScene, parent=None):
        super().__init__(scena, parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setMouseTracking(True)  # żeby dostawać ruch myszy także bez klikania
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)  # zoom w stronę kursora
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self.setDragMode(QGraphicsView.NoDrag)
        self._zoom = 1.0
        self._przesuwanie = False
        self.aktywny_obiekt = None   # nazwa z palety albo None, moze zmienimy na jakies rezerwowe ksztalty czy cos

    # ----- Zoom -----
    def wheelEvent(self, event):
        """Kółko myszy = zoom."""
        krok = ZOOM_KROK if event.angleDelta().y() > 0 else 1 / ZOOM_KROK
        self.ustaw_zoom(self._zoom * krok)

    def ustaw_zoom(self, nowy_zoom: float):
        nowy_zoom = max(ZOOM_MIN, min(ZOOM_MAX, nowy_zoom))
        wspolczynnik = nowy_zoom / self._zoom
        self.scale(wspolczynnik, wspolczynnik)
        self._zoom = nowy_zoom
        self.zmieniono_zoom.emit(self._zoom)

    def przybliz(self):
        self.ustaw_zoom(self._zoom * ZOOM_KROK)

    def oddal(self):
        self.ustaw_zoom(self._zoom / ZOOM_KROK)

    def resetuj_widok(self):
        """Zoom 100% i wyśrodkowanie na punkcie (0, 0)."""
        self.ustaw_zoom(1.0)
        self.centerOn(QPointF(0, 0))

    # ----- Przesuwanie widoku środkowym przyciskiem myszy -----
    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._przesuwanie = True
            self._ostatnia_pozycja = event.position()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return


    #akcja LMB, dodawanie itd
        if event.button() == Qt.LeftButton and self.aktywny_obiekt:
            poz = self.mapToScene(event.position().toPoint())
            item = utworz_obiekt(self.aktywny_obiekt)
            item.setPos(poz)
            self.scene().addItem(item)
            event.accept()
            return

        super().mousePressEvent(event)


    def ustaw_aktywny_obiekt(self, nazwa):
        self.aktywny_obiekt = nazwa if nazwa else None                            # zapamiętuje wybraną pozycję z palety
        self.setCursor(Qt.CrossCursor if self.aktywny_obiekt else Qt.ArrowCursor) # zmienia kursor (krzyżyk albo strzałka)

    def mouseMoveEvent(self, event):
        if self._przesuwanie:
            roznica = event.position() - self._ostatnia_pozycja
            self._ostatnia_pozycja = event.position()
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - int(roznica.x()))
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - int(roznica.y()))
            event.accept()
            return
        # Zamiana pozycji myszy z pikseli okna na współrzędne sceny
        poz = self.mapToScene(event.position().toPoint())
        self.zmieniono_pozycje_myszy.emit(poz.x(), poz.y())
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self._przesuwanie:
            self._przesuwanie = False
            # self.unsetCursor()
            self.ustaw_aktywny_obiekt(self.aktywny_obiekt)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        #usuwanie Delete-key
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            for item in self.scene().selectedItems():
                self.scene().removeItem(item)
            event.accept()
            return
        super().keyPressEvent(event)



