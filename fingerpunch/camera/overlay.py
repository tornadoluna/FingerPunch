from __future__ import annotations

from PySide6.QtCore import QPointF
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen

from fingerpunch.camera.landmarks import (
    FINGERTIP_LANDMARKS,
    DetectedHand,
    LandmarkSnapshot,
)
from fingerpunch.finger_map import Hand
from fingerpunch.ui import styles

HAND_CONNECTIONS: tuple[tuple[int, int], ...] = (
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17),
)
HAND_COLORS: dict[Hand, str] = {Hand.LEFT: styles.ACCENT, Hand.RIGHT: styles.SUCCESS}
BONE_WIDTH = 2
JOINT_RADIUS = 2.5
FINGERTIP_RADIUS = 4.5


def draw_hands(image: QImage, snapshot: LandmarkSnapshot) -> QImage:
    if not snapshot.hands:
        return image

    painted = image.copy()
    painter = QPainter(painted)
    painter.setRenderHint(QPainter.Antialiasing)
    try:
        for hand in snapshot.hands:
            _draw_hand(painter, hand, painted.width(), painted.height())
    finally:
        painter.end()
    return painted


def _draw_hand(painter: QPainter, hand: DetectedHand, width: int, height: int) -> None:
    color = QColor(HAND_COLORS.get(hand.hand, styles.ACCENT))
    points = [QPointF(point.x * width, point.y * height) for point in hand.points]

    painter.setPen(QPen(color, BONE_WIDTH))
    for start, end in HAND_CONNECTIONS:
        if start < len(points) and end < len(points):
            painter.drawLine(points[start], points[end])

    tips = set(FINGERTIP_LANDMARKS.values())
    painter.setPen(QPen(color, 1))
    painter.setBrush(QBrush(color))
    for index, point in enumerate(points):
        radius = FINGERTIP_RADIUS if index in tips else JOINT_RADIUS
        painter.drawEllipse(point, radius, radius)
