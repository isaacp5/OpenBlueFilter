from PyQt6.QtWidgets import QWidget, QSlider, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal

class LabeledSlider(QWidget):
    valueChanged = pyqtSignal(int)
    
    def __init__(self, label_text, min_value=0, max_value=100, initial_value=50, parent=None):
        super().__init__(parent)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        self.label = QLabel(label_text)
        main_layout.addWidget(self.label)
        
        # Slider and value display layout
        slider_layout = QHBoxLayout()
        
        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(min_value)
        self.slider.setMaximum(max_value)
        self.slider.setValue(initial_value)
        self.slider.valueChanged.connect(self._on_value_changed)
        slider_layout.addWidget(self.slider, 4)
        
        # Value display
        self.value_label = QLabel(str(initial_value))
        self.value_label.setMinimumWidth(40)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        slider_layout.addWidget(self.value_label, 1)
        
        main_layout.addLayout(slider_layout)
        self.setLayout(main_layout)
    
    def _on_value_changed(self, value):
        self.value_label.setText(str(value))
        self.valueChanged.emit(value)
    
    def value(self):
        return self.slider.value()
    
    def setValue(self, value):
        self.slider.setValue(value)
    
    def setRange(self, min_value, max_value):
        self.slider.setMinimum(min_value)
        self.slider.setMaximum(max_value)


class PercentageSlider(LabeledSlider):
    valueChangedFloat = pyqtSignal(float)
    
    def __init__(self, label_text, min_percent=0, max_percent=100, initial_percent=50, parent=None):
        super().__init__(label_text, min_percent, max_percent, initial_percent, parent)
        self.value_label.setText(f"{initial_percent}%")
        self.slider.valueChanged.connect(self._emit_float_value)
    
    def _on_value_changed(self, value):
        self.value_label.setText(f"{value}%")
        self.valueChanged.emit(value)
    
    def _emit_float_value(self, value):
        # Convert percentage to float (0.0 to 1.0)
        float_value = value / 100.0
        self.valueChangedFloat.emit(float_value)
    
    def setValueFloat(self, float_value):
        # Convert float (0.0 to 1.0) to percentage (0 to 100)
        percent_value = int(float_value * 100)
        self.setValue(percent_value)
    
    def valueFloat(self):
        return self.value() / 100.0


class TemperatureSlider(LabeledSlider):
    def __init__(self, label_text, min_temp=1000, max_temp=6500, initial_temp=3500, parent=None):
        super().__init__(label_text, min_temp, max_temp, initial_temp, parent)
        self.value_label.setText(f"{initial_temp}K")
    
    def _on_value_changed(self, value):
        self.value_label.setText(f"{value}K")
        self.valueChanged.emit(value) 