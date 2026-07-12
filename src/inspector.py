from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFormLayout, QLabel, QGroupBox, QLineEdit, QComboBox
from registry import UNIVERSAL_ATTRIBUTES, XUI_REGISTRY


class PropertyInspector(QWidget):
    property_changed_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_xui_item = None
        self.updating = False

        # Caches active UI input fields to allow real-time canvas sync updates
        self.editors = {}

        self.layout = QVBoxLayout(self)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.form_layout = QFormLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)

    def set_item(self, xui_item):
        self.current_xui_item = xui_item
        self._rebuild_form()

    def refresh_values(self):
        """Silently updates field data in real-time without rebuilding the UI (prevents focus loss)."""
        if self.updating or not self.current_xui_item:
            return

        self.updating = True
        for key, (editor, attr_type) in self.editors.items():
            val = self.current_xui_item.attributes.get(key, "")

            if isinstance(editor, QComboBox):
                target_val = str(val).lower() if attr_type == "bool" else str(val)
                if editor.currentText() != target_val:
                    editor.setCurrentText(target_val)

            elif isinstance(editor, QLineEdit):
                if editor.text() != str(val):
                    editor.setText(str(val))

        self.updating = False

    def _get_item_schema(self, tag_name):
        """Looks up the specialized parameter schema for the selected widget tag."""
        for category, widgets in XUI_REGISTRY.items():
            if tag_name in widgets:
                return widgets[tag_name].get("params", UNIVERSAL_ATTRIBUTES)
        return UNIVERSAL_ATTRIBUTES

    def _rebuild_form(self):
        self.updating = True
        self.editors.clear()

        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.current_xui_item:
            self.updating = False
            return

        schema = self._get_item_schema(self.current_xui_item.tag_name)
        groups = {}

        for key, meta in schema.items():
            grp = meta.get("group", "General")
            if grp not in groups:
                groups[grp] = []
            val = self.current_xui_item.attributes.get(key, meta.get("default", ""))
            groups[grp].append((key, val, meta))

        for grp_name, items in sorted(groups.items()):
            grp_box = QGroupBox(grp_name)
            grp_layout = QFormLayout(grp_box)

            for key, val, meta in sorted(items, key=lambda x: x[0]):
                attr_type = meta.get("type", "str")

                if attr_type == "combo" and "options" in meta:
                    editor = QComboBox()
                    editor.addItems(meta["options"])
                    if str(val) in meta["options"]:
                        editor.setCurrentText(str(val))
                    else:
                        editor.setEditText(str(val))
                    editor.currentTextChanged.connect(lambda text, k=key: self._on_attr_changed(k, text))

                # --- NEW: Automatically render dropdowns for ANY Boolean tag! ---
                elif attr_type == "bool":
                    editor = QComboBox()
                    editor.addItems(["true", "false"])
                    editor.setCurrentText(str(val).lower() if str(val).lower() in ["true", "false"] else "true")
                    editor.currentTextChanged.connect(lambda text, k=key: self._on_attr_changed(k, text))

                else:
                    editor = QLineEdit(str(val))
                    editor.editingFinished.connect(lambda k=key, ed=editor: self._on_attr_changed(k, ed.text()))

                self.editors[key] = (editor, attr_type)
                grp_layout.addRow(QLabel(key + ":"), editor)

            self.form_layout.addRow(grp_box)

        self.updating = False

    def _on_attr_changed(self, key, val_str):
        if self.updating or not self.current_xui_item:
            return

        # Avoid redundant rendering if value hasn't actually changed
        if self.current_xui_item.attributes.get(key) == val_str:
            return

        self.current_xui_item.attributes[key] = val_str

        # Update bounding boxes and trigger layout logic seamlessly
        try:
            if key == "left":
                self.current_xui_item.setX(float(val_str))
                self.current_xui_item.sync_attributes_to_geometry()
            elif key == "top":
                self.current_xui_item.setY(float(val_str))
                self.current_xui_item.sync_attributes_to_geometry()
            elif key == "width":
                self.current_xui_item.resize_item(float(val_str), self.current_xui_item.rect().height())
            elif key == "height":
                self.current_xui_item.resize_item(self.current_xui_item.rect().width(), float(val_str))

            # Recalculate relative padding updates live!
            elif key in ["left_delta", "left_pad", "top_delta", "top_pad"]:
                parent = self.current_xui_item.parentItem()
                if parent and hasattr(parent, 'child_xui_items') and self.current_xui_item in parent.child_xui_items:
                    idx = parent.child_xui_items.index(self.current_xui_item)
                    prev_sib = parent.child_xui_items[idx - 1] if idx > 0 else None
                    if prev_sib:
                        if key == "left_delta":
                            self.current_xui_item.setX(prev_sib.x() + float(val_str))
                        elif key == "left_pad":
                            self.current_xui_item.setX(prev_sib.x() + prev_sib.rect().width() + float(val_str))
                        elif key == "top_delta":
                            self.current_xui_item.setY(prev_sib.y() + float(val_str))
                        elif key == "top_pad":
                            self.current_xui_item.setY(prev_sib.y() + prev_sib.rect().height() + float(val_str))
                        self.current_xui_item.sync_attributes_to_geometry()
        except ValueError:
            pass

        self.current_xui_item.update()
        if self.current_xui_item.scene():
            self.current_xui_item.scene().update()

        self.property_changed_signal.emit()