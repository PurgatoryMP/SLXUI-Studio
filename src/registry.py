
LLVIEW_PARAMS = {
    # Designer Utilities
    "designer_export_geometry": {"type": "bool", "default": "true", "group": "Designer Tools"},

    # General & Lifecycle
    "name": {"type": "str", "default": "unnamed", "group": "LLView (General)"},
    "enabled": {"type": "bool", "default": "true", "group": "LLView (General)"},
    "visible": {"type": "bool", "default": "true", "group": "LLView (General)"},
    "mouse_opaque": {"type": "bool", "default": "true", "group": "LLView (General)"},
    "use_bounding_rect": {"type": "bool", "default": "false", "group": "LLView (General)"},
    "from_xui": {"type": "bool", "default": "true", "group": "LLView (General)"},
    "focus_root": {"type": "bool", "default": "false", "group": "LLView (General)"},
    "tab_group": {"type": "int", "default": "0", "group": "LLView (General)"},
    "default_tab_group": {"type": "int", "default": "", "group": "LLView (General)"},
    "tool_tip": {"type": "str", "default": "", "group": "LLView (General)"},
    "sound_flags": {"type": "combo", "options": ["MOUSE_UP", "MOUSE_DOWN"], "default": "MOUSE_UP",
                    "group": "LLView (General)"},
    "hover_cursor": {"type": "str", "default": "UI_CURSOR_ARROW", "group": "LLView (General)"},

    # Layout & Positioning (LLRect / Relative / Follows)
    "layout": {"type": "combo", "options": ["topleft", "bottomleft"], "default": "topleft", "group": "LLView (Layout)"},
    "follows": {"type": "str", "default": "left|top", "group": "LLView (Layout)"},
    "left": {"type": "int", "default": "0", "group": "LLView (Rect Absolute)"},
    "top": {"type": "int", "default": "0", "group": "LLView (Rect Absolute)"},
    "right": {"type": "int", "default": "", "group": "LLView (Rect Absolute)"},
    "bottom": {"type": "int", "default": "", "group": "LLView (Rect Absolute)"},
    "width": {"type": "int", "default": "100", "group": "LLView (Rect Absolute)"},
    "height": {"type": "int", "default": "20", "group": "LLView (Rect Absolute)"},
    "left_pad": {"type": "int", "default": "", "group": "LLView (Rect Relative)"},
    "top_pad": {"type": "int", "default": "", "group": "LLView (Rect Relative)"},
    "left_delta": {"type": "int", "default": "", "group": "LLView (Rect Relative)"},
    "top_delta": {"type": "int", "default": "", "group": "LLView (Rect Relative)"},
    "bottom_delta": {"type": "int", "default": "", "group": "LLView (Rect Relative)"},
}

LLUICTRL_PARAMS = {
    **LLVIEW_PARAMS,
    "label": {"type": "str", "default": "", "group": "LLUICtrl"},
    "tab_stop": {"type": "bool", "default": "true", "group": "LLUICtrl"},
    "chrome": {"type": "bool", "default": "false", "group": "LLUICtrl"},
    "requests_front": {"type": "bool", "default": "false", "group": "LLUICtrl"},
    "value": {"type": "str", "default": "", "group": "LLUICtrl (Data Binding)"},
    "initial_value": {"type": "str", "default": "", "group": "LLUICtrl (Data Binding)"},
    "control_name": {"type": "str", "default": "", "group": "LLUICtrl (Data Binding)"},
    "enabled_controls": {"type": "combo", "options": ["none", "spec", "config", "prefs", "global", "all"],
                         "default": "none", "group": "LLUICtrl (Data Binding)"},
    "controls_visibility": {"type": "combo", "options": ["none", "spec", "config", "prefs", "global", "all"],
                            "default": "none", "group": "LLUICtrl (Data Binding)"},
    "font": {"type": "combo",
             "options": ["SansSerif", "SansSerifSmall", "SansSerifBig", "SansSerifHuge", "Monospace", "Cursive"],
             "default": "SansSerifSmall", "group": "LLUICtrl (Typography)"},
    "halign": {"type": "combo", "options": ["left", "center", "right"], "default": "left",
               "group": "LLUICtrl (Typography)"},
    "valign": {"type": "combo", "options": ["top", "center", "vcenter", "bottom", "baseline"], "default": "vcenter",
               "group": "LLUICtrl (Typography)"},
    "commit_callback": {"type": "str", "default": "", "group": "LLUICtrl (Callbacks)"},
    "init_callback": {"type": "str", "default": "", "group": "LLUICtrl (Callbacks)"},
    "validate_callback": {"type": "str", "default": "", "group": "LLUICtrl (Callbacks)"},
    "mouseenter_callback": {"type": "str", "default": "", "group": "LLUICtrl (Callbacks)"},
    "mouseleave_callback": {"type": "str", "default": "", "group": "LLUICtrl (Callbacks)"},
}

