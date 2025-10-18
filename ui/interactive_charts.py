"""
Интерактивные графики для PySide viewer'а
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal, Qt, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QMouseEvent
from PySide6.QtCharts import (
    QChart, QChartView, QBarSeries, QBarSet, QValueAxis, 
    QBarCategoryAxis, QLineSeries, QScatterSeries, QPieSeries, QPieSlice
)
from typing import Dict, List, Any, Optional
import math

class InteractiveBarChart(QChartView):
    """Интерактивная столбчатая диаграмма с кликабельными элементами"""
    
    barClicked = Signal(str, dict)  # signal when bar is clicked
    barHovered = Signal(str, dict)  # signal when bar is hovered
    
    def __init__(self, title: str = "Interactive Chart", parent=None):
        super().__init__(parent)
        self.chart = QChart()
        self.chart.setTitle(title)
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.setChart(self.chart)
        self.setRenderHint(QPainter.Antialiasing)
        
        self._data = {}
        self._series = QBarSeries()
        self._bars = {}  # mapping from bar index to data key
        self._hovered_bar = None
        self._selected_bar = None
        
        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)
        
    def set_data(self, data: Dict[str, Any], colors: Optional[Dict[str, QColor]] = None):
        """Установить данные для отображения"""
        self._data = data
        self.chart.removeAllSeries()
        self._series = QBarSeries()
        self._bars.clear()
        
        # Создаем бар-сеты
        for i, (key, value) in enumerate(sorted(data.items(), key=lambda x: -x[1] if isinstance(x[1], (int, float)) else 0)):
            bar_set = QBarSet(str(key))
            bar_set.append(value if isinstance(value, (int, float)) else 0)
            
            # Устанавливаем цвет
            if colors and key in colors:
                bar_set.setColor(colors[key])
            else:
                bar_set.setColor(self._get_default_color(i))
            
            # Подключаем сигналы
            bar_set.clicked.connect(lambda index, k=key: self._on_bar_clicked(k))
            
            self._series.addBarSet(bar_set)
            self._bars[i] = key
        
        self.chart.addSeries(self._series)
        self._setup_axes()
        
    def _get_default_color(self, index: int) -> QColor:
        """Получить цвет по умолчанию для индекса"""
        colors = [
            QColor(31, 119, 180),   # синий
            QColor(255, 127, 14),   # оранжевый
            QColor(44, 160, 44),    # зеленый
            QColor(214, 39, 40),    # красный
            QColor(148, 103, 189),  # фиолетовый
            QColor(140, 86, 75),    # коричневый
            QColor(227, 119, 194),  # розовый
            QColor(127, 127, 127),  # серый
        ]
        return colors[index % len(colors)]
        
    def _setup_axes(self):
        """Настройка осей"""
        axis_x = QBarCategoryAxis()
        axis_x.append([""])
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        self._series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        self._series.attachAxis(axis_y)
        axis_y.applyNiceNumbers()
        
    def _on_bar_clicked(self, key: str):
        """Обработка клика по бару"""
        self._selected_bar = key
        self.barClicked.emit(key, self._data)
        self.update()
        
    def mouseMoveEvent(self, event: QMouseEvent):
        """Обработка движения мыши для hover эффектов"""
        super().mouseMoveEvent(event)
        
        # Определяем, над каким баром находится мышь
        pos = event.position() if hasattr(event, 'position') else event.pos()
        chart_pos = self.chart.mapToValue(pos)
        
        # Простая логика определения бара (можно улучшить)
        if 0 <= chart_pos.x() < len(self._bars):
            bar_index = int(chart_pos.x())
            if bar_index in self._bars:
                key = self._bars[bar_index]
                if self._hovered_bar != key:
                    self._hovered_bar = key
                    self.barHovered.emit(key, self._data)
                    self.update()
            else:
                if self._hovered_bar:
                    self._hovered_bar = None
                    self.update()
        else:
            if self._hovered_bar:
                self._hovered_bar = None
                self.update()
                
    def paintEvent(self, event):
        """Переопределяем отрисовку для добавления hover эффектов"""
        super().paintEvent(event)
        
        if self._hovered_bar:
            painter = QPainter(self)
            painter.setPen(QPen(QColor(255, 255, 0), 3))  # Желтая рамка для hover
            
            # Находим позицию бара и рисуем рамку
            # Это упрощенная реализация - в реальности нужно точно вычислить позицию
            painter.drawRect(10, 10, 100, 20)  # Заглушка

class InteractivePieChart(QChartView):
    """Интерактивная круговая диаграмма"""
    
    sliceClicked = Signal(str, dict)
    sliceHovered = Signal(str, dict)
    
    def __init__(self, title: str = "Interactive Pie Chart", parent=None):
        super().__init__(parent)
        self.chart = QChart()
        self.chart.setTitle(title)
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.setChart(self.chart)
        self.setRenderHint(QPainter.Antialiasing)
        
        self._data = {}
        self._series = QPieSeries()
        self._slices = {}  # mapping from slice to data key
        self._hovered_slice = None
        self._selected_slice = None
        
        self.setMouseTracking(True)
        
    def set_data(self, data: Dict[str, Any], colors: Optional[Dict[str, QColor]] = None):
        """Установить данные для отображения"""
        self._data = data
        self.chart.removeAllSeries()
        self._series = QPieSeries()
        self._slices.clear()
        
        total = sum(data.values()) if data else 1
        
        for key, value in data.items():
            if total > 0:
                percentage = (value / total) * 100
                slice_item = QPieSlice(f"{key} ({percentage:.1f}%)", value)
                
                # Устанавливаем цвет
                if colors and key in colors:
                    slice_item.setColor(colors[key])
                else:
                    slice_item.setColor(self._get_default_color(len(self._slices)))
                
                slice_item.setLabelVisible(True)
                slice_item.setExploded(False)
                
                # Подключаем сигналы
                slice_item.clicked.connect(lambda checked, k=key: self._on_slice_clicked(k))
                slice_item.hovered.connect(lambda state, k=key: self._on_slice_hovered(k, state))
                
                self._series.append(slice_item)
                self._slices[slice_item] = key
        
        self.chart.addSeries(self._series)
        
    def _get_default_color(self, index: int) -> QColor:
        """Получить цвет по умолчанию"""
        colors = [
            QColor(31, 119, 180),
            QColor(255, 127, 14),
            QColor(44, 160, 44),
            QColor(214, 39, 40),
            QColor(148, 103, 189),
            QColor(140, 86, 75),
            QColor(227, 119, 194),
            QColor(127, 127, 127),
        ]
        return colors[index % len(colors)]
        
    def _on_slice_clicked(self, key: str):
        """Обработка клика по сегменту"""
        self._selected_slice = key
        self.sliceClicked.emit(key, self._data)
        self.update()
        
    def _on_slice_hovered(self, key: str, state: bool):
        """Обработка наведения на сегмент"""
        if state:
            self._hovered_slice = key
        else:
            self._hovered_slice = None
        self.sliceHovered.emit(key, self._data)
        self.update()

class InteractiveLineChart(QChartView):
    """Интерактивный линейный график"""
    
    pointClicked = Signal(int, dict)
    pointHovered = Signal(int, dict)
    
    def __init__(self, title: str = "Interactive Line Chart", parent=None):
        super().__init__(parent)
        self.chart = QChart()
        self.chart.setTitle(title)
        self.chart.setAnimationOptions(QChart.SeriesAnimations)
        self.setChart(self.chart)
        self.setRenderHint(QPainter.Antialiasing)
        
        self._data = []
        self._series = QLineSeries()
        self._hovered_point = None
        self._selected_point = None
        
        self.setMouseTracking(True)
        
    def set_data(self, data: List[tuple], color: Optional[QColor] = None):
        """Установить данные для отображения (список кортежей (x, y))"""
        self._data = data
        self.chart.removeAllSeries()
        self._series = QLineSeries()
        
        for x, y in data:
            self._series.append(x, y)
            
        if color:
            self._series.setColor(color)
            
        self._series.setMarkerSize(8)
        self._series.setPointsVisible(True)
        
        # Подключаем сигналы
        self._series.clicked.connect(self._on_point_clicked)
        self._series.hovered.connect(self._on_point_hovered)
        
        self.chart.addSeries(self._series)
        self._setup_axes()
        
    def _setup_axes(self):
        """Настройка осей"""
        axis_x = QValueAxis()
        axis_x.setTitleText("X")
        self.chart.addAxis(axis_x, Qt.AlignBottom)
        self._series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        axis_y.setTitleText("Y")
        self.chart.addAxis(axis_y, Qt.AlignLeft)
        self._series.attachAxis(axis_y)
        
        axis_x.applyNiceNumbers()
        axis_y.applyNiceNumbers()
        
    def _on_point_clicked(self, point):
        """Обработка клика по точке"""
        index = int(point.x())
        if 0 <= index < len(self._data):
            self._selected_point = index
            self.pointClicked.emit(index, dict(self._data))
            self.update()
            
    def _on_point_hovered(self, point, state):
        """Обработка наведения на точку"""
        if state:
            index = int(point.x())
            if 0 <= index < len(self._data):
                self._hovered_point = index
                self.pointHovered.emit(index, dict(self._data))
        else:
            self._hovered_point = None
        self.update()

class ChartContainer(QWidget):
    """Контейнер для интерактивных графиков с дополнительной информацией"""
    
    def __init__(self, chart_widget: QWidget, title: str = "Chart", parent=None):
        super().__init__(parent)
        self.chart_widget = chart_widget
        self.title = title
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Настройка UI"""
        layout = QVBoxLayout(self)
        
        # Заголовок
        title_label = QLabel(self.title)
        title_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 5px;")
        layout.addWidget(title_label)
        
        # График
        layout.addWidget(self.chart_widget)
        
        # Информационная панель
        self.info_panel = QLabel("Наведите мышь на элементы графика для получения информации")
        self.info_panel.setStyleSheet("font-size: 10px; color: #666; margin: 5px;")
        self.info_panel.setWordWrap(True)
        layout.addWidget(self.info_panel)
        
        # Подключаем сигналы от графика
        if hasattr(self.chart_widget, 'barClicked'):
            self.chart_widget.barClicked.connect(self._on_data_clicked)
        if hasattr(self.chart_widget, 'sliceClicked'):
            self.chart_widget.sliceClicked.connect(self._on_data_clicked)
        if hasattr(self.chart_widget, 'pointClicked'):
            self.chart_widget.pointClicked.connect(self._on_data_clicked)
            
        if hasattr(self.chart_widget, 'barHovered'):
            self.chart_widget.barHovered.connect(self._on_data_hovered)
        if hasattr(self.chart_widget, 'sliceHovered'):
            self.chart_widget.sliceHovered.connect(self._on_data_hovered)
        if hasattr(self.chart_widget, 'pointHovered'):
            self.chart_widget.pointHovered.connect(self._on_data_hovered)
            
    def _on_data_clicked(self, key, data):
        """Обработка клика по данным"""
        if isinstance(key, str):
            value = data.get(key, 0)
            self.info_panel.setText(f"Выбрано: {key} = {value}")
        else:
            self.info_panel.setText(f"Выбрана точка: {key}")
            
    def _on_data_hovered(self, key, data):
        """Обработка наведения на данные"""
        if isinstance(key, str):
            value = data.get(key, 0)
            self.info_panel.setText(f"Наведено: {key} = {value}")
        else:
            self.info_panel.setText(f"Точка: {key}")