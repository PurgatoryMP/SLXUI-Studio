import xml.etree.ElementTree as ET
from PySide6.QtCore import Qt, QPointF, QMimeData
from PySide6.QtGui import (
    QFont, QAction, QDrag, QTextDocument, QTextCursor,
    QTextCharFormat, QColor, QBrush
)
from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QTreeWidget, QTreeWidgetItem, QTreeWidgetItemIterator,
    QTextEdit, QFileDialog, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton
)
from registry import XUI_REGISTRY
from textures import TextureManager
from graphics_item import XUIGraphicsItem
from canvas import CanvasContainer
from tree_widget import SceneTreeWidget
from inspector import PropertyInspector
from compiler import XUICompiler


class WidgetPaletteTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setHeaderLabel("XUI Widget Palette (Drag to Canvas)")

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item or item.childCount() > 0:
            return
        drag = QDrag(self)
        mime_data = QMimeData()
        mime_data.setText(item.text(0))
        drag.setMimeData(mime_data)
        drag.exec(Qt.CopyAction)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Second Life XUI Designer - Professional Edition")
        self.resize(1600, 950)

        self.current_selected_item = None
        self.tree_search_matches = []
        self.tree_search_idx = -1

        self._setup_menus()
        self._setup_ui()

    def _setup_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")

        new_act = QAction("&New Layout", self)
        new_act.triggered.connect(self._new_layout)
        file_menu.addAction(new_act)

        open_act = QAction("&Open XUI File...", self)
        open_act.setShortcut("Ctrl+O")
        open_act.triggered.connect(self._open_file)
        file_menu.addAction(open_act)

        save_act = QAction("&Save XUI File...", self)
        save_act.setShortcut("Ctrl+S")
        save_act.triggered.connect(self._save_file)
        file_menu.addAction(save_act)

        file_menu.addSeparator()

        set_skin_act = QAction("Set Viewer Texture Folder...", self)
        set_skin_act.triggered.connect(self._set_texture_folder)
        file_menu.addAction(set_skin_act)

    def _setup_ui(self):
        main_splitter = QSplitter(Qt.Horizontal, self)
        self.setCentralWidget(main_splitter)

        palette_tree = WidgetPaletteTree()
        for cat_name, widgets in XUI_REGISTRY.items():
            cat_item = QTreeWidgetItem(palette_tree, [cat_name])
            for w_name, w_meta in widgets.items():
                item = QTreeWidgetItem(cat_item, [w_name])
                item.setToolTip(0, w_meta.get("desc", w_name))
        palette_tree.expandAll()
        main_splitter.addWidget(palette_tree)

        center_splitter = QSplitter(Qt.Vertical)
        self.canvas = CanvasContainer()
        center_splitter.addWidget(self.canvas)

        # ----------------------------------------------------
        # LIVE XML SOURCE + FIND FIELD
        # ----------------------------------------------------
        code_container = QWidget()
        code_layout = QVBoxLayout(code_container)
        code_layout.setContentsMargins(0, 0, 0, 0)

        xml_header_layout = QHBoxLayout()
        xml_header_layout.addWidget(QLabel("<b>Live Second Life XML Source:</b>"))
        xml_header_layout.addStretch()

        self.xml_search_input = QLineEdit()
        self.xml_search_input.setPlaceholderText("Find in XML...")
        self.xml_search_input.setFixedWidth(150)
        self.xml_search_input.textChanged.connect(self._on_xml_search_changed)
        xml_header_layout.addWidget(self.xml_search_input)

        xml_prev_btn = QPushButton("▲")
        xml_prev_btn.setFixedWidth(30)
        xml_prev_btn.clicked.connect(self._xml_search_prev)
        xml_header_layout.addWidget(xml_prev_btn)

        xml_next_btn = QPushButton("▼")
        xml_next_btn.setFixedWidth(30)
        xml_next_btn.clicked.connect(self._xml_search_next)
        xml_header_layout.addWidget(xml_next_btn)

        code_layout.addLayout(xml_header_layout)

        self.code_view = QTextEdit()
        self.code_view.setFont(QFont("Consolas", 10))
        self.code_view.setReadOnly(True)
        code_layout.addWidget(self.code_view)

        center_splitter.addWidget(code_container)
        center_splitter.setSizes([650, 300])
        main_splitter.addWidget(center_splitter)

        right_splitter = QSplitter(Qt.Vertical)

        # ----------------------------------------------------
        # DOM HIERARCHY + FIND FIELD
        # ----------------------------------------------------
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)

        tree_header_layout = QHBoxLayout()
        tree_header_layout.addWidget(QLabel("<b>XUI DOM Hierarchy:</b>"))
        tree_header_layout.addStretch()

        self.tree_search_input = QLineEdit()
        self.tree_search_input.setPlaceholderText("Find node...")
        self.tree_search_input.setFixedWidth(120)
        self.tree_search_input.textChanged.connect(self._on_tree_search_changed)
        tree_header_layout.addWidget(self.tree_search_input)

        tree_prev_btn = QPushButton("▲")
        tree_prev_btn.setFixedWidth(30)
        tree_prev_btn.clicked.connect(self._tree_search_prev)
        tree_header_layout.addWidget(tree_prev_btn)

        tree_next_btn = QPushButton("▼")
        tree_next_btn.setFixedWidth(30)
        tree_next_btn.clicked.connect(self._tree_search_next)
        tree_header_layout.addWidget(tree_next_btn)

        tree_layout.addLayout(tree_header_layout)

        self.scene_tree = SceneTreeWidget()
        self.scene_tree.set_canvas(self.canvas)
        tree_layout.addWidget(self.scene_tree)
        right_splitter.addWidget(tree_container)

        inspector_container = QWidget()
        inspector_layout = QVBoxLayout(inspector_container)
        inspector_layout.setContentsMargins(0, 0, 0, 0)
        inspector_layout.addWidget(QLabel("<b>Widget Attributes & Parameters:</b>"))
        self.inspector = PropertyInspector()
        inspector_layout.addWidget(self.inspector)
        right_splitter.addWidget(inspector_container)

        right_splitter.setSizes([350, 600])
        main_splitter.addWidget(right_splitter)

        main_splitter.setSizes([250, 950, 400])

        self.canvas.item_selected_signal.connect(self._on_item_selected)
        self.canvas.item_modified_signal.connect(self._refresh_code_view)
        self.inspector.property_changed_signal.connect(self._refresh_code_view)
        # Re-apply tree search highlights after canvas drags refresh the tree
        self.scene_tree.tree_refreshed.connect(self._reapply_tree_search)

    # ------------------------------------------------------------------------
    # SEARCH & HIGHLIGHT: XML SOURCE
    # ------------------------------------------------------------------------
    def _on_xml_search_changed(self, text):
        self._highlight_all_xml(text)
        self._xml_search_next()

    def _highlight_all_xml(self, text):
        self.code_view.setExtraSelections([])
        if not text:
            return

        selections = []
        doc = self.code_view.document()
        cursor = QTextCursor(doc)

        format = QTextCharFormat()
        format.setBackground(QColor("#FFFF00"))
        format.setForeground(QColor("#000000"))

        while not cursor.isNull() and not cursor.atEnd():
            cursor = doc.find(text, cursor)
            if not cursor.isNull():
                sel = QTextEdit.ExtraSelection()
                sel.cursor = cursor
                sel.format = format
                selections.append(sel)

        self.code_view.setExtraSelections(selections)

    def _xml_search_next(self):
        text = self.xml_search_input.text()
        if not text: return
        if not self.code_view.find(text):
            # Wrap around to start
            cursor = self.code_view.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.code_view.setTextCursor(cursor)
            self.code_view.find(text)

    def _xml_search_prev(self):
        text = self.xml_search_input.text()
        if not text: return
        options = QTextDocument.FindBackward
        if not self.code_view.find(text, options):
            # Wrap around to end
            cursor = self.code_view.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.code_view.setTextCursor(cursor)
            self.code_view.find(text, options)

    # ------------------------------------------------------------------------
    # SEARCH & HIGHLIGHT: DOM HIERARCHY
    # ------------------------------------------------------------------------
    def _on_tree_search_changed(self, text):
        self.tree_search_matches = []
        self.tree_search_idx = -1

        it = QTreeWidgetItemIterator(self.scene_tree)
        while it.value():
            item = it.value()
            # Reset colors to default
            item.setBackground(0, QBrush())
            item.setForeground(0, QBrush())

            if text and text.lower() in item.text(0).lower():
                item.setBackground(0, QBrush(QColor("#FFFF00")))
                item.setForeground(0, QBrush(QColor("#000000")))
                self.tree_search_matches.append(item)
            it += 1

        if self.tree_search_matches:
            self._tree_search_next()

    def _reapply_tree_search(self):
        """Automatically reapplies search highlights if a drag-drop resets the DOM Tree."""
        if hasattr(self, 'tree_search_input') and self.tree_search_input.text():
            self._on_tree_search_changed(self.tree_search_input.text())

    def _tree_search_next(self):
        if not self.tree_search_matches: return
        self.tree_search_idx = (self.tree_search_idx + 1) % len(self.tree_search_matches)
        item = self.tree_search_matches[self.tree_search_idx]
        self.scene_tree.setCurrentItem(item)
        self.scene_tree.scrollToItem(item)

    def _tree_search_prev(self):
        if not self.tree_search_matches: return
        self.tree_search_idx = (self.tree_search_idx - 1) % len(self.tree_search_matches)
        item = self.tree_search_matches[self.tree_search_idx]
        self.scene_tree.setCurrentItem(item)
        self.scene_tree.scrollToItem(item)

    # ------------------------------------------------------------------------
    # CORE LOGIC
    # ------------------------------------------------------------------------
    def _on_item_selected(self, item):
        self.current_selected_item = item
        self.inspector.set_item(item)
        self._refresh_code_view()

    def _refresh_code_view(self, _ignored=None):
        xml_str = XUICompiler.generate_rich_xml(self.canvas.root_container_instance, self.current_selected_item)
        self.code_view.setHtml(xml_str)
        # Re-apply XML yellow highlight on code refresh
        if hasattr(self, 'xml_search_input') and self.xml_search_input.text():
            self._highlight_all_xml(self.xml_search_input.text())

    def _new_layout(self):
        self.canvas.clear_canvas()
        self.scene_tree.clear()
        self.inspector.set_item(None)
        self.current_selected_item = None
        self.code_view.clear()

    def _set_texture_folder(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Viewer Textures Directory",
            TextureManager.get().base_path
        )
        if dir_path:
            TextureManager.get().set_base_path(dir_path)
            self.canvas.scene.update()

    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open XUI XML File", "", "XML Files (*.xml);;All Files (*)")
        if not file_path:
            return

        try:
            tree = ET.parse(file_path)
            root_el = tree.getroot()
            self._new_layout()

            self._parse_xml_node(root_el, parent_item=None)
            self.scene_tree.refresh_tree()
            self._refresh_code_view()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to parse XUI file:\n{str(e)}")

    def _parse_xml_node(self, element, parent_item=None, last_sibling_item=None):
        tag_name = element.tag

        if "." in tag_name:
            if parent_item and isinstance(parent_item, XUIGraphicsItem):
                parent_item.non_visual_children.append({
                    "tag": tag_name,
                    "attributes": dict(element.attrib)
                })
            return None

        attributes = dict(element.attrib)

        has_geometry = any(k in attributes for k in ["left", "right", "top", "bottom", "width", "height"])
        if not has_geometry:
            attributes["designer_export_geometry"] = "false"

        parent_w = parent_item.rect().width() if isinstance(parent_item, XUIGraphicsItem) else 500
        parent_h = parent_item.rect().height() if isinstance(parent_item, XUIGraphicsItem) else 500

        left, right, top, bottom = None, None, None, None

        if "left" in attributes:
            left = int(attributes["left"])
        elif "left_delta" in attributes and last_sibling_item:
            left = int(last_sibling_item.x()) + int(attributes["left_delta"])
        elif "left_pad" in attributes and last_sibling_item:
            left = int(last_sibling_item.x() + last_sibling_item.rect().width()) + int(attributes["left_pad"])

        if "right" in attributes:
            right_val = int(attributes["right"])
            right = int(parent_w) + right_val if right_val <= 0 else right_val

        if "top" in attributes:
            top = int(attributes["top"])
        elif "top_delta" in attributes and last_sibling_item:
            top = int(last_sibling_item.y()) + int(attributes["top_delta"])
        elif "top_pad" in attributes and last_sibling_item:
            top = int(last_sibling_item.y() + last_sibling_item.rect().height()) + int(attributes["top_pad"])

        if "bottom" in attributes:
            bottom_val = int(attributes["bottom"])
            bottom = int(parent_h) + bottom_val if bottom_val <= 0 else bottom_val

        default_w, default_h = 100, 20
        for cat, widgets in XUI_REGISTRY.items():
            if tag_name in widgets:
                default_w = widgets[tag_name].get("width", 100)
                default_h = widgets[tag_name].get("height", 20)
                break

        width = int(attributes.get("width", default_w))
        height = int(attributes.get("height", default_h))

        if left is not None and right is not None:
            width = right - left
        elif left is None and right is not None:
            left = right - width
        elif left is None:
            left = 0

        if top is not None and bottom is not None:
            height = bottom - top
        elif top is None and bottom is not None:
            top = bottom - height
        elif top is None:
            top = 0

        attributes["left"] = str(int(left))
        attributes["top"] = str(int(top))
        attributes["width"] = str(int(width))
        attributes["height"] = str(int(height))

        item = XUIGraphicsItem(tag_name, attributes)

        if element.text and element.text.strip():
            item.inner_text = element.text.strip()

        item.setPos(QPointF(left, top))
        item.sync_geometry_to_attributes()

        if parent_item and isinstance(parent_item, XUIGraphicsItem):
            parent_item.add_child_item(item)
        elif self.canvas.root_container_instance is None:
            self.canvas.root_container_instance = item
            self.canvas.scene.addItem(item)

        previous_child = None
        for child_el in element:
            created_child = self._parse_xml_node(child_el, parent_item=item, last_sibling_item=previous_child)
            if created_child:
                previous_child = created_child

        return item

    def _save_file(self):
        if not self.canvas.root_container_instance:
            QMessageBox.warning(self, "Warning", "No layout to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save XUI XML File", "layout.xml",
                                                   "XML Files (*.xml);;All Files (*)")
        if file_path:
            try:
                xml_content = XUICompiler.generate_plain_xml(self.canvas.root_container_instance)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(xml_content)
                QMessageBox.information(self, "Success", "XUI file saved successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save file:\n{str(e)}")