# BACKWARD COMPATIBILITY ALIAS: Prevents ImportError in inspector.py and graphics_item.py
UNIVERSAL_ATTRIBUTES = {**LLVIEW_PARAMS, **LLUICTRL_PARAMS}

XUI_REGISTRY = {
    "Containers & Windows": {
        "floater": {
            "width": 450, "height": 350, "color": "#222222", "desc": "Free-floating top-level window (LLFloater)",
            "params": {
                **LLVIEW_PARAMS,
                "title": {"type": "str", "default": "FLOATER", "group": "LLFloater"},
                "image_background": {"type": "str", "default": "Window_Background", "group": "LLFloater (Textures)"},
                "can_resize": {"type": "bool", "default": "false", "group": "LLFloater"},
                "save_rect": {"type": "bool", "default": "true", "group": "LLFloater"},
                "single_instance": {"type": "bool", "default": "true", "group": "LLFloater"},
                "legacy_header_height": {"type": "int", "default": "18", "group": "LLFloater"},
            }
        },
        "panel": {
            "width": 200, "height": 150, "color": "#2d2d2d", "desc": "Standard child container panel (LLPanel)",
            "params": {
                **LLUICTRL_PARAMS,
                "border": {"type": "bool", "default": "false", "group": "LLPanel"},
                "bg_opaque": {"type": "bool", "default": "false", "group": "LLPanel"},
                "bg_color": {"type": "str", "default": "Inspector_Background", "group": "LLPanel"},
            }
        },
        "tab_container": {
            "width": 250, "height": 180, "color": "#2a3540", "desc": "Tabbed panel switcher (LLTabContainer)",
            "params": {
                **LLUICTRL_PARAMS,
                "tab_position": {"type": "combo", "options": ["top", "bottom", "left"], "default": "top", "group": "LLTabContainer"},
                "tab_top_image_unselected": {"type": "str", "default": "TabTop_Middle_Off", "group": "LLTabContainer (Textures)"},
                "tab_top_image_selected": {"type": "str", "default": "TabTop_Middle_Selected", "group": "LLTabContainer (Textures)"},
                "tab_height": {"type": "int", "default": "21", "group": "LLTabContainer"},
                "tab_min_width": {"type": "int", "default": "60", "group": "LLTabContainer"},
                "tab_max_width": {"type": "int", "default": "150", "group": "LLTabContainer"},
            }
        },
        "layout_stack": {"width": 220, "height": 200, "desc": "Arranges layout panels linearly", "params": {**LLVIEW_PARAMS, "orientation": {"type": "combo", "options": ["horizontal", "vertical"], "default": "vertical", "group": "LLLayoutStack"}}},
        "layout_panel": {"width": 180, "height": 120, "desc": "Layout container embedded inside stacks", "params": {**LLVIEW_PARAMS, "auto_resize": {"type": "bool", "default": "true", "group": "LLLayoutPanel"}}},
        "accordion": {"width": 200, "height": 250, "desc": "Collapsible vertical accordion container", "params": {**LLVIEW_PARAMS}},
    },
    "Buttons & Toggles": {
        "button": {
            "width": 90, "height": 22, "color": "#4e5d6c", "label": "Button", "desc": "Standard clickable button (LLButton)",
            "params": {
                **LLUICTRL_PARAMS,
                "label_selected": {"type": "str", "default": "", "group": "LLButton"},
                "image_unselected": {"type": "str", "default": "PushButton_Off", "group": "LLButton (Textures)"},
                "image_selected": {"type": "str", "default": "PushButton_On", "group": "LLButton (Textures)"},
                "image_pressed": {"type": "str", "default": "PushButton_Press", "group": "LLButton (Textures)"},
                "image_disabled": {"type": "str", "default": "PushButton_Disabled", "group": "LLButton (Textures)"},
                "is_toggle": {"type": "bool", "default": "false", "group": "LLButton"},
                "pad_right": {"type": "int", "default": "4", "group": "LLButton"},
            }
        },
        "check_box": {
            "width": 120, "height": 16, "color": "#3b5249", "label": "Check Box", "desc": "Standard toggle checkbox (LLCheckBoxCtrl)",
            "params": {
                **LLUICTRL_PARAMS,
                "image_unselected": {"type": "str", "default": "Checkbox_Off", "group": "LLCheckBoxCtrl (Textures)"},
                "image_selected": {"type": "str", "default": "Checkbox_On", "group": "LLCheckBoxCtrl (Textures)"},
                "radio_style": {"type": "bool", "default": "false", "group": "LLCheckBoxCtrl"},
            }
        },
    },
    "Text & Editors": {
        "text": {"width": 100, "height": 16, "label": "Label Text", "desc": "Static text display", "params": {**LLUICTRL_PARAMS, "wrap": {"type": "bool", "default": "false", "group": "LLTextBox"}}},
        "line_editor": {
            "width": 140, "height": 20, "desc": "Single-line string entry input field",
            "params": {
                **LLUICTRL_PARAMS,
                "image_unselected": {"type": "str", "default": "TextField_Off", "group": "LLLineEditor (Textures)"},
                "max_length_bytes": {"type": "int", "default": "255", "group": "LLLineEditor"},
                "password": {"type": "bool", "default": "false", "group": "LLLineEditor"},
            }
        },
        "search_editor": {"width": 140, "height": 22, "desc": "Text entry field containing search glyphs", "params": {**LLUICTRL_PARAMS}},
    },
    "Selection & Numeric Controls": {
        "combo_box": {
            "width": 130, "height": 22, "label": "Select Option", "desc": "Selectable dropdown box",
            "params": {
                **LLUICTRL_PARAMS,
                "image_unselected": {"type": "str", "default": "ComboButton_Off", "group": "LLComboBox (Textures)"},
                "allow_text_entry": {"type": "bool", "default": "false", "group": "LLComboBox"},
            }
        },
        "slider": {"width": 150, "height": 18, "label": "Slider", "desc": "Numeric value slider with label", "params": {**LLUICTRL_PARAMS, "image_bar": {"type": "str", "default": "Slider_Track", "group": "LLSlider (Textures)"}, "min_val": {"type": "str", "default": "0", "group": "LLSliderCtrl"}}},
        "spinner": {"width": 70, "height": 20, "label": "0", "desc": "Numeric spinner box with up/down buttons", "params": {**LLUICTRL_PARAMS, "min_val": {"type": "str", "default": "0", "group": "LLSpinCtrl"}}},
    },
    "Display & Indicators": {
        "icon": {"width": 32, "height": 32, "desc": "Static graphic glyph display", "params": {**LLUICTRL_PARAMS, "image_name": {"type": "str", "default": "Lock", "group": "LLIconCtrl"}}},
        "progress_bar": {"width": 150, "height": 16, "desc": "Linear progress fill gauge", "params": {**LLVIEW_PARAMS, "image_bar": {"type": "str", "default": "ProgressBarSolid", "group": "LLProgressBar"}}},
    }
}