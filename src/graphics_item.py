"""
This module provides the XUIGraphicsItem class, a specialized QGraphicsRectItem
responsible for rendering Second Life Viewer UI controls on the editor canvas.
It handles 9-slice background scaling, dynamic grid snapping, layout resizing
using 'follows' rules, and specialized rendering for container widgets like
floaters, tab containers, and layout stacks.
"""
from PySide6.QtCore import Qt, QRectF, QPointF, QLineF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QCursor, QFont, QAction
from PySide6.QtWidgets import (
    QGraphicsRectItem, QGraphicsItem, QWidget, QMenu,
    QGraphicsSceneContextMenuEvent, QStyleOptionGraphicsItem, QStyle
)
from registry import LLVIEW_PARAMS, LLUICTRL_PARAMS, XUI_REGISTRY
from textures import TextureManager, draw_9_slice
from typing import Any, Dict, List, Optional, Tuple

class StackDragHandle(QGraphicsRectItem):
    """An interactive drag handle rendered between layout_panels in a layout_stack."""

    def __init__(self, stack_item: any, index: int, orientation: str) -> None:
        super().__init__(stack_item)
        self.stack_item = stack_item
        self.index = index
        self.orientation = orientation
        self.setFlags(QGraphicsItem.ItemIsSelectable | QGraphicsItem.ItemIsMovable)
        self.setAcceptHoverEvents(True)
        self.setZValue(1000.0)  # Sit above child layout_panels so mouse events are intercepted
        self.resizing: bool = False
        self.drag_start_pos: Optional[QPointF] = None
        self.start_w1: float = 0.0
        self.start_h1: float = 0.0
        self.start_w2: float = 0.0
        self.start_h2: float = 0.0

    def hoverEnterEvent(self, event: any) -> None:
        self.update()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: any) -> None:
        self.update()
        super().hoverLeaveEvent(event)

    def hoverMoveEvent(self, event: any) -> None:
        if self.orientation == "vertical":
            self.setCursor(QCursor(Qt.SplitVCursor))
        else:
            self.setCursor(QCursor(Qt.SplitHCursor))
        super().hoverMoveEvent(event)

    def mousePressEvent(self, event: any) -> None:
        if event.button() == Qt.LeftButton:
            panels = [
                c for c in self.stack_item.child_xui_items
                if isinstance(c, XUIGraphicsItem) and getattr(c, "tag_name", "") == "layout_panel"
            ]
            if self.index < len(panels) - 1:
                self.resizing = True
                self.drag_start_pos = event.scenePos()
                p1 = panels[self.index]
                p2 = panels[self.index + 1]
                self.start_w1 = p1.rect().width()
                self.start_h1 = p1.rect().height()
                self.start_w2 = p2.rect().width()
                self.start_h2 = p2.rect().height()

                self.update()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: any) -> None:
        if self.resizing and self.drag_start_pos:
            cur_pos = event.scenePos()
            panels = [
                c for c in self.stack_item.child_xui_items
                if isinstance(c, XUIGraphicsItem) and getattr(c, "tag_name", "") == "layout_panel"
            ]
            if self.index >= len(panels) - 1:
                return
            p1 = panels[self.index]
            p2 = panels[self.index + 1]

            def get_min_max(item: any, orient: str) -> Tuple[float, float]:
                if orient == "vertical":
                    min_val = float(item.attributes.get("min_height", 10))
                    max_val = float(item.attributes.get("max_height", 10000))
                else:
                    min_val = float(item.attributes.get("min_width", 10))
                    max_val = float(item.attributes.get("max_width", 10000))
                return max(10.0, min_val), max(min_val, max_val)

            if self.orientation == "vertical":
                delta_y = cur_pos.y() - self.drag_start_pos.y()
                min_h1, max_h1 = get_min_max(p1, "vertical")
                min_h2, max_h2 = get_min_max(p2, "vertical")

                new_h1 = max(min_h1, min(max_h1, self.start_h1 + delta_y))
                actual_delta = new_h1 - self.start_h1
                new_h2 = self.start_h2 - actual_delta
                new_h2_constrained = max(min_h2, min(max_h2, new_h2))
                actual_delta = self.start_h2 - new_h2_constrained
                new_h1 = self.start_h1 + actual_delta

                p1.attributes["height"] = str(int(new_h1))
                p1.setRect(0, 0, p1.rect().width(), new_h1)
                p1.sync_attributes_to_geometry()

                p2.attributes["height"] = str(int(new_h2_constrained))
                p2.setRect(0, 0, p2.rect().width(), new_h2_constrained)
                p2.sync_attributes_to_geometry()
            else:
                delta_x = cur_pos.x() - self.drag_start_pos.x()
                min_w1, max_w1 = get_min_max(p1, "horizontal")
                min_w2, max_w2 = get_min_max(p2, "horizontal")

                new_w1 = max(min_w1, min(max_w1, self.start_w1 + delta_x))
                actual_delta = new_w1 - self.start_w1
                new_w2 = self.start_w2 - actual_delta
                new_w2_constrained = max(min_w2, min(max_w2, new_w2))
                actual_delta = self.start_w2 - new_w2_constrained
                new_w1 = self.start_w1 + actual_delta

                p1.attributes["width"] = str(int(new_w1))
                p1.setRect(0, 0, new_w1, p1.rect().height())
                p1.sync_attributes_to_geometry()

                p2.attributes["width"] = str(int(new_w2_constrained))
                p2.setRect(0, 0, new_w2_constrained, p2.rect().height())
                p2.sync_attributes_to_geometry()

            self.stack_item.update_layout_stack()
            if self.scene():
                self.scene().update()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: any) -> None:
        if self.resizing:
            self.resizing = False
            self.update()
            if hasattr(self.scene(), "canvas_container") and self.scene().canvas_container:
                self.scene().canvas_container.item_modified_signal.emit(self.stack_item)
            event.accept()
        super().mouseReleaseEvent(event)

    def paint(self, painter: QPainter, option: any, widget: Optional[any] = None) -> None:
        rect = self.rect()
        if option:
            option.state &= ~QStyle.State_Selected

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing, False)

        if self.orientation == "vertical":
            mid_y = rect.height() / 2.0
            pill_w = min(40.0, max(16.0, rect.width() * 0.2))
            pill_x = (rect.width() - pill_w) / 2.0
            pill_rect = QRectF(pill_x, mid_y - 2.0, pill_w, 4.0)

            painter.fillRect(QRectF(0, mid_y - 1.0, rect.width(), 2.0), QColor("#2a2a2a"))
            painter.fillRect(
                pill_rect,
                QColor("#569CD6") if self.isUnderMouse() or self.resizing else QColor("#666666"),
            )
            painter.setPen(QPen(QColor("#111111"), 1))
            painter.drawRect(pill_rect)
        else:
            mid_x = rect.width() / 2.0
            pill_h = min(40.0, max(16.0, rect.height() * 0.2))
            pill_y = (rect.height() - pill_h) / 2.0
            pill_rect = QRectF(mid_x - 2.0, pill_y, 4.0, pill_h)

            painter.fillRect(QRectF(mid_x - 1.0, 0, 2.0, rect.height()), QColor("#2a2a2a"))
            painter.fillRect(
                pill_rect,
                QColor("#569CD6") if self.isUnderMouse() or self.resizing else QColor("#666666"),
            )
            painter.setPen(QPen(QColor("#111111"), 1))
            painter.drawRect(pill_rect)

        painter.restore()


