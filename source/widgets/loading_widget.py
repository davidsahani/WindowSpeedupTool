from typing import override

from PyQt6.QtCore import (
    QEasingCurve,
    QParallelAnimationGroup,
    QSequentialAnimationGroup,
    Qt,
    QVariantAnimation,
)
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from utils import styles


class ArcLoader:
    def __init__(
        self,
        parent: QWidget,
        duration: int = 4000,
        close_wise: bool = True
    ) -> None:
        self.parent = parent
        self.duration = duration
        self.direction = close_wise

        self.spacer: int = 0
        self.start_angle = 270
        self.span_angle = 1 / 16
        self.fixed_start_angle = self.start_angle

    def startAnimations(self) -> None:
        seq_group = QSequentialAnimationGroup(self.parent)

        if self.direction:
            seq_group.addAnimation(self.getSpanAngleAnimation())
            seq_group.addAnimation(self.getStartAngleAnimation())
        else:
            seq_group.addAnimation(self.getStartAngleAnimation())
            seq_group.addAnimation(self.getSpanAngleAnimation())

        par_group = QParallelAnimationGroup(self.parent)
        par_group.addAnimation(self.getRotationAnimation())
        par_group.addAnimation(seq_group)
        par_group.setLoopCount(100)
        par_group.start()

    def getRotationAnimation(self) -> QVariantAnimation:
        animation = QVariantAnimation(self.parent)
        animation.setStartValue(self.spacer)
        animation.setEndValue(self.spacer + 360 * 2)
        animation.setDuration(self.duration)
        animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        animation.valueChanged.connect(self.updateSpacer)
        return animation

    def getSpanAngleAnimation(self) -> QVariantAnimation:
        animation = QVariantAnimation(self.parent)
        animation.setStartValue(1 / 16)
        animation.setEndValue(1 / 16 + 360)
        animation.setDuration(int(self.duration * 0.5))
        animation.finished.connect(self.animationFinished)
        animation.valueChanged.connect(self.updateSpanAngle)
        return animation

    def getStartAngleAnimation(self) -> QVariantAnimation:
        animation = QVariantAnimation(self.parent)
        animation.setStartValue(270)
        animation.setEndValue(270 + 360)
        animation.setDuration(int(self.duration * 0.5))
        animation.finished.connect(self.startAnimationFinished)
        animation.valueChanged.connect(self.updateStartAngle)
        return animation

    def startAnimationFinished(self) -> None:
        self.start_angle = 270
        self.fixed_start_angle = self.start_angle
        self.span_angle = 1 / 16
        self.direction = not self.direction

    def animationFinished(self) -> None:
        self.direction = not self.direction

    def updateSpacer(self, value: int) -> None:
        self.spacer = value
        self.parent.update()

    def updateStartAngle(self, value: int) -> None:
        self.start_angle = value
        self.parent.update()

    def updateSpanAngle(self, value: int) -> None:
        self.span_angle = value
        self.parent.update()


class CustomArcLoader(QFrame):
    def __init__(
            self,
            color: QColor = QColor("#ffffff"),
            arc_width: int = 20,
            parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.color = color
        self.setFixedSize(160, 160)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.initPen(arc_width)

        self.arc = ArcLoader(self)
        self.arc.startAnimations()

    def initPen(self, pen_width: int) -> None:
        self.pen = QPen()
        self.pen.setColor(self.color)
        self.pen.setWidth(pen_width)
        self.pen.setCapStyle(Qt.PenCapStyle.RoundCap)

    @override
    def paintEvent(self, a0: QPaintEvent | None) -> None:
        self.painter = QPainter(self)
        self.painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.painter.setPen(self.pen)
        self.draw()
        self.painter.end()

    def draw(self) -> None:
        x, r = self.calculateXR(1)
        arc = self.arc
        if arc.direction:
            span_angle = arc.start_angle - arc.fixed_start_angle + arc.span_angle
        else:
            span_angle = 360 - (arc.start_angle - arc.fixed_start_angle)
        if span_angle < 1 / 16:
            span_angle = 1 / 16
        self.painter.drawArc(
            x, x, r, r, -(arc.spacer + arc.start_angle) *
            16, -int(span_angle) * 16
        )
        x, r = self.calculateXR(5)
        self.painter.drawArc(
            x, x, r, r, - (arc.spacer + arc.start_angle) *
            16, (360 - int(span_angle)) * 16
        )

    def calculateXR(self, level: int) -> tuple[int, int]:
        x = self.pen.width() * level / 2
        r = self.width() - self.pen.width() * level
        return int(x), r


class LoadingWidget(QFrame):
    def __init__(self, text: str,  parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setupWidgets(text)
        self.setStyleSheet(styles.get("loading"))

    def setupWidgets(self, text: str) -> None:
        arc_loader = CustomArcLoader()
        label = QLabel(f"<p align=center>{text}</p>")

        loader_layout = QHBoxLayout()
        loader_layout.addWidget(arc_loader)
        loader_layout.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout()
        layout.addLayout(loader_layout)
        layout.addSpacing(30)
        layout.addWidget(label)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
