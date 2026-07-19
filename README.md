# SLXUI-Studio: Visual UI & Skin Layout Designer for Second Life

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://doc.qt.io/qtforpython-6/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-orange.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Second Life](https://img.shields.io/badge/Platform-Second%20Life%20%7C%20Firestorm-purple.svg)](https://secondlife.com/)

**SLXUI-Studio** is an open-source, visual WYSIWYG layout editor and desktop IDE built specifically for the **Second Life** and **Firestorm Viewer** creator ecosystem. Built with Python and PySide6, it eliminates the guesswork of hand-coding raw XML by providing a real-time visual canvas, interactive widget alignment, and synchronized XML code generation for Second Life XML User Interface (XUI) layouts and custom viewer skins.

---

## 📸 Screenshots

| Modern Dark-Mode Main Window | Configuration & Theme Customization |
| :---: | :---: |
| ![Main Window](screenshots/MainWindow.PNG) | ![Preferences Dialog](screenshots/Preferences.PNG) |

---

## 🚀 Why Use SLXUI-Studio?

Historically, modding Second Life viewer UI required blindly editing XML files in text editors and repeatedly restarting the viewer in developer mode to test changes. **SLXUI-Studio** solves this by offering an end-to-end desktop development environment:
* **Visual Drag-and-Drop Canvas:** Arrange panels, buttons, and text boxes visually without touching raw XML.
* **Instant 9-Slice Texture Previews:** See how custom skin textures, TGA arrays, and J2C images render on UI elements in real time.
* **Bi-Directional Synchronization:** Click a visual widget on the canvas to highlight its exact XML code block, or edit the XML directly to watch the visual canvas update instantly.

---

## ✨ Key Features

### 🎨 Visual Canvas & Alignment Studio
* **Comprehensive Widget Palette:** Drag-and-drop pre-registered Second Life XUI widgets directly onto your layout workspace.
* **Precision Manipulation:** Real-time 8-way resize handles with dynamic grid-snapping (adjustable from 2px to 50px) and quick-toggle hotkeys.
* **Hardware Ruler Bars:** 1:1 coordinate space rulers ensure pixel-perfect widget alignment across complex panels.

### ⚡ Live Synchronized XML Compiler
* **Real-Time Compilation:** Canvas modifications instantly compile into clean, schema-compliant Second Life XML syntax.
* **Built-in XML Scanner & DOM Tree:** Features syntax highlighting and a hierarchical DOM navigation tree for rapid structural searching.
* **Smart Container Mechanics:** Native support for complex viewer container behaviors, including tab containers, layout stacks, and layout panels. Create, delete, and switch active tab panels on the fly directly within the canvas.
* **Constraint Recalculation:** Automatic follows-anchor layout recalculation to preserve nested layout constraints when resizing windows.

### 📂 Skin & Asset Pipeline Integration
* **Recursive Sub-XUI Importing:** Automatically resolves, imports, and merges secondary XML layout dependencies (such as shared headers, footers, or sub-panels).
* **Automated Asset Discovery:** Searches local working directories and systemic Second Life or Firestorm skin configuration paths to resolve missing asset packages.
* **Advanced Texture Mapping:** Supports custom skin theme parsing and live 9-slice button and texture preview rendering.

---

## 🛠️ System & Runtime Requirements

* **Python:** Version 3.10 or newer (utilizing modern structural pattern matching and debounced timers).
* **Operating System:** Fully cross-platform, natively supporting **Windows 10/11**, **macOS**, and **Linux**.
* **Target Viewers:** Compatible with official Linden Lab Second Life Viewers, Firestorm Viewer, and other third-party viewer distributions.

---

## 📦 Installation & Setup

To get started with SLXUI-Studio on your local machine, complete the following three steps:

1. **Clone the Repository:** Download the project files to your computer using your preferred Git client or by downloading the repository ZIP file directly from GitHub and extracting it to a local folder.
2. **Install Core Dependencies:** Open your command prompt or terminal and use Python's package manager to install the two required graphics and UI libraries by typing: pip install PySide6 Pillow
3. **Launch the Studio:** Navigate into your project folder inside your terminal and start the application by running: python src/main.py

---

## 🏗️ Technical Architecture & Under the Hood

SLXUI-Studio relies on a clean, decoupled architecture powered by industry-standard Python libraries:

| Module / Library | Core Responsibility |
| :--- | :--- |
| **PySide6.QtWidgets** | Powers the main IDE dashboard, 2D canvas rendering, multi-pane docking windows, and hierarchical DOM navigation trees. |
| **PySide6.QtGui** | Drives high-speed 2D hardware graphics engines and manages active GUI texture caches. |
| **PySide6.QtCore** | Handles asynchronous thread signaling, hardware drag-and-drop operations, and debounced background timers to eliminate layout lag. |
| **Pillow (PIL)** | Operates the image asset pipeline—decoding complex Second Life texture formats into standard 32-bit RGBA pixel buffers. |
| **xml.etree.ElementTree** | Executes schema-compliant parsing, serialization, and compilation of XUI DOM structures. |

---

## 🤝 Contributing & Community

Contributions, bug reports, and feature suggestions are welcome! Whether you are building custom Firestorm skins or developing experimental viewer UI, feel free to fork the repository, submit pull requests, or open an issue on GitHub.

**License:** Distributed under the GNU General Public License v3.0. See the LICENSE file in the repository for more information.