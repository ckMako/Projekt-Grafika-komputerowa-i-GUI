"""Obiekty, które można umieszczać na mapie."""

from pathlib import Path

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsItem, QGraphicsPixmapItem
from PySide6.QtCore import Qt  


# Folder z grafikami liczony względem tego pliku (działa niezależnie od tego, skąd uruchomisz program)
FOLDER_GRAFIK = Path(__file__).parent / "grafiki"

# nazwa w palecie -> (plik, docelowa szerokość w jednostkach sceny, pozycja z (czy podspodem))
DEFINICJE = {
    "Drzewo":   ("cactus.png", 60, 1),
    "Skrzynia": ("boxAlt.png", 40, 0),
    "Kamień":   ("rock.png", 40, 0),
    "Domek":    ("mushroomRed.png", 100, 0),
    "Woda":     ("liquidWater.png", 150, -1),
    "Ziemia":   ("grassMid.png", 150, -1),
}

# Cache: każdy plik wczytujemy z dysku tylko raz
_cache: dict[str, QPixmap] = {}


def _wczytaj(plik: str) -> QPixmap:
    if plik not in _cache:
        pix = QPixmap(str(FOLDER_GRAFIK / plik))
        if pix.isNull():
            raise FileNotFoundError(f"Nie można wczytać grafiki: {FOLDER_GRAFIK / plik}")
        _cache[plik] = pix
    return _cache[plik]




def utworz_obiekt(nazwa: str) -> QGraphicsItem:
    plik, szerokosc, z = DEFINICJE[nazwa]
    pix = _wczytaj(plik)

    item = QGraphicsPixmapItem(pix)
    item.setTransformationMode(Qt.SmoothTransformation)
    item.setOffset(-pix.width() / 2, -pix.height() / 2)   # środek obrazka w (0,0)
    item.setScale(szerokosc / pix.width())
    item.setShapeMode(QGraphicsPixmapItem.MaskShape)      # klik tylko w widoczne piksele
    item.setZValue(z)                          # pozycja z -- pod spodem


    item.setFlags(
        QGraphicsItem.ItemIsMovable
        | QGraphicsItem.ItemIsSelectable
        | QGraphicsItem.ItemSendsGeometryChanges
    )
    item.setData(0, nazwa)
    return item
