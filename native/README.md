# FileX - Native Windows 11 Desktop Application

**FileX** is a high-performance, professional native Windows desktop application built with **C#**, **.NET 10**, and **WPF-UI (Windows 11 WinUI 3 Fluent Design System)** following Clean Architecture.

FileX provides an instant offline file conversion experience using both a modern dashboard interface and an always-on-top, glassmorphic floating desktop drag-and-drop widget.

---

## 🏗 Architecture Overview

The native solution is located at `native/FileX.slnx` and adheres strictly to **Clean Architecture**:

```
native/
├── src/
│   ├── FileX.Core/                  # Pure Domain & Business Abstractions (.NET 10)
│   │   ├── Enums/                   # FileCategory, ConversionStatus
│   │   ├── Models/                  # FormatDefinition, ConversionTask, HistoryRecord, AppSettings
│   │   └── Interfaces/              # IConversionEngine, IFileDetector, IHistoryRepository, etc.
│   │
│   ├── FileX.Infrastructure/        # Concrete Implementations (.NET 10-windows)
│   │   ├── Converters/              # NativeImageConverter, NativeDocumentConverter, NativePdfConverter, etc.
│   │   ├── Persistence/             # SqliteHistoryRepository, JsonSettingsService
│   │   ├── FileDetector.cs          # Magic-bytes + extension validation engine
│   │   ├── FormatRegistry.cs        # Comprehensive format matrix & conversion mapper
│   │   └── ConversionManager.cs     # Async pipeline, cancellation, progress dispatcher
│   │
│   ├── FileX.UI/                    # Presentation Layer (.NET 10-windows + WPF-UI 4.3.0)
│   │   ├── Views/                   # DashboardPage, ConvertPage, HistoryPage, SettingsPage
│   │   ├── Windows/                 # MainWindow, FloatingWidgetWindow, ConversionDialog
│   │   ├── Services/                # NativeTrayIcon (Win32), WindowsIntegrationService
│   │   └── Assets/                  # High-DPI Windows application icons & logos
│   │
│   └── FileX.Tests/                 # Unit & Integration Tests (XUnit)
│       └── ConverterTests.cs        # Verification suite for formats, conversions, and persistence
│
├── installer/
│   └── FileX.iss                    # Inno Setup 6 production installer script
│
└── dist/
    ├── app/                         # Self-contained native Windows x64 binaries (FileX.exe)
    └── installer/                   # Production installer (FileX_Setup.exe)
```

---

## ⚡ Supported Formats & Native Engines

FileX operates **100% offline** without any cloud dependencies:

| Category | Formats Supported | Engine / Implementation |
|---|---|---|
| **Images** | JPG, JPEG, PNG, WEBP, BMP, TIFF, GIF, ICO | Windows Imaging Components (WIC) native pipeline |
| **Documents** | DOCX, TXT, MD, HTML | OpenXML SDK & Markdig native parsing |
| **PDF** | PDF (Text extraction & document generation) | Native Document Streams |
| **Spreadsheets**| CSV, XLSX | OpenXML Spreadsheet DOM engine |
| **Audio** | MP3, WAV, FLAC, AAC, OGG, M4A | Bundled native 64-bit FFmpeg engine |
| **Video** | MP4, MKV, AVI, MOV, WEBM | Bundled native 64-bit FFmpeg engine |

---

## 🚀 Key Features

1. **Floating Drag-and-Drop Widget**:
   - Always-on-top, draggable anywhere across multiple displays.
   - Acrylic/Mica glassmorphism with responsive drop animations.
   - Drag files directly from Windows File Explorer onto the widget to trigger immediate format detection and conversion.
2. **Modern Windows 11 Fluent Dashboard**:
   - Built with WPF-UI Fluent design controls and Mica materials.
   - Real-time conversion metrics, category grid, quick-convert actions.
   - Searchable SQLite-backed conversion history with 1-click "Open File" and "Open Folder".
3. **Smart File Detector**:
   - Validates actual file content via magic-byte signatures and MIME types to prevent extension spoofing.
4. **Native System Integration**:
   - Win32 system tray integration with instant toggle.
   - Windows Startup registration support (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).
   - Native shell integration and high-DPI desktop shortcuts.

---

## 📦 Building and Publishing

### Prerequisites
- .NET 10 SDK (v10.0.301+) with Windows Desktop workload
- Inno Setup 6 (for compiling `FileX_Setup.exe`)

### Build Commands

1. **Compile Solution**:
   ```powershell
   dotnet build native/FileX.slnx -c Release
   ```

2. **Run Tests**:
   ```powershell
   dotnet test native/FileX.slnx
   ```

3. **Publish Self-Contained Native Windows App**:
   ```powershell
   dotnet publish native/src/FileX.UI/FileX.UI.csproj -c Release -r win-x64 --self-contained true -o "native/dist/app"
   ```

4. **Compile Installer**:
   ```powershell
   & "C:\Users\ASUS\AppData\Local\Programs\Inno Setup 6\ISCC.exe" "native/installer/FileX.iss"
   ```

---

## 💿 Deliverables

- **Standalone Native Application**: `native/dist/app/FileX.exe`
- **Windows Setup Installer**: `native/dist/installer/FileX_Setup.exe`
