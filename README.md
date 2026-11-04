# FileX — Floating Universal File Converter for Windows

<p align="center">
  <img src="assets/images/logo.png" alt="FileX Logo" width="120"/>
</p>

<p align="center">
  <b>A sleek, always-on-top floating Windows desktop app that converts files instantly — drag, drop, and done.</b>
</p>

---

## ✨ Features

- 🖱️ **Drag & Drop Interface** — Drop any file onto the floating widget to convert it
- 🗂️ **Universal Converter** — Supports Images, PDFs, Documents, Spreadsheets, Presentations, Audio, and Video
- 🌙 **Dark Mode UI** — Beautiful dark-themed PySide6 interface
- 📌 **Always-on-Top Float** — Stays above all windows for instant access
- 📜 **Conversion History** — Browse all past conversions with status
- ⚙️ **Settings** — Output folder, theme, default formats, and more
- 🔔 **Windows Notifications** — Native toast notifications on conversion complete
- ⚡ **Background Processing** — Non-blocking threaded conversions

---

## 🗂️ Supported Formats

| Category      | Input Formats                         | Output Formats                        |
|---------------|---------------------------------------|---------------------------------------|
| Image         | JPG, PNG, BMP, GIF, TIFF, WEBP, ICO  | JPG, PNG, BMP, GIF, TIFF, WEBP, ICO  |
| PDF           | PDF, DOCX, TXT, HTML, Images          | PDF, DOCX, TXT, Images               |
| Document      | DOCX, DOC, TXT, HTML, MD, ODT         | DOCX, TXT, HTML, MD, PDF             |
| Spreadsheet   | XLSX, XLS, CSV, ODS                   | XLSX, XLS, CSV, PDF                  |
| Presentation  | PPTX, PPT                             | PPTX, PDF, Images                    |
| Audio         | MP3, WAV, AAC, FLAC, OGG, M4A        | MP3, WAV, AAC, FLAC, OGG             |
| Video         | MP4, AVI, MKV, MOV, WMV, FLV        | MP4, AVI, MKV, MOV, WMV, GIF        |

---

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- Windows 10/11
- [FFmpeg](https://ffmpeg.org/download.html) (required for audio/video conversion — add to PATH)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/Jinchuriki-7/FileX.git
cd FileX

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
python main.py
```

---

## 🏗️ Project Structure

```
FileX/
├── main.py                        # App entry point
├── requirements.txt
├── README.md
│
├── core/                          # Business logic
│   ├── settings_manager.py        # App settings (JSON)
│   ├── format_registry.py         # Supported formats registry
│   ├── file_detector.py           # File type detection
│   ├── history_manager.py         # Conversion history (SQLite)
│   └── conversion_manager.py      # Orchestrates conversions
│
├── converters/                    # Format-specific converters
│   ├── image_converter.py
│   ├── pdf_converter.py
│   ├── document_converter.py
│   ├── spreadsheet_converter.py
│   ├── presentation_converter.py
│   ├── audio_converter.py
│   └── video_converter.py
│
├── ui/                            # PySide6 UI
│   ├── main_window.py
│   ├── floating_widget.py
│   ├── conversion_dialog.py
│   ├── history_page.py
│   ├── settings_page.py
│   └── components/
│       ├── animated_button.py
│       ├── drop_zone.py
│       └── progress_card.py
│
├── utils/                         # Helpers
│   ├── file_utils.py
│   ├── windows_utils.py
│   └── notifications.py
│
└── assets/
    ├── styles/
    │   └── dark_theme.qss
    └── images/
```

---

## ⌨️ Usage

1. **Launch** `python main.py` — a small floating widget appears
2. **Drag & drop** any file onto the widget
3. **Select output format** in the conversion dialog
4. **Click Convert** — the file is saved to your configured output folder
5. **Click the history icon** to browse past conversions
6. **Right-click** the widget for settings and options

---

## 🔧 Configuration

Settings are stored in `%APPDATA%\FileX\settings.json`:

| Setting          | Default            | Description                     |
|------------------|--------------------|---------------------------------|
| `output_folder`  | `~/Downloads/FileX`| Where converted files are saved |
| `theme`          | `dark`             | UI theme                        |
| `always_on_top`  | `true`             | Keep widget above all windows   |
| `show_notifications` | `true`         | Windows toast notifications     |

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

Pull requests welcome! Please open an issue first to discuss major changes.

---

<p align="center">Built with ❤️ using Python & PySide6</p>