class XUIGraphicsItem(QGraphicsRectItem):
    """A visual canvas item representing a single XML node in the XUI hierarchy.

    Manages bidirectional synchronization between visual canvas geometry and DOM
    attribute dictionaries. Supports interactive moving, 8-way handle resizing,
    and automatic layout adjustments for child components.

    Attributes:
        tag_name (str): The XML tag name of the widget (e.g., 'button', 'floater').
        attributes (dict): Key-value pairs representing the XML node's attributes.
        source_file (str): The filename where this XML node originated.
        is_imported_root (bool): True if this item represents the root of an included XML file.
        active_tab_index (int): The currently active tab index if this is a tab container.
        child_xui_items (list[XUIGraphicsItem]): Visual child components nested inside this item.
        non_visual_children (list[dict]): Non-visual XML children (e.g., event bindings, timers).
        inner_text (str): Text content located between opening and closing XML tags.
        resize_handle_size (int): The pixel size of interactive selection corner handles.
        resizing (bool): Flag indicating if the item is currently being resized by the user.
        resize_dir (str | None): The active resize handle direction (e.g., 'TL', 'BR').
    """

    def __init__(self, tag_name, attributes=None, parent_item=None):
        """Initializes the graphics item, inheriting schema defaults and configuring flags.

        Args:
            tag_name: The XUI XML tag identifier for the widget type.
            attributes: Optional initial dictionary of XML attributes.
            parent_item: The parent QGraphicsItem, if nested inside another container.
        """
        super().__init__(parent_item)
        self.tag_name = tag_name
        self.attributes = attributes or {}

        self.source_file = "layout.xml"
        self.is_imported_root = False
        self.active_tab_index = 0

        # Inherit parameters based on schema registry
        target_params = {}
        for cat_name, widgets in XUI_REGISTRY.items():
            if tag_name in widgets:
                widget_def = widgets[tag_name]
                target_params = widget_def.get("params", {})

                # Apply compound attributes discovered during XML registration
                if "default_attributes" in widget_def:
                    for k, v in widget_def["default_attributes"].items():
                        if k not in self.attributes:
                            self.attributes[k] = v

                if "label" in widget_def and not self.attributes.get("label"):
                    self.attributes["label"] = widget_def["label"]
                if "width" in widget_def and "width" not in self.attributes:
                    self.attributes["width"] = str(widget_def["width"])
                if "height" in widget_def and "height" not in self.attributes:
                    self.attributes["height"] = str(widget_def["height"])
                break

        if not target_params:
            target_params = LLUICTRL_PARAMS if tag_name != "view" else LLVIEW_PARAMS

        if "name" not in self.attributes:
            if tag_name in ["floater", "multi_floater", "panel", "layout_panel", "tab_container", "layout_stack"]:
                self.attributes["name"] = tag_name
            elif "label" in self.attributes and self.attributes["label"]:
                self.attributes["name"] = self.attributes["label"].lower().replace(" ", "_")
            else:
                self.attributes["name"] = tag_name

        for attr, meta in target_params.items():
            if attr not in self.attributes and meta.get("default", "") != "":
                self.attributes[attr] = meta["default"]

        # Mandatory layout container defaults for proper serialization and layout math
        if tag_name == "layout_stack":
            if "orientation" not in self.attributes:
                self.attributes["orientation"] = "vertical"
            if "width" not in self.attributes:
                self.attributes["width"] = "200"
            if "height" not in self.attributes:
                self.attributes["height"] = "200"
        elif tag_name == "layout_panel":
            if "auto_resize" not in self.attributes:
                self.attributes["auto_resize"] = "true"
            if "width" not in self.attributes:
                self.attributes["width"] = "200"
            if "height" not in self.attributes:
                self.attributes["height"] = "100"

        self.setFlags(
            QGraphicsItem.ItemIsSelectable |
            QGraphicsItem.ItemIsMovable |
            QGraphicsItem.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)

        self.child_xui_items = []
        self.non_visual_children = []
        self.inner_text = ""

        self.resize_handle_size = 6
        self.resizing = False
        self.resize_dir = None

        self._drag_handles = []
        self._plus_btn_rect = None

        self.sync_geometry_to_attributes()

    def itemChange(self, change, value):
        """Intercepts Qt item state changes to handle grid snapping and XML coordinate updates.

        When moved, this method snaps coordinates to the canvas grid and recalculates
        positional XML attributes ('left', 'top', 'right', 'bottom', or relative delta/pad
        attributes) based on parent boundaries and sibling offsets.
        """
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            parent = self.parentItem()
            # In a layout stack, panel coordinates are strictly managed by the layout engine.
            # Suppress generation of absolute left/top/right/bottom attributes.
            if parent and getattr(parent, "tag_name", "") == "layout_stack":
                if hasattr(self.scene(), 'canvas_container') and self.scene().canvas_container:
                    self.scene().canvas_container.item_modified_signal.emit(self)
                return value

            canvas = getattr(self.scene(), 'canvas_container', None) or self.scene()
            snapping_enabled = getattr(canvas, 'grid_snapping_enabled', True)
            grid_size = getattr(canvas, 'grid_size', 10)

            new_pos = value
            if snapping_enabled and grid_size > 0:
                snapped_x = round(new_pos.x() / grid_size) * grid_size
                snapped_y = round(new_pos.y() / grid_size) * grid_size
            else:
                snapped_x = new_pos.x()
                snapped_y = new_pos.y()

            idx = parent.child_xui_items.index(self) if isinstance(parent, XUIGraphicsItem) and self in parent.child_xui_items else -1
            prev_sib = parent.child_xui_items[idx - 1] if idx > 0 else None

            if "right" in self.attributes:
                parent_w = parent.rect().width() if isinstance(parent, XUIGraphicsItem) else 500
                try:
                    if int(self.attributes["right"]) <= 0:
                        self.attributes["right"] = str(int((snapped_x + self.rect().width()) - parent_w))
                    else:
                        self.attributes["right"] = str(int(snapped_x + self.rect().width()))
                except ValueError:
                    self.attributes["right"] = str(int(snapped_x + self.rect().width()))
            elif "left_delta" in self.attributes and prev_sib:
                self.attributes["left_delta"] = str(int(snapped_x - prev_sib.x()))
            elif "left_pad" in self.attributes and prev_sib:
                self.attributes["left_pad"] = str(int(snapped_x - (prev_sib.x() + prev_sib.rect().width())))
            else:
                self.attributes["left"] = str(int(snapped_x))

            if "bottom" in self.attributes:
                parent_h = parent.rect().height() if isinstance(parent, XUIGraphicsItem) else 500
                try:
                    if int(self.attributes["bottom"]) <= 0:
                        self.attributes["bottom"] = str(int((snapped_y + self.rect().height()) - parent_h))
                    else:
                        self.attributes["bottom"] = str(int(snapped_y + self.rect().height()))
                except ValueError:
                    self.attributes["bottom"] = str(int(snapped_y + self.rect().height()))
            elif "top_delta" in self.attributes and prev_sib:
                self.attributes["top_delta"] = str(int(snapped_y - prev_sib.y()))
            elif "top_pad" in self.attributes and prev_sib:
                self.attributes["top_pad"] = str(int(snapped_y - (prev_sib.y() + prev_sib.rect().height())))
            else:
                self.attributes["top"] = str(int(snapped_y))

            if hasattr(self.scene(), 'canvas_container') and self.scene().canvas_container:
                self.scene().canvas_container.item_modified_signal.emit(self)
            return QPointF(snapped_x, snapped_y)
        return super().itemChange(change, value)

    def contextMenuEvent(self, event: QGraphicsSceneContextMenuEvent) -> None:
        """Displays right-click context menu with edit actions and anchor checkboxes."""
        menu = QMenu()

        # Standard Edit Actions
        copy_action = menu.addAction("Copy")
        paste_action = menu.addAction("Paste")
        duplicate_action = menu.addAction("Duplicate")
        menu.addSeparator()
        delete_action = menu.addAction("Delete")
        menu.addSeparator()

        # Connect edit actions to the CanvasContainer
        canvas = self._get_canvas_container()
        if canvas:
            copy_action.triggered.connect(lambda: getattr(canvas, "copy_selected", lambda: None)())
            paste_action.triggered.connect(lambda: getattr(canvas, "paste_selected", lambda: None)())
            duplicate_action.triggered.connect(lambda: getattr(canvas, "duplicate_selected", lambda: None)())
            delete_action.triggered.connect(lambda: getattr(canvas, "delete_selected", lambda: None)())

        # "Anchor To" Submenu with Checkboxes
        anchor_menu = menu.addMenu("Anchor To")
        current_follows = self.attributes.get("follows", "left|top").lower()
        is_all = (current_follows == "all")

        if is_all:
            active_edges = {"left", "top", "right", "bottom"}
        else:
            active_edges = set(e.strip() for e in current_follows.split("|") if e.strip())

        edges = ["Left", "Top", "Right", "Bottom"]
        for edge in edges:
            action = QAction(edge, menu)
            action.setCheckable(True)
            action.setChecked(edge.lower() in active_edges)
            action.triggered.connect(lambda checked, e=edge.lower(): self._toggle_follow_edge(e, checked))
            anchor_menu.addAction(action)

        anchor_menu.addSeparator()
        all_action = QAction("All", menu)
        all_action.setCheckable(True)
        all_action.setChecked(is_all or len(active_edges) == 4)
        all_action.triggered.connect(self._set_follow_all)
        anchor_menu.addAction(all_action)

        menu.exec(event.screenPos())
        event.accept()

    def _toggle_follow_edge(self, edge: str, checked: bool) -> None:
        """Toggles an individual edge in the follows attribute."""
        current = self.attributes.get("follows", "left|top").lower()
        if current == "all":
            edges = {"left", "top", "right", "bottom"}
        else:
            edges = set(e.strip() for e in current.split("|") if e.strip())

        if checked:
            edges.add(edge)
        else:
            edges.discard(edge)

        if len(edges) == 4:
            new_val = "all"
        elif not edges:
            new_val = ""
        else:
            order = ["left", "top", "right", "bottom"]
            new_val = "|".join([e for e in order if e in edges])

        self._apply_follows_change(new_val)

    def _set_follow_all(self, checked: bool) -> None:
        """Sets the follows attribute to all or resets to default."""
        new_val = "all" if checked else "left|top"
        self._apply_follows_change(new_val)

    def _apply_follows_change(self, new_val: str) -> None:
        """Applies follows attribute updates and triggers scene/tree synchronization."""
        self.attributes["follows"] = new_val
        if hasattr(self, "sync_attributes_to_geometry"):
            self.sync_attributes_to_geometry()

        # If parent is a layout stack, immediately re-layout to reflect expanded space
        parent = self.parentItem()
        if parent and getattr(parent, "tag_name", "") in ("layout_stack", "layout_panel"):
            if hasattr(parent, "update_layout_stack"):
                parent.update_layout_stack()

        canvas = self._get_canvas_container()
        if canvas and hasattr(canvas, "item_modified_signal"):
            canvas.item_modified_signal.emit(self)

        if self.scene():
            self.scene().update()

    def _get_canvas_container(self) -> any:
        """Traverses view hierarchy to find the main CanvasContainer instance."""
        if not self.scene():
            return None
        if hasattr(self.scene(), "canvas_container"):
            return self.scene().canvas_container
        for view in self.scene().views():
            widget = view
            while widget:
                if hasattr(widget, "item_modified_signal"):
                    return widget
                widget = widget.parent()
        return None

    def _draw_tab_container(self, painter, rect):
        """Renders the standard tab container background and top header buttons."""
        painter.fillRect(rect, QColor("#222222"))
        painter.setPen(QPen(QColor("#555555"), 1))
        painter.drawRect(rect)

        tabs = [child for child in getattr(self, 'child_xui_items', []) if isinstance(child, XUIGraphicsItem)]
        if not tabs:
            return

        header_height = 24
        header_rect = QRectF(rect.x(), rect.y(), rect.width(), header_height)
        painter.fillRect(header_rect, QColor("#181818"))
        painter.drawLine(rect.left(), rect.top() + header_height, rect.right(), rect.top() + header_height)

        tab_width = min(120, max(60, rect.width() / max(1, len(tabs))))
        for i, tab_item in enumerate(tabs):
            tab_x = rect.x() + (i * tab_width)
            tab_rect = QRectF(tab_x, rect.y(), tab_width, header_height)

            if i == self.active_tab_index:
                painter.fillRect(tab_rect, QColor("#3a3a3a"))
                painter.setPen(QPen(QColor("#1e457c"), 2))
                painter.drawLine(tab_rect.left(), tab_rect.bottom(), tab_rect.right(), tab_rect.bottom())
                painter.setPen(QPen(QColor("#FFFFFF")))
            else:
                painter.fillRect(tab_rect, QColor("#282828"))
                painter.setPen(QPen(QColor("#888888")))

            painter.drawRect(tab_rect)
            label = tab_item.attributes.get("label") or tab_item.attributes.get("title") or tab_item.attributes.get("name") or f"Tab {i + 1}"
            painter.drawText(tab_rect.adjusted(4, 0, -4, 0), Qt.AlignCenter | Qt.AlignVCenter, label)

        self.update_tab_visibility()

    def update_tab_visibility(self):
        """Updates child panel visibility, showing only the currently active tab panel."""
        tabs = [child for child in getattr(self, 'child_xui_items', []) if isinstance(child, XUIGraphicsItem)]
        for i, tab_item in enumerate(tabs):
            is_active = (i == self.active_tab_index)
            if tab_item.isVisible() != is_active:
                tab_item.setVisible(is_active)

    def update_z_orders(self):
        """Synchronizes Qt canvas Z-stacking order to strictly mirror DOM child array indexing."""
        for idx, child in enumerate(self.child_xui_items):
            child.setZValue(float(idx + 1))
            child.update_z_orders()

    def sync_geometry_to_attributes(self):
        """Updates the Qt bounding rectangle to match the XML width and height attributes."""
        try:
            w = float(self.attributes.get("width", 100))
            h = float(self.attributes.get("height", 20))
            self.setRect(0, 0, w, h)
        except ValueError:
            self.setRect(0, 0, 100, 20)

        if self.tag_name == "layout_stack":
            self.update_layout_stack()
        elif self.tag_name == "tab_container":
            self.update_tabs()
        elif self.parentItem() and getattr(self.parentItem(), "tag_name", "") == "layout_stack":
            if not getattr(self.parentItem(), "_updating_stack", False):
                self.parentItem().update_layout_stack()

        self.update()
        if self.scene():
            self.scene().update()

    def sync_attributes_to_geometry(self) -> None:
        """Recalculates and stores XML dimensional attributes based on current canvas geometry.

        Updates width, height, left, top, right, and bottom attributes while respecting
        relative positioning flags and parent container dimensions. Suppresses coordinate
        clutter for panels nested inside a layout_stack.
        """
        rect = self.rect()
        pos = self.pos()
        self.attributes["width"] = str(int(rect.width()))
        self.attributes["height"] = str(int(rect.height()))

        parent = self.parentItem()
        is_in_stack = parent and getattr(parent, "tag_name", "") == "layout_stack"

        if not is_in_stack:
            parent_w = parent.rect().width() if isinstance(parent, XUIGraphicsItem) else 500
            parent_h = parent.rect().height() if isinstance(parent, XUIGraphicsItem) else 500

            if "right" in self.attributes:
                try:
                    if int(self.attributes["right"]) <= 0:
                        self.attributes["right"] = str(int((pos.x() + rect.width()) - parent_w))
                    else:
                        self.attributes["right"] = str(int(pos.x() + rect.width()))
                except ValueError:
                    self.attributes["right"] = str(int(pos.x() + rect.width()))
            elif "left_delta" not in self.attributes and "left_pad" not in self.attributes:
                self.attributes["left"] = str(int(pos.x()))

            if "bottom" in self.attributes:
                try:
                    if int(self.attributes["bottom"]) <= 0:
                        self.attributes["bottom"] = str(int((pos.y() + rect.height()) - parent_h))
                    else:
                        self.attributes["bottom"] = str(int(pos.y() + rect.height()))
                except ValueError:
                    self.attributes["bottom"] = str(int(pos.y() + rect.height()))
            elif "top_delta" not in self.attributes and "top_pad" not in self.attributes:
                self.attributes["top"] = str(int(pos.y()))
        else:
            # Strip redundant absolute coordinates if present
            for col_key in ("left", "top", "right", "bottom", "left_delta", "top_delta", "left_pad", "top_pad"):
                self.attributes.pop(col_key, None)

        # Synchronize canvas transparency with the XML 'visible' attribute
        vis_val = str(self.attributes.get("visible", "true")).lower()
        is_visible = vis_val in ["true", "1", "yes"]
        self.setOpacity(1.0 if is_visible else 0.4)

        if self.tag_name == "layout_stack":
            self.update_layout_stack()
        elif is_in_stack and hasattr(parent, "update_layout_stack"):
            # Only trigger parent layout if the parent isn't ALREADY updating us
            if not getattr(parent, "_updating_stack", False):
                parent.update_layout_stack()

        self.update()
        if self.scene():
            self.scene().update()

    def resize_item(self, new_w, new_h):
        """Resizes the item and repositions child widgets according to their 'follows' rules.

        Parses child 'follows' flags (left, right, top, bottom, all) to proportionally
        move or resize nested elements as the parent container scales.

        Args:
            new_w: The new width in pixels.
            new_h: The new height in pixels.
        """
        old_w = self.rect().width()
        old_h = self.rect().height()
        dw = new_w - old_w
        dh = new_h - old_h

        if dw == 0 and dh == 0:
            return

        self.setRect(0, 0, new_w, new_h)
        self.sync_attributes_to_geometry()

        if self.tag_name == "tab_container":
            self.update_tabs()
        elif self.tag_name == "layout_stack":
            self.update_layout_stack()
        else:
            for child in self.child_xui_items:
                follows_str = child.attributes.get("follows", "left|top").lower()
                normalized_follows = follows_str.replace(" ", "|").replace(",", "|")
                follows = [f.strip() for f in normalized_follows.split("|") if f.strip()]

                if "all" in follows:
                    follows = ["left", "top", "right", "bottom"]

                cx, cy = child.x(), child.y()
                cw, ch = child.rect().width(), child.rect().height()
                child_dw = child_dh = move_x = move_y = 0

                if "left" in follows and "right" in follows:
                    child_dw = dw
                elif "right" in follows and "left" not in follows:
                    move_x = dw

                if "top" in follows and "bottom" in follows:
                    child_dh = dh
                elif "bottom" in follows and "top" not in follows:
                    move_y = dh

                if move_x != 0 or move_y != 0:
                    child.setPos(cx + move_x, cy + move_y)
                    child.sync_attributes_to_geometry()

                if child_dw != 0 or child_dh != 0:
                    child.resize_item(cw + child_dw, ch + child_dh)

    def update_tabs(self):
        """Recalculates layouts and panel boundaries for tab container controls."""
        if self.tag_name != "tab_container":
            return

        tabs = [c for c in self.child_xui_items if c.tag_name in ["panel", "layout_panel"]]
        if self.active_tab_index >= len(tabs):
            self.active_tab_index = max(0, len(tabs) - 1)

        tab_pos_side = self.attributes.get("tab_position", "top").lower()
        tab_height = int(self.attributes.get("tab_height", 21))
        tab_width_attr = int(self.attributes.get("tab_width", 80))

        container_w = float(self.attributes.get("width", 250))
        container_h = float(self.attributes.get("height", 180))

        if tab_pos_side == "top":
            panel_x, panel_y = 2.0, float(tab_height + 2)
            panel_w = max(10.0, container_w - 4.0)
            panel_h = max(10.0, container_h - tab_height - 4.0)
        elif tab_pos_side == "bottom":
            panel_x, panel_y = 2.0, 2.0
            panel_w = max(10.0, container_w - 4.0)
            panel_h = max(10.0, container_h - tab_height - 4.0)
        elif tab_pos_side == "left":
            panel_x, panel_y = float(tab_width_attr + 2), 2.0
            panel_w = max(10.0, container_w - tab_width_attr - 4.0)
            panel_h = max(10.0, container_h - 4.0)
        elif tab_pos_side == "right":
            panel_x, panel_y = 2.0, 2.0
            panel_w = max(10.0, container_w - tab_width_attr - 4.0)
            panel_h = max(10.0, container_h - 4.0)
        else:
            panel_x, panel_y = 2.0, float(tab_height + 2)
            panel_w = max(10.0, container_w - 4.0)
            panel_h = max(10.0, container_h - tab_height - 4.0)

        for i, tab in enumerate(tabs):
            is_active = (i == self.active_tab_index)
            tab.setVisible(is_active)
            tab.setPos(panel_x, panel_y)
            tab.attributes["left"] = str(int(panel_x))
            tab.attributes["top"] = str(int(panel_y))
            try:
                tab.resize_item(panel_w, panel_h)
            except ValueError:
                pass
        self.update_z_orders()

    def update_layout_stack(self) -> None:
        """Recalculates and positions child panels within a layout_stack.

        Distributes remaining container space proportionally among expanding panels
        while respecting min/max constraints, auto_resize flags, and cross-axis alignment.
        """
        # --- REENTRANCY GUARD ---
        if getattr(self, "_updating_stack", False):
            return
        self._updating_stack = True

        try:
            if not getattr(self, "child_xui_items", None):
                return

            orientation = self.attributes.get("orientation", "vertical").lower()
            stack_rect = self.rect()
            stack_width = max(10.0, stack_rect.width())
            stack_height = max(10.0, stack_rect.height())

            border_size = int(self.attributes.get("border_size", 0))
            padding = int(self.attributes.get("padding", 0))

            def is_expanding(item: "XUIGraphicsItem") -> bool:
                return item.attributes.get("auto_resize", "true").lower() == "true"

            def get_min_max(item: "XUIGraphicsItem", orient: str) -> Tuple[float, float]:
                if orient == "vertical":
                    min_val = float(item.attributes.get("min_height", 10))
                    max_val = float(item.attributes.get("max_height", 10000))
                else:
                    min_val = float(item.attributes.get("min_width", 10))
                    max_val = float(item.attributes.get("max_width", 10000))
                return max(10.0, min_val), max(min_val, max_val)

            panels = [
                c for c in self.child_xui_items
                if isinstance(c, XUIGraphicsItem) and getattr(c, "tag_name", "") == "layout_panel"
            ]
            if not panels:
                return

            total_gap = padding * max(0, len(panels) - 1) + (border_size * 2)

            if orientation == "vertical":
                avail_width = max(10.0, stack_width - (border_size * 2))
                avail_height = max(10.0, stack_height - total_gap)

                fixed_height = sum(
                    max(10.0, c.rect().height()) for c in panels if not is_expanding(c)
                )
                remaining_height = max(0.0, avail_height - fixed_height)
                expanding_panels = [c for c in panels if is_expanding(c)]

                total_expanding_initial_size = sum(
                    max(10.0, c.rect().height()) for c in expanding_panels
                )

                current_y = float(border_size)
                max_allowed_y = stack_height - float(border_size)

                for child in panels:
                    if child in expanding_panels:
                        min_h, max_h = get_min_max(child, "vertical")
                        curr_h = max(10.0, child.rect().height())
                        if total_expanding_initial_size > 0:
                            proportional_share = remaining_height * (curr_h / total_expanding_initial_size)
                        else:
                            proportional_share = remaining_height / len(expanding_panels)
                        child_h = max(min_h, min(max_h, proportional_share))
                    else:
                        child_h = max(10.0, child.rect().height())

                    remaining_space = max(10.0, max_allowed_y - current_y)
                    child_h = min(child_h, remaining_space)
                    child_w = avail_width

                    child.setPos(float(border_size), current_y)
                    child.attributes["width"] = str(int(child_w))
                    child.attributes["height"] = str(int(child_h))

                    if child.rect().width() != child_w or child.rect().height() != child_h:
                        child.resize_item(child_w, child_h)
                    else:
                        child.setRect(0, 0, child_w, child_h)
                        child.sync_attributes_to_geometry()

                    current_y += child_h + padding
            else:
                avail_width = max(10.0, stack_width - total_gap)
                avail_height = max(10.0, stack_height - (border_size * 2))

                fixed_width = sum(
                    max(10.0, c.rect().width()) for c in panels if not is_expanding(c)
                )
                remaining_width = max(0.0, avail_width - fixed_width)
                expanding_panels = [c for c in panels if is_expanding(c)]

                total_expanding_initial_size = sum(
                    max(10.0, c.rect().width()) for c in expanding_panels
                )

                current_x = float(border_size)
                max_allowed_x = stack_width - float(border_size)

                for child in panels:
                    if child in expanding_panels:
                        min_w, max_w = get_min_max(child, "horizontal")
                        curr_w = max(10.0, child.rect().width())
                        if total_expanding_initial_size > 0:
                            proportional_share = remaining_width * (curr_w / total_expanding_initial_size)
                        else:
                            proportional_share = remaining_width / len(expanding_panels)
                        child_w = max(min_w, min(max_w, proportional_share))
                    else:
                        child_w = max(10.0, child.rect().width())

                    remaining_space = max(10.0, max_allowed_x - current_x)
                    child_w = min(child_w, remaining_space)
                    child_h = avail_height

                    child.setPos(current_x, float(border_size))
                    child.attributes["width"] = str(int(child_w))
                    child.attributes["height"] = str(int(child_h))

                    if child.rect().width() != child_w or child.rect().height() != child_h:
                        child.resize_item(child_w, child_h)
                    else:
                        child.setRect(0, 0, child_w, child_h)
                        child.sync_attributes_to_geometry()

                    current_x += child_w + padding

            self._update_stack_drag_handles(panels, orientation)

        finally:
            self._updating_stack = False

    def _update_stack_drag_handles(self, panels: List[any], orientation: str) -> None:
        """Creates, removes, and positions StackDragHandle items between layout panels based on user_resize."""
        if not hasattr(self, "_drag_handles"):
            self._drag_handles = []

        valid_adjacent_pairs = []
        for i in range(len(panels) - 1):
            p1 = panels[i]
            p2 = panels[i + 1]
            p1_resize = str(p1.attributes.get("user_resize", "false")).lower() in ("true", "1", "yes")
            p2_resize = str(p2.attributes.get("user_resize", "false")).lower() in ("true", "1", "yes")
            if p1_resize or p2_resize:
                valid_adjacent_pairs.append((i, p1, p2))

        needed_handles = len(valid_adjacent_pairs)

        while len(self._drag_handles) > needed_handles:
            handle = self._drag_handles.pop()
            if handle.scene():
                handle.scene().removeItem(handle)
            handle.setParentItem(None)

        while len(self._drag_handles) < needed_handles:
            handle = StackDragHandle(self, 0, orientation)
            self._drag_handles.append(handle)

        border_size = int(self.attributes.get("border_size", 0))
        stack_rect = self.rect()
        stack_w = max(10.0, stack_rect.width())
        stack_h = max(10.0, stack_rect.height())

        for idx, (p_index, p1, p2) in enumerate(valid_adjacent_pairs):
            handle = self._drag_handles[idx]
            handle.index = p_index
            handle.orientation = orientation

            if orientation == "vertical":
                mid_y = (p1.y() + p1.rect().height() + p2.y()) / 2.0
                handle.setRect(0, 0, max(10.0, stack_w - (border_size * 2)), 8.0)
                handle.setPos(float(border_size), mid_y - 4.0)
            else:
                mid_x = (p1.x() + p1.rect().width() + p2.x()) / 2.0
                handle.setRect(0, 0, 8.0, max(10.0, stack_h - (border_size * 2)))
                handle.setPos(mid_x - 4.0, float(border_size))
            handle.setZValue(1000.0)
            handle.setVisible(self.isVisible())

    def add_child_item(self, child_item):
        """Appends a child item to this container and triggers layout recalculations."""
        if child_item not in self.child_xui_items:
            self.child_xui_items.append(child_item)
            child_item.setParentItem(self)
        if self.tag_name == "tab_container":
            self.update_tabs()
        elif self.tag_name == "layout_stack":
            self.update_layout_stack()
        self.update_z_orders()

    def insert_child_item(self, index, child_item):
        """Inserts a child item at a specific DOM index and triggers layout updates."""
        if child_item in self.child_xui_items:
            self.child_xui_items.remove(child_item)
        index = max(0, min(index, len(self.child_xui_items)))
        self.child_xui_items.insert(index, child_item)
        child_item.setParentItem(self)
        if self.tag_name == "tab_container":
            self.update_tabs()
        elif self.tag_name == "layout_stack":
            self.update_layout_stack()
        self.update_z_orders()

    def remove_child_item(self, child_item):
        """Removes a child item from this container and updates internal Z-ordering."""
        if child_item in self.child_xui_items:
            self.child_xui_items.remove(child_item)
            child_item.setParentItem(None)
        if self.tag_name == "tab_container":
            self.update_tabs()
        elif self.tag_name == "layout_stack":
            self.update_layout_stack()
        self.update_z_orders()

    def _get_delete_rect(self):
        """Calculates the bounding rectangle for the top-right selection delete ('X') button."""
        return QRectF(self.rect().width() - 10, -10, 18, 18)

    def boundingRect(self):
        """Returns the outer drawing boundary of the item, padded for selection handles and plus buttons."""
        rect = self.rect().adjusted(-12, -12, 12, 12)
        if self.tag_name == "layout_stack":
            rect = rect.united(QRectF(-2, -26, 26, 26))
        return rect

    def _get_handles(self):
        """Generates bounding rectangles for all 8 interactive resize handles."""
        r = self.rect()
        w, h, hs = r.width(), r.height(), self.resize_handle_size
        return {
            "TL": QRectF(0, 0, hs, hs),
            "T": QRectF(w / 2 - hs / 2, 0, hs, hs),
            "TR": QRectF(w - hs, 0, hs, hs),
            "R": QRectF(w - hs, h / 2 - hs / 2, hs, hs),
            "BR": QRectF(w - hs, h - hs, hs, hs),
            "B": QRectF(w / 2 - hs / 2, h - hs, hs, hs),
            "BL": QRectF(0, h - hs, hs, hs),
            "L": QRectF(0, h / 2 - hs / 2, hs, hs),
        }

    def _draw_handles(self, painter):
        """Renders the green 8-way resize handles and the red top-right delete button."""
        painter.setBrush(QBrush(QColor("#00FF00")))
        painter.setPen(QPen(QColor("#000000"), 1))

        for handle in self._get_handles().values():
            painter.drawRect(handle)

        del_rect = self._get_delete_rect()
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(QBrush(QColor("#D32F2F")))
        painter.setPen(QPen(QColor("#FFFFFF"), 1.5))
        painter.drawEllipse(del_rect)
        painter.setFont(QFont("SansSerif", 8, QFont.Bold))
        painter.drawText(del_rect, Qt.AlignCenter, "X")

    def mousePressEvent(self, event):
        """Handles mouse click interactions for tab creation, tab switching, and resize grabs."""
        if event.button() == Qt.LeftButton:
            pos = event.pos()

            if self.tag_name == "layout_stack":
                if hasattr(self, '_plus_btn_rect') and self._plus_btn_rect and self._plus_btn_rect.contains(pos):
                    actual_panels = [
                        c for c in self.child_xui_items
                        if isinstance(c, XUIGraphicsItem) and getattr(c, "tag_name", "") == "layout_panel"
                    ]
                    new_idx = len(actual_panels) + 1

                    new_panel = XUIGraphicsItem("layout_panel", {
                        "name": f"panel_{new_idx}",
                        "auto_resize": "true",
                        "width": self.attributes.get("width", "200"),
                        "height": "100"
                    })
                    new_panel.source_file = self.source_file
                    self.add_child_item(new_panel)

                    if hasattr(self.scene(), 'canvas_container') and self.scene().canvas_container:
                        self.scene().canvas_container.item_modified_signal.emit(self)

                    self.scene().update()
                    event.accept()
                    return

            if self.tag_name == "tab_container":
                if hasattr(self, '_plus_btn_rect') and self._plus_btn_rect and self._plus_btn_rect.contains(pos):
                    actual_panels = [c for c in self.child_xui_items if c.tag_name in ["panel", "layout_panel"]]
                    new_idx = len(actual_panels) + 1

                    new_panel = XUIGraphicsItem("panel", {"label": f"New Tab {new_idx}", "name": f"tab_{new_idx}"})
                    new_panel.source_file = self.source_file
                    self.add_child_item(new_panel)

                    self.active_tab_index = new_idx - 1
                    self.update_tabs()

                    if hasattr(self.scene(), 'canvas_container'):
                        self.scene().canvas_container.item_modified_signal.emit(self)

                    self.scene().update()
                    event.accept()
                    return

                if hasattr(self, '_tab_header_rects') and self._tab_header_rects:
                    for idx, tab_rect in self._tab_header_rects:
                        if tab_rect.contains(pos):
                            self.active_tab_index = idx
                            self.update_tabs()
                            self.scene().update()

                            if hasattr(self.scene(), 'canvas_container'):
                                self.scene().canvas_container.item_modified_signal.emit(self)

                            super().mousePressEvent(event)
                            return

            if self.isSelected():
                if self._get_delete_rect().contains(pos):
                    if hasattr(self.scene(), 'canvas_container'):
                        self.scene().canvas_container.delete_item(self)
                    event.accept()
                    return

                handles = self._get_handles()
                for h_id, r in handles.items():
                    if r.contains(pos):
                        self.resizing = True
                        self.resize_dir = h_id
                        event.accept()
                        return

        super().mousePressEvent(event)

    def hoverMoveEvent(self, event):
        if not self.isSelected():
            self.setCursor(QCursor(Qt.ArrowCursor))
            return super().hoverMoveEvent(event)

        pos = event.pos()
        handles = self._get_handles()

        if self._get_delete_rect().contains(pos):
            self.setCursor(QCursor(Qt.PointingHandCursor))
        elif handles["TL"].contains(pos) or handles["BR"].contains(pos):
            self.setCursor(QCursor(Qt.SizeFDiagCursor))
        elif handles["TR"].contains(pos) or handles["BL"].contains(pos):
            self.setCursor(QCursor(Qt.SizeBDiagCursor))
        elif handles["T"].contains(pos) or handles["B"].contains(pos):
            self.setCursor(QCursor(Qt.SizeVerCursor))
        elif handles["L"].contains(pos) or handles["R"].contains(pos):
            self.setCursor(QCursor(Qt.SizeHorCursor))
        else:
            self.setCursor(QCursor(Qt.SizeAllCursor))

        super().hoverMoveEvent(event)

    def mouseMoveEvent(self, event):
        """Processes mouse drag events to perform grid-snapped resizing and live stack reordering."""
        if self.resizing and self.resize_dir:
            scene_pos = self.mapToScene(event.pos())
            parent_pos = self.parentItem().mapFromScene(scene_pos) if self.parentItem() else scene_pos

            cur_pos = self.pos()
            cur_rect = self.rect()

            new_x, new_y = cur_pos.x(), cur_pos.y()
            new_w, new_h = cur_rect.width(), cur_rect.height()
            canvas = getattr(self.scene(), 'canvas_container', None) or self.scene()
            snapping_enabled = getattr(canvas, 'grid_snapping_enabled', True)
            grid_size = getattr(canvas, 'grid_size', 10)

            if snapping_enabled and grid_size > 0:
                snapped_x = round(parent_pos.x() / grid_size) * grid_size
                snapped_y = round(parent_pos.y() / grid_size) * grid_size
            else:
                snapped_x = parent_pos.x()
                snapped_y = parent_pos.y()

            if "L" in self.resize_dir:
                diff = snapped_x - cur_pos.x()
                new_w = max(10, cur_rect.width() - diff)
                if new_w > 10:
                    new_x = snapped_x
            elif "R" in self.resize_dir:
                new_w = max(10, snapped_x - cur_pos.x())

            if "T" in self.resize_dir:
                diff = snapped_y - cur_pos.y()
                new_h = max(10, cur_rect.height() - diff)
                if new_h > 10:
                    new_y = snapped_y
            elif "B" in self.resize_dir:
                new_h = max(10, snapped_y - cur_pos.y())

            # If resizing a panel inside a stack, lock cross-axis and disable auto_resize
            parent = self.parentItem()
            if parent and getattr(parent, "tag_name", "") == "layout_stack":
                orient = parent.attributes.get("orientation", "vertical").lower()
                border_size = int(parent.attributes.get("border_size", 0))
                if orient == "vertical":
                    new_w = parent.rect().width() - (border_size * 2)
                    new_x = float(border_size)
                    max_h = max(10.0, parent.rect().height() - cur_pos.y() - border_size)
                    new_h = min(new_h, max_h)
                else:
                    new_h = parent.rect().height() - (border_size * 2)
                    new_y = float(border_size)
                    max_w = max(10.0, parent.rect().width() - cur_pos.x() - border_size)
                    new_w = min(new_w, max_w)

            if new_x != cur_pos.x() or new_y != cur_pos.y():
                self.setPos(new_x, new_y)
            if new_w != cur_rect.width() or new_h != cur_rect.height():
                self.resize_item(new_w, new_h)

            if parent and getattr(parent, "tag_name", "") == "layout_stack":
                if hasattr(parent, "update_layout_stack"):
                    parent.update_layout_stack()

            self.scene().update()
            event.accept()
        else:
            parent = self.parentItem()
            if parent and getattr(parent, "tag_name", "") == "layout_stack":
                # Handle live interactive reordering when dragging panels across siblings
                scene_pos = self.mapToScene(event.pos())
                parent_pos = parent.mapFromScene(scene_pos)
                orient = parent.attributes.get("orientation", "vertical").lower()

                siblings = [c for c in parent.child_xui_items if isinstance(c, XUIGraphicsItem)]
                if self in siblings and len(siblings) > 1:
                    idx = siblings.index(self)
                    if orient == "vertical":
                        if idx > 0 and parent_pos.y() < siblings[idx - 1].y() + (siblings[idx - 1].rect().height() / 2.0):
                            parent.child_xui_items.remove(self)
                            parent.child_xui_items.insert(idx - 1, self)
                            parent.update_layout_stack()
                            parent.update_z_orders()
                            if hasattr(self.scene(), 'canvas_container'):
                                self.scene().canvas_container.item_modified_signal.emit(parent)
                        elif idx < len(siblings) - 1 and parent_pos.y() > siblings[idx + 1].y() + (siblings[idx + 1].rect().height() / 2.0):
                            parent.child_xui_items.remove(self)
                            parent.child_xui_items.insert(idx + 1, self)
                            parent.update_layout_stack()
                            parent.update_z_orders()
                            if hasattr(self.scene(), 'canvas_container'):
                                self.scene().canvas_container.item_modified_signal.emit(parent)
                    else:
                        if idx > 0 and parent_pos.x() < siblings[idx - 1].x() + (siblings[idx - 1].rect().width() / 2.0):
                            parent.child_xui_items.remove(self)
                            parent.child_xui_items.insert(idx - 1, self)
                            parent.update_layout_stack()
                            parent.update_z_orders()
                            if hasattr(self.scene(), 'canvas_container'):
                                self.scene().canvas_container.item_modified_signal.emit(parent)
                        elif idx < len(siblings) - 1 and parent_pos.x() > siblings[idx + 1].x() + (siblings[idx + 1].rect().width() / 2.0):
                            parent.child_xui_items.remove(self)
                            parent.child_xui_items.insert(idx + 1, self)
                            parent.update_layout_stack()
                            parent.update_z_orders()
                            if hasattr(self.scene(), 'canvas_container'):
                                self.scene().canvas_container.item_modified_signal.emit(parent)
                event.accept()
            else:
                super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Finalizes resizing operations and emits item modification signals."""
        if self.resizing:
            self.resizing = False
            self.resize_dir = None
            self.sync_attributes_to_geometry()

            if self.tag_name == "tab_container":
                self.update_tabs()
            elif self.tag_name == "layout_stack":
                self.update_layout_stack()

            if hasattr(self.scene(), 'canvas_container'):
                self.scene().canvas_container.item_modified_signal.emit(self)
        super().mouseReleaseEvent(event)

    def validate(self):
        """Evaluates the item against Second Life XUI layout and syntax rules."""
        errors, warnings = [], []
        if self.tag_name not in ["panel", "layout_panel", "text", "view_border", "icon", "window_shade", "accordion", "scroll_list"]:
            if not self.attributes.get("name") or self.attributes.get("name") == "unnamed":
                warnings.append(f"Bad Practice: Missing or 'unnamed' name attribute for {self.tag_name}.")

        if self.tag_name == "layout_panel":
            parent = self.parentItem()
            if not isinstance(parent, XUIGraphicsItem) or parent.tag_name != "layout_stack":
                errors.append(f"Syntax Error: <layout_panel> must be a direct child of <layout_stack>.")

        has_left, has_right = "left" in self.attributes, "right" in self.attributes
        follows = self.attributes.get("follows", "").lower()
        normalized_follows = follows.replace(" ", "|").replace(",", "|")
        follows_list = [f.strip() for f in normalized_follows.split("|") if f.strip()]

        if has_left and has_right and "left" not in follows_list and "right" not in follows_list and "all" not in follows_list:
            warnings.append("Bad Practice: Opposing anchors (left & right) used without matching 'follows' flags.")

        return errors, warnings

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Optional[QWidget] = None) -> None:
        """Renders the complete graphical representation of the XUI widget on the canvas."""
        try:
            is_selected = bool(option.state & QStyle.State_Selected)
            option.state &= ~QStyle.State_Selected

            painter.setClipRect(option.exposedRect)
            rect = self.rect()

            tm = TextureManager.get()
            get_pixmap = tm.get_pixmap if tm else lambda k: None

            is_checkbox_or_radio = self.tag_name in ("check_box", "radio_item")

            # 1. Resolve Background / 9-Slice Textures
            bg_texture_key = None
            bg_keys = ["background_image", "bg_image", "bg_opaque_image", "chrome_image"]
            if not is_checkbox_or_radio:
                bg_keys = ["image_unselected", "background_image", "bg_image", "bg_opaque_image", "image", "chrome_image"]

            for attr_key in bg_keys:
                val = self.attributes.get(attr_key)
                if val and str(val).strip():
                    bg_texture_key = str(val).strip()
                    break

            if not bg_texture_key:
                if self.tag_name == "floater":
                    bg_texture_key = "floater_bg"
                elif self.tag_name == "panel":
                    bg_texture_key = "panel_bg"
                elif self.tag_name == "button" and not is_checkbox_or_radio:
                    bg_texture_key = "PushButton_Off"
                elif self.tag_name == "combo_box":
                    bg_texture_key = "combobox_off"
                elif self.tag_name == "line_editor":
                    bg_texture_key = "lineeditor_bg"

            bg_pixmap = get_pixmap(bg_texture_key) if bg_texture_key else None

            # --- Special Case: Floater Window ---
            if self.tag_name == "floater":
                if bg_pixmap and not bg_pixmap.isNull():
                    draw_9_slice(painter, bg_pixmap, rect)
                else:
                    painter.fillRect(rect, QColor("#222222"))
                    painter.setPen(QPen(QColor("#555555"), 1))
                    painter.drawRect(rect)

                header_rect = QRectF(rect.x(), rect.y(), rect.width(), 24)
                header_pixmap = get_pixmap("floater_header")
                if header_pixmap and not header_pixmap.isNull():
                    draw_9_slice(painter, header_pixmap, header_rect, 4, 4, 4, 4)
                else:
                    painter.fillRect(header_rect, QColor("#333333"))

                painter.setPen(QPen(QColor("#FFFFFF")))
                title = self.attributes.get("title") or self.attributes.get("name") or "Floater"
                painter.drawText(header_rect.adjusted(8, 0, -8, 0), Qt.AlignLeft | Qt.AlignVCenter, title)
                self._draw_selection_box(painter, rect, is_selected)
                return

            # --- Special Case: Progress Bar ---
            elif self.tag_name == "progress_bar":
                track_rect = QRectF(rect.x(), rect.y(), rect.width(), rect.height())
                painter.fillRect(track_rect, QColor("#111111"))
                painter.setPen(QPen(QColor("#444444"), 1))
                painter.drawRect(track_rect)

                try:
                    val_str = (self.attributes.get("value") or self.attributes.get("initial_val") or
                               self.attributes.get("val") or "0.5")
                    progress_val = max(0.0, min(1.0, float(val_str)))
                except ValueError:
                    progress_val = 0.5

                fill_w = max(0.0, (rect.width() - 4) * progress_val)
                if fill_w > 0:
                    fill_rect = QRectF(rect.x() + 2, rect.y() + 2, fill_w, rect.height() - 4)
                    painter.fillRect(fill_rect, QColor("#1e457c"))
                self._draw_selection_box(painter, rect, is_selected)
                return

            # --- Special Case: Pure Text Label ---
            elif self.tag_name == "text":
                painter.setPen(QPen(QColor("#FFFFFF")))
                txt_label = (self.attributes.get("label") or self.attributes.get("name") or
                             getattr(self, 'inner_text', '') or "Text Label")
                if txt_label == "unnamed":
                    txt_label = "Text Label"

                halign_str = self.attributes.get("halign", "left").lower()
                valign_str = self.attributes.get("valign", "center").lower()
                align_flags = Qt.TextSingleLine
                align_flags |= Qt.AlignHCenter if halign_str == "center" else (
                    Qt.AlignRight if halign_str == "right" else Qt.AlignLeft)
                align_flags |= Qt.AlignTop if valign_str == "top" else (
                    Qt.AlignBottom if valign_str == "bottom" else Qt.AlignVCenter)

                painter.drawText(rect.adjusted(2, 2, -2, -2), align_flags, txt_label)
                self._draw_selection_box(painter, rect, is_selected)
                return

            # --- Special Case: Tab Container ---
            elif self.tag_name == "tab_container":
                self._draw_tab_container_internal(painter, rect)
                return

            # --- Special Case: Layout Stack ---
            elif self.tag_name == "layout_stack":
                painter.fillRect(rect, QColor("#1a1a1a"))
                pen = QPen(QColor("#3d5a80"), 1, Qt.DashLine)
                painter.setPen(pen)
                painter.drawRect(rect)
                self._plus_btn_rect = QRectF(0, -22, 20, 20)
                painter.fillRect(self._plus_btn_rect, QColor("#2d4a60"))
                painter.setPen(QPen(QColor("#FFFFFF"), 1))
                painter.drawRect(self._plus_btn_rect)
                painter.setFont(QFont("SansSerif", 10, QFont.Bold))
                painter.drawText(self._plus_btn_rect, Qt.AlignCenter, "+")
                self._draw_selection_box(painter, rect, is_selected)
                return

            # --- Special Case: Layout Panel ---
            elif self.tag_name == "layout_panel":
                painter.fillRect(rect, QColor("#222222"))
                pen = QPen(QColor("#4f6d7a" if is_selected else "#444444"), 1, Qt.SolidLine)
                painter.setPen(pen)
                painter.drawRect(rect)
                self._draw_selection_box(painter, rect, is_selected)
                return

            # --- Standard Controls & Imported Viewer Widgets ---
            if bg_pixmap and not bg_pixmap.isNull():
                if self.tag_name in ("icon", "image", "avatar_icon", "view_border"):
                    painter.drawPixmap(rect, bg_pixmap, QRectF(bg_pixmap.rect()))
                else:
                    draw_9_slice(painter, bg_pixmap, rect)
            else:
                painter.fillRect(rect, QColor("#3a3a3a"))
                painter.setPen(QPen(QColor("#555555"), 1))
                painter.drawRect(rect)

            # 2. Resolve Control Icons / Overlays
            icon_texture_key = None
            if is_checkbox_or_radio:
                is_checked = str(self.attributes.get("value", "")).lower() in ["true", "1", "yes"] or \
                             str(self.attributes.get("initial_value", "")).lower() in ["true", "1", "yes"]
                if is_checked:
                    icon_texture_key = self.attributes.get("image_selected") or (
                        "Checkbox_On" if self.tag_name == "check_box" else "RadioButton_On")
                else:
                    icon_texture_key = self.attributes.get("image_unselected") or (
                        "Checkbox_Off" if self.tag_name == "check_box" else "RadioButton_Off")
            else:
                icon_texture_key = (self.attributes.get("default_icon_name") or
                                    self.attributes.get("icon") or
                                    self.attributes.get("image_name") or
                                    self.attributes.get("image_overlay") or
                                    (self.attributes.get("image") if self.tag_name in ("icon", "image") else None))

            if icon_texture_key:
                icon_pixmap = get_pixmap(icon_texture_key)
                if icon_pixmap and not icon_pixmap.isNull():
                    iw, ih = float(icon_pixmap.width()), float(icon_pixmap.height())
                    if is_checkbox_or_radio:
                        box_size = min(max(12.0, ih), rect.height() - 4.0)
                        target_rect = QRectF(rect.left() + 4.0, rect.center().y() - (box_size / 2.0), box_size, box_size)
                    else:
                        avail_w, avail_h = max(1.0, rect.width() - 4.0), max(1.0, rect.height() - 4.0)
                        if (iw > avail_w or ih > avail_h or self.tag_name in ("icon", "image")) and iw > 0 and ih > 0:
                            scale = min(avail_w / iw, avail_h / ih)
                            target_w, target_h = iw * scale, ih * scale
                            target_rect = QRectF(rect.center().x() - target_w / 2.0, rect.center().y() - target_h / 2.0, target_w, target_h)
                        else:
                            target_rect = QRectF(rect.center().x() - iw / 2.0, rect.center().y() - ih / 2.0, iw, ih)
                    painter.drawPixmap(target_rect, icon_pixmap, QRectF(icon_pixmap.rect()))
                elif is_checkbox_or_radio:
                    box_size = 14.0
                    target_rect = QRectF(rect.left() + 4.0, rect.center().y() - (box_size / 2.0), box_size, box_size)
                    painter.save()
                    painter.setPen(QPen(QColor("#AAAAAA"), 1.5))
                    painter.setBrush(QBrush(QColor("#222222")))
                    if self.tag_name == "radio_item":
                        painter.drawEllipse(target_rect)
                        if "on" in str(icon_texture_key).lower() or "selected" in str(icon_texture_key).lower():
                            painter.setBrush(QBrush(QColor("#FFFFFF")))
                            painter.drawEllipse(target_rect.adjusted(3, 3, -3, -3))
                    else:
                        painter.drawRect(target_rect)
                        if "on" in str(icon_texture_key).lower() or "selected" in str(icon_texture_key).lower():
                            painter.setPen(QPen(QColor("#FFFFFF"), 2))
                            painter.drawLine(target_rect.left() + 3, target_rect.center().y(), target_rect.center().x(), target_rect.bottom() - 3)
                            painter.drawLine(target_rect.center().x(), target_rect.bottom() - 3, target_rect.right() - 3, target_rect.top() + 3)
                    painter.restore()

            # 3. Draw Control Label Text
            label_text = self.attributes.get("label") or self.attributes.get("label_selected")
            if not label_text and self.tag_name in ("button", "check_box", "radio_item", "menu_item", "flyout_button"):
                name_val = self.attributes.get("name", "")
                if name_val and name_val != "unnamed":
                    label_text = name_val

            if label_text:
                painter.setPen(QPen(QColor("#FFFFFF")))
                if is_checkbox_or_radio:
                    painter.drawText(rect.adjusted(22, 0, -4, 0), Qt.AlignLeft | Qt.AlignVCenter, label_text)
                else:
                    painter.drawText(rect.adjusted(6, 0, -6, 0), Qt.AlignCenter | Qt.AlignVCenter, label_text)

            self._draw_selection_box(painter, rect, is_selected)
        except Exception as e:
            print(f"[Verbose Error] XUIGraphicsItem.paint failed on <{self.tag_name}>: {e}")

    def _draw_tab_container_internal(self, painter, rect):
        """Helper method extracted to keep tab rendering clean and exception-safe."""
        try:
            painter.fillRect(rect, QColor("#1e1e1e"))
            painter.setPen(QPen(QColor("#555555"), 1))
            painter.drawRect(rect)

            tab_pos_side = self.attributes.get("tab_position", "top").lower()
            tab_height = int(self.attributes.get("tab_height", 21))
            tab_width_attr = int(self.attributes.get("tab_width", 80))
            min_w, max_w = int(self.attributes.get("tab_min_width", 60)), int(self.attributes.get("tab_max_width", 150))

            actual_panels = [c for c in getattr(self, 'child_xui_items', []) if c.tag_name in ["panel", "layout_panel"]]
            self._tab_header_rects = []
            self._plus_btn_rect = None

            if tab_pos_side == "top":
                header_rect = QRectF(rect.x(), rect.y(), rect.width(), tab_height)
                divider_line = QLineF(rect.left(), rect.top() + tab_height, rect.right(), rect.top() + tab_height)
            elif tab_pos_side == "bottom":
                header_rect = QRectF(rect.x(), rect.bottom() - tab_height, rect.width(), tab_height)
                divider_line = QLineF(rect.left(), rect.bottom() - tab_height, rect.right(), rect.bottom() - tab_height)
            elif tab_pos_side == "left":
                header_rect = QRectF(rect.x(), rect.y(), tab_width_attr, rect.height())
                divider_line = QLineF(rect.left() + tab_width_attr, rect.top(), rect.left() + tab_width_attr, rect.bottom())
            elif tab_pos_side == "right":
                header_rect = QRectF(rect.right() - tab_width_attr, rect.y(), tab_width_attr, rect.height())
                divider_line = QLineF(rect.right() - tab_width_attr, rect.top(), rect.right() - tab_width_attr, rect.bottom())
            else:
                header_rect = QRectF(rect.x(), rect.y(), rect.width(), tab_height)
                divider_line = QLineF(rect.left(), rect.top() + tab_height, rect.right(), rect.top() + tab_height)

            painter.fillRect(header_rect, QColor("#141414"))
            painter.drawLine(divider_line)

            offset = 2
            for i, tab_panel in enumerate(actual_panels):
                tab_label = tab_panel.attributes.get("label", tab_panel.attributes.get("title", tab_panel.attributes.get("name", "Unnamed Tab")))
                is_active = (i == getattr(self, 'active_tab_index', 0))

                if tab_pos_side in ["top", "bottom"]:
                    calc_size = max(min_w, min(max_w, len(tab_label) * 7 + 20)) + (20 if is_active else 0)
                    tab_rect = QRectF(rect.x() + offset, header_rect.y(), calc_size, tab_height)
                else:
                    calc_size = max(20, tab_height + (6 if is_active else 0))
                    tab_rect = QRectF(header_rect.x(), rect.y() + offset, tab_width_attr, calc_size)

                self._tab_header_rects.append((i, tab_rect))

                if is_active:
                    painter.fillRect(tab_rect, QColor("#2b2b2b"))
                    painter.setPen(QPen(QColor("#1e457c"), 2))
                    if tab_pos_side == "top":
                        painter.drawLine(tab_rect.left(), tab_rect.bottom(), tab_rect.right(), tab_rect.bottom())
                    elif tab_pos_side == "bottom":
                        painter.drawLine(tab_rect.left(), tab_rect.top(), tab_rect.right(), tab_rect.top())
                    elif tab_pos_side == "left":
                        painter.drawLine(tab_rect.right(), tab_rect.top(), tab_rect.right(), tab_rect.bottom())
                    elif tab_pos_side == "right":
                        painter.drawLine(tab_rect.left(), tab_rect.top(), tab_rect.left(), tab_rect.bottom())
                    painter.setPen(QPen(QColor("#FFFFFF")))
                else:
                    painter.fillRect(tab_rect, QColor("#222222"))
                    painter.setPen(QPen(QColor("#888888")))

                painter.drawRect(tab_rect)
                painter.drawText(tab_rect.adjusted(4, 0, -4, 0), Qt.AlignCenter | Qt.AlignVCenter, tab_label)
                offset += calc_size

            if tab_pos_side in ["top", "bottom"]:
                self._plus_btn_rect = QRectF(rect.x() + offset + 4, header_rect.y() + 2, 20, tab_height - 4)
            else:
                self._plus_btn_rect = QRectF(header_rect.x() + 2, rect.y() + offset + 4, tab_width_attr - 4, 20)

            painter.fillRect(self._plus_btn_rect, QColor("#333333"))
            painter.setPen(QPen(QColor("#AAAAAA")))
            painter.drawRect(self._plus_btn_rect)
            painter.drawText(self._plus_btn_rect, Qt.AlignCenter, "+")
            self._draw_selection_box(painter, rect)
        except Exception as e:
            print(f"[Verbose Error] _draw_tab_container_internal failed: {e}")

    def _draw_selection_box(self, painter: QPainter, rect: QRectF, is_selected: bool = False) -> None:
        """Draws the bounding box, 8 resize handles, and red delete badge when selected."""
        if not (is_selected or self.isSelected()):
            return

        vis_val = str(self.attributes.get("visible", "true")).lower()
        is_visible = vis_val in ["true", "1", "yes"]

        selection_color = QColor("#00FF00") if is_visible else QColor("#FFD700")

        painter.save()
        pen = QPen(selection_color, 1.5, Qt.SolidLine)
        pen.setCosmetic(True)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(rect)

        handle_size = 6.0
        half = handle_size / 2.0
        left, top, right, bottom = rect.left(), rect.top(), rect.right(), rect.bottom()
        mid_x, mid_y = rect.center().x(), rect.center().y()

        handle_points = [
            (left, top), (mid_x, top), (right, top),
            (right, mid_y), (right, bottom), (mid_x, bottom),
            (left, bottom), (left, mid_y)
        ]

        painter.setBrush(QBrush(selection_color))
        painter.setPen(QPen(QColor("#000000"), 1))

        for x, y in handle_points:
            painter.drawRect(QRectF(x - half, y - half, handle_size, handle_size))

        badge_size = 14.0
        badge_rect = QRectF(right - (badge_size / 2.0), top - (badge_size / 2.0), badge_size, badge_size)

        painter.setBrush(QBrush(QColor("#FF0000")))
        painter.setPen(QPen(QColor("#FFFFFF"), 1))
        painter.drawEllipse(badge_rect)

        painter.setPen(QPen(QColor("#FFFFFF"), 1.5, Qt.SolidLine, Qt.RoundCap))
        margin = 4.0
        painter.drawLine(
            badge_rect.left() + margin, badge_rect.top() + margin,
            badge_rect.right() - margin, badge_rect.bottom() - margin
        )
        painter.drawLine(
            badge_rect.right() - margin, badge_rect.top() + margin,
            badge_rect.left() + margin, badge_rect.bottom() - margin
        )

        painter.restore()