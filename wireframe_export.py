"""
Script xuất wireframe PNG cho báo cáo EchoViet
Chạy độc lập, không cần Streamlit - chỉ để tạo file PNG mô tả cấu trúc web app.

Cách sử dụng:
    1. Cài đặt dependencies:
       pip install graphviz
    
    2. (Windows) Cài Graphviz system nếu chưa có:
       - Tải từ: https://graphviz.org/download/
       - Cài đặt và đảm bảo thêm vào PATH
    
    3. Chạy script:
       python wireframe_export.py
    
    4. File PNG sẽ được tạo: echoviet_wireframe.png (hoặc đường dẫn bạn chỉ định)

Tùy biến:
    - Đổi output path: sửa biến OUTPUT_PATH trong hàm main()
    - Đổi nhãn node: sửa hàm get_wireframe_dot()
    - Ẩn/hiện node: comment/uncomment các node trong DOT string
"""

import os
import sys

try:
    import graphviz
except ImportError:
    print("ERROR: Thư viện 'graphviz' chưa được cài đặt.")
    print("Cài đặt bằng: pip install graphviz")
    print("Và đảm bảo đã cài Graphviz system package (https://graphviz.org/download/)")
    sys.exit(1)


def get_wireframe_dot() -> str:
    """
    Trả về chuỗi DOT mô tả sơ đồ wireframe của EchoViet.
    
    Cấu trúc:
    - Main Flow: Home → Audio → Transcription → Enhancement → Export
    - Quick Navigation: Home có thể đi thẳng đến bất kỳ trang nào
    - Advanced Pages: Các trang nâng cao (Settings, Analysis, API) từ Home
    
    Returns:
        str: DOT language string để render bằng Graphviz
    """
    return r"""
digraph EchoVietWireframe {
    rankdir=LR;
    bgcolor="white";
    fontname="Segoe UI";
    node [shape=box style="rounded,filled" color="#1f4e79" fillcolor="#e3f2fd" fontname="Segoe UI" fontsize=10];
    edge [color="#90a4ae" fontname="Segoe UI" fontsize=9];

    // Main Flow cluster
    subgraph cluster_main {
        label="Main Workflow Flow";
        style="rounded,dashed";
        color="#bbdefb";
        fontname="Segoe UI Bold";
        fontsize=12;

        Home       [label="🏠 Home / Dashboard"];
        Audio      [label="🎤 Audio Input"];
        Trans      [label="📝 Transcription"];
        Enhance    [label="✨ Enhancement & Speaker"];
        Export     [label="📊 Export & Reporting"];

        // Main sequential flow
        Home   -> Audio   [label="Start Step 1" color="#4caf50" style=bold];
        Audio  -> Trans   [label="Next: STT" color="#4caf50" style=bold];
        Trans  -> Enhance [label="Next: AI Enhance" color="#4caf50" style=bold];
        Enhance-> Export  [label="Next: Export" color="#4caf50" style=bold];

        // Quick navigation từ Home (dashed lines)
        Home -> Trans   [style=dashed label="Quick nav" color="#ff9800"];
        Home -> Enhance [style=dashed label="Quick nav" color="#ff9800"];
        Home -> Export  [style=dashed label="Quick nav" color="#ff9800"];
    }

    // Advanced / Technical pages cluster
    subgraph cluster_advanced {
        label="Advanced / Technical Pages";
        style="rounded,dotted";
        color="#c8e6c9";
        fontname="Segoe UI Bold";
        fontsize=12;

        AdvSettings [label="⚙️ Advanced Settings"];
        Analysis    [label="📈 Analysis & Evaluation"];
        APIInfo     [label="🔌 API / System Info"];
    }

    // Điều hướng từ Home sang các trang nâng cao
    Home -> AdvSettings [style=dashed label="Advanced expander" color="#9c27b0"];
    Home -> Analysis    [style=dashed label="Advanced expander" color="#9c27b0"];
    Home -> APIInfo     [style=dashed label="Advanced expander" color="#9c27b0"];
}
"""


def get_ui_wireframe_dot() -> str:
    """
    Trả về chuỗi DOT mô tả wireframe UI (bố cục) của trang Home / Dashboard.

    Các vùng chính:
    - Header
    - Quick Start Guide + Workflow Steps
    - Processing Pipeline
    - Key Features
    - Quick Navigation
    - System Status
    - Help / Info
    - Advanced Settings
    - Footer
    """
    return r"""
digraph EchoVietUIWireframe {
    rankdir=TB;
    bgcolor="white";
    fontname="Segoe UI";
    node [shape=box style="rounded,filled" color="#37474f" fillcolor="#eceff1" fontname="Segoe UI" fontsize=10];
    edge [color="#90a4ae" fontname="Segoe UI" fontsize=9];

    page [label="🏠 Home / Dashboard Page" shape=box style="rounded,bold,filled" fillcolor="#bbdefb"];

    header         [label="Header\n- Logo\n- Title\n- Subtitle" fillcolor="#e3f2fd"];
    quickStart     [label="Quick Start Guide\n- 3 steps description" fillcolor="#f1f8e9"];
    workflowSteps  [label="Workflow Steps (3 columns)\n1. Upload Audio\n2. Transcription\n3. Enhancement & Export" fillcolor="#f9fbe7"];
    pipeline       [label="Processing Pipeline Diagram" fillcolor="#fff3e0"];
    keyFeatures    [label="Key Features (2 columns)\n- STT, Diarization\n- AI Enhancement, Export" fillcolor="#f3e5f5"];
    quickNav       [label="Quick Navigation (4 buttons)\n- Audio Input\n- Transcription\n- Enhancement\n- Export" fillcolor="#ede7f6"];
    systemStatus   [label="System Status Section" fillcolor="#e0f7fa"];
    helpInfo       [label="Help / Info\n- Usage Tips\n- Privacy & Security" fillcolor="#e8eaf6"];
    advanced       [label="Advanced Settings Expander\n- Advanced Settings\n- Analysis & Evaluation\n- API / System Info" fillcolor="#fce4ec"];
    footer         [label="Footer\n- Credits / Links" fillcolor="#f5f5f5"];

    page -> header;
    header -> quickStart;
    quickStart -> workflowSteps;
    workflowSteps -> pipeline;
    pipeline -> keyFeatures;
    keyFeatures -> quickNav;
    quickNav -> systemStatus;
    systemStatus -> helpInfo;
    helpInfo -> advanced;
    advanced -> footer;
}
"""


def get_audio_input_ui_dot() -> str:
    """
    Wireframe UI cho trang 1 - Audio Input.
    """
    return r"""
digraph AudioInputUIWireframe {
    rankdir=TB;
    bgcolor="white";
    fontname="Segoe UI";
    node [shape=box style="rounded,filled" color="#37474f" fillcolor="#eceff1" fontname="Segoe UI" fontsize=10];
    edge [color="#90a4ae" fontname="Segoe UI" fontsize=9];

    page [label="🎤 Audio Input Page" shape=box style="rounded,bold,filled" fillcolor="#bbdefb"];

    header      [label="Header\n- Title\n- Description" fillcolor="#e3f2fd"];
    inputMode   [label="Input Mode Selector\n- Upload file\n- Record mic" fillcolor="#f1f8e9"];
    uploadArea  [label="Upload Area\n- File uploader\n- Constraints (format, size)" fillcolor="#f9fbe7"];
    recordArea  [label="Record Controls\n- Start/Stop\n- Level indicator" fillcolor="#fffde7"];
    options     [label="Processing Options\n- Language\n- Model size\n- Chunking" fillcolor="#ede7f6"];
    preview     [label="Audio Preview\n- Waveform / basic info" fillcolor="#e8eaf6"];
    actions     [label="Actions\n- Clear\n- Go to Transcription" fillcolor="#fce4ec"];
    footer      [label="Footer / Help link" fillcolor="#f5f5f5"];

    page -> header -> inputMode;
    inputMode -> uploadArea;
    inputMode -> recordArea;
    uploadArea -> options;
    recordArea -> options;
    options -> preview;
    preview -> actions;
    actions -> footer;
}
"""


def get_transcription_ui_dot() -> str:
    """
    Wireframe UI cho trang 2 - Transcription.
    """
    return r"""
digraph TranscriptionUIWireframe {
    rankdir=TB;
    bgcolor="white";
    fontname="Segoe UI";
    node [shape=box style="rounded,filled" color="#37474f" fillcolor="#eceff1" fontname="Segoe UI" fontsize=10];
    edge [color="#90a4ae" fontname="Segoe UI" fontsize=9];

    page [label="📝 Transcription Page" shape=box style="rounded,bold,filled" fillcolor="#bbdefb"];

    header      [label="Header\n- Title\n- Audio info" fillcolor="#e3f2fd"];
    controls    [label="Transcription Controls\n- Start / Stop / Retry\n- Progress bar" fillcolor="#f1f8e9"];
    leftCol     [label="Left Column\n- Original transcript\n- Timestamps" fillcolor="#f9fbe7"];
    rightCol    [label="Right Column\n- Segment list\n- Speaker / time info" fillcolor="#fff3e0"];
    status      [label="Status / Logs" fillcolor="#e0f7fa"];
    actions     [label="Actions\n- Save draft\n- Go to Enhancement" fillcolor="#fce4ec"];

    page -> header -> controls;
    controls -> leftCol;
    controls -> rightCol;
    leftCol -> status;
    rightCol -> status;
    status -> actions;
}
"""


def get_enhancement_ui_dot() -> str:
    """
    Wireframe UI cho trang 3 - Enhancement & Speaker.
    """
    return r"""
digraph EnhancementUIWireframe {
    rankdir=TB;
    bgcolor="white";
    fontname="Segoe UI";
    node [shape=box style="rounded,filled" color="#37474f" fillcolor="#eceff1" fontname="Segoe UI" fontsize=10];
    edge [color="#90a4ae" fontname="Segoe UI" fontsize=9];

    page [label="✨ Enhancement & Speaker Page" shape=box style="rounded,bold,filled" fillcolor="#bbdefb"];

    header      [label="Header\n- Title\n- Transcript summary" fillcolor="#e3f2fd"];
    options     [label="Enhancement Options\n- Punctuation\n- Capitalization\n- Cleaning\n- Speaker diarization on/off" fillcolor="#f3e5f5"];
    textView    [label="Enhanced Text View\n- Editable text area\n- Speaker tags" fillcolor="#f9fbe7"];
    sidePanel   [label="Side Panel\n- Speaker list\n- Legend / colors" fillcolor="#e0f7fa"];
    stats       [label="Basic Stats\n- Word count\n- Duration\n- Speakers count" fillcolor="#ede7f6"];
    actions     [label="Actions\n- Apply changes\n- Reset\n- Go to Export" fillcolor="#fce4ec"];

    page -> header -> options;
    options -> textView;
    textView -> stats;
    textView -> sidePanel;
    stats -> actions;
    sidePanel -> actions;
}
"""


def get_export_ui_dot() -> str:
    """
    Wireframe UI cho trang 4 - Export & Reporting.
    """
    return r"""
digraph ExportUIWireframe {
    rankdir=TB;
    bgcolor="white";
    fontname="Segoe UI";
    node [shape=box style="rounded,filled" color="#37474f" fillcolor="#eceff1" fontname="Segoe UI" fontsize=10];
    edge [color="#90a4ae" fontname="Segoe UI" fontsize=9];

    page [label="📊 Export & Reporting Page" shape=box style="rounded,bold,filled" fillcolor="#bbdefb"];

    header      [label="Header\n- Title\n- File / session info" fillcolor="#e3f2fd"];
    formatBox   [label="Export Format\n- TXT\n- DOCX\n- PDF\n- JSON" fillcolor="#f1f8e9"];
    options     [label="Export Options\n- Include timestamps\n- Include speakers\n- Include raw vs enhanced" fillcolor="#f9fbe7"];
    preview     [label="Preview Area\n- Short preview of export" fillcolor="#fff3e0"];
    report      [label="Reporting Section (optional)\n- Basic stats / charts" fillcolor="#ede7f6"];
    actions     [label="Actions\n- Export buttons\n- Download links" fillcolor="#fce4ec"];

    page -> header -> formatBox;
    formatBox -> options;
    options -> preview;
    preview -> report;
    report -> actions;
}
"""


def get_advanced_ui_dot() -> str:
    """
    Wireframe UI cho trang 5 - Advanced Settings.
    """
    return r"""
digraph AdvancedSettingsUIWireframe {
    rankdir=TB;
    bgcolor="white";
    fontname="Segoe UI";
    node [shape=box style="rounded,filled" color="#37474f" fillcolor="#eceff1" fontname="Segoe UI" fontsize=10];
    edge [color="#90a4ae" fontname="Segoe UI" fontsize=9];

    page [label="⚙️ Advanced Settings Page" shape=box style="rounded,bold,filled" fillcolor="#bbdefb"];

    header      [label="Header\n- Title\n- Warning (for technical users)" fillcolor="#e3f2fd"];
    modelCfg    [label="Model Configuration\n- Whisper model\n- Device (CPU/GPU)\n- Batch/chunk settings" fillcolor="#f3e5f5"];
    audioCfg    [label="Audio Processing\n- Sample rate\n- VAD / noise settings" fillcolor="#f1f8e9"];
    cacheCfg    [label="Cache / Storage\n- Temp directory\n- Limits" fillcolor="#e0f7fa"];
    debugCfg    [label="Debug / Logging\n- Verbosity\n- Export logs" fillcolor="#ede7f6"];
    actions     [label="Actions\n- Save\n- Reset to default" fillcolor="#fce4ec"];

    page -> header;
    header -> modelCfg;
    modelCfg -> audioCfg;
    audioCfg -> cacheCfg;
    cacheCfg -> debugCfg;
    debugCfg -> actions;
}
"""


def get_analysis_ui_dot() -> str:
    """
    Wireframe UI cho trang 6 - Analysis & Evaluation.
    """
    return r"""
digraph AnalysisUIWireframe {
    rankdir=TB;
    bgcolor="white";
    fontname="Segoe UI";
    node [shape=box style="rounded,filled" color="#37474f" fillcolor="#eceff1" fontname="Segoe UI" fontsize=10];
    edge [color="#90a4ae" fontname="Segoe UI" fontsize=9];

    page [label="📈 Analysis & Evaluation Page" shape=box style="rounded,bold,filled" fillcolor="#bbdefb"];

    header      [label="Header\n- Title\n- Experiment description" fillcolor="#e3f2fd"];
    datasetBox  [label="Dataset Selector\n- Upload ref transcript\n- Choose sample sets" fillcolor="#f1f8e9"];
    metricsBox  [label="Metrics\n- WER\n- CER\n- Duration-based stats" fillcolor="#f9fbe7"];
    charts      [label="Charts\n- Bar/line charts for scores" fillcolor="#fff3e0"];
    table       [label="Results Table\n- Per-file metrics" fillcolor="#ede7f6"];
    notes       [label="Notes / Observations" fillcolor="#fce4ec"];

    page -> header -> datasetBox;
    datasetBox -> metricsBox;
    metricsBox -> charts;
    charts -> table;
    table -> notes;
}
"""


def get_api_ui_dot() -> str:
    """
    Wireframe UI cho trang 7 - API / System Info.
    """
    return r"""
digraph APIUIWireframe {
    rankdir=TB;
    bgcolor="white";
    fontname="Segoe UI";
    node [shape=box style="rounded,filled" color="#37474f" fillcolor="#eceff1" fontname="Segoe UI" fontsize=10];
    edge [color="#90a4ae" fontname="Segoe UI" fontsize=9];

    page [label="🔌 API / System Info Page" shape=box style="rounded,bold,filled" fillcolor="#bbdefb"];

    header      [label="Header\n- Title\n- Short description" fillcolor="#e3f2fd"];
    apiInfo     [label="API Info\n- Endpoints\n- Auth / tokens\n- Rate limits" fillcolor="#f1f8e9"];
    examples    [label="Code Examples\n- cURL\n- Python snippet" fillcolor="#f9fbe7"];
    systemInfo  [label="System Info\n- Versions\n- Hardware / GPU" fillcolor="#e0f7fa"];
    statusBox   [label="Health / Status\n- Service status\n- Last update" fillcolor="#ede7f6"];

    page -> header -> apiInfo;
    apiInfo -> examples;
    examples -> systemInfo;
    systemInfo -> statusBox;
}
"""


def export_wireframe_png(output_path: str = "echoviet_wireframe.png") -> bool:
    """
    Xuất wireframe diagram ra file PNG.
    
    Args:
        output_path: Đường dẫn file PNG đầu ra (mặc định: echoviet_wireframe.png)
    
    Returns:
        bool: True nếu thành công, False nếu có lỗi
    """
    try:
        dot_src = get_wireframe_dot()
        
        # Tạo đối tượng Source từ DOT string
        src = graphviz.Source(dot_src, format="png")
        
        # Render ra PNG bytes
        png_bytes = src.pipe(format="png")
        
        # Ghi ra file
        with open(output_path, "wb") as f:
            f.write(png_bytes)
        
        print(f"✓ Wireframe PNG đã được tạo thành công: {output_path}")
        print(f"  Kích thước file: {len(png_bytes)} bytes")
        
        return True
        
    except graphviz.ExecutableNotFound:
        print("ERROR: Không tìm thấy Graphviz executable.")
        print("Vui lòng cài đặt Graphviz system package:")
        print("  - Windows: https://graphviz.org/download/")
        print("  - Sau khi cài, đảm bảo thêm vào PATH")
        return False
        
    except Exception as e:
        print(f"ERROR: Lỗi khi xuất wireframe PNG: {e}")
        print(f"  Loại lỗi: {type(e).__name__}")
        return False


def export_ui_wireframe_png(output_path: str = "echoviet_ui_wireframe.png") -> bool:
    """
    Xuất wireframe UI (bố cục trang Dashboard) ra file PNG.

    Args:
        output_path: Đường dẫn file PNG đầu ra (mặc định: echoviet_ui_wireframe.png)

    Returns:
        bool: True nếu thành công, False nếu có lỗi
    """
    try:
        dot_src = get_ui_wireframe_dot()

        src = graphviz.Source(dot_src, format="png")
        png_bytes = src.pipe(format="png")

        with open(output_path, "wb") as f:
            f.write(png_bytes)

        print(f"✓ UI Wireframe PNG đã được tạo thành công: {output_path}")
        print(f"  Kích thước file: {len(png_bytes)} bytes")

        return True

    except graphviz.ExecutableNotFound:
        print("ERROR: Không tìm thấy Graphviz executable (cho UI wireframe).")
        print("Vui lòng cài đặt Graphviz system package:")
        print("  - Windows: https://graphviz.org/download/")
        print("  - Sau khi cài, đảm bảo thêm vào PATH")
        return False

def export_page_ui_wireframes(base_dir: str = ".") -> bool:
    """
    Xuất wireframe UI cho TẤT CẢ các page chính.

    Tạo các file PNG:
    - echoviet_ui_home.png
    - echoviet_ui_audio_input.png
    - echoviet_ui_transcription.png
    - echoviet_ui_enhancement.png
    - echoviet_ui_export.png
    - echoviet_ui_advanced.png
    - echoviet_ui_analysis.png
    - echoviet_ui_api.png
    """
    mappings = [
        ("echoviet_ui_home.png", get_ui_wireframe_dot),
        ("echoviet_ui_audio_input.png", get_audio_input_ui_dot),
        ("echoviet_ui_transcription.png", get_transcription_ui_dot),
        ("echoviet_ui_enhancement.png", get_enhancement_ui_dot),
        ("echoviet_ui_export.png", get_export_ui_dot),
        ("echoviet_ui_advanced.png", get_advanced_ui_dot),
        ("echoviet_ui_analysis.png", get_analysis_ui_dot),
        ("echoviet_ui_api.png", get_api_ui_dot),
    ]

    all_ok = True

    for filename, dot_fn in mappings:
        output_path = os.path.join(base_dir, filename)
        try:
            dot_src = dot_fn()
            src = graphviz.Source(dot_src, format="png")
            png_bytes = src.pipe(format="png")
            with open(output_path, "wb") as f:
                f.write(png_bytes)
            print(f"✓ UI wireframe đã tạo: {output_path} ({len(png_bytes)} bytes)")
        except graphviz.ExecutableNotFound:
            print("ERROR: Không tìm thấy Graphviz executable khi tạo UI wireframes.")
            all_ok = False
            break
        except Exception as e:
            print(f"ERROR: Lỗi khi tạo {output_path}: {e}")
            all_ok = False

    return all_ok


def main():
    """
    Hàm main để chạy script.
    """
    print("=" * 60)
    print("EchoViet Wireframe PNG Export Tool")
    print("=" * 60)
    print()
    
    # Đường dẫn output mặc định (có thể thay đổi)
    output_path_structure = "echoviet_wireframe.png"
    output_path_ui = "echoviet_ui_wireframe.png"
    ui_pages_dir = "."
    
    # Hoặc lưu vào thư mục docs/ nếu có
    if os.path.exists("docs"):
        output_path_structure = os.path.join("docs", "echoviet_wireframe.png")
        output_path_ui = os.path.join("docs", "echoviet_ui_wireframe.png")
        ui_pages_dir = "docs"
        print(f"Thư mục 'docs' tồn tại, sẽ lưu vào:")
        print(f"  - Structure wireframe       : {output_path_structure}")
        print(f"  - UI wireframe (Dashboard)  : {output_path_ui}")
        print(f"  - UI wireframes (per page)  : {ui_pages_dir}/echoviet_ui_*.png")
    else:
        print("Sẽ lưu file PNG vào thư mục hiện tại:")
        print(f"  - Structure wireframe       : {output_path_structure}")
        print(f"  - UI wireframe (Dashboard)  : {output_path_ui}")
        print(f"  - UI wireframes (per page)  : ./echoviet_ui_*.png")
    
    print()
    
    # Xuất PNG cho structure wireframe
    success_structure = export_wireframe_png(output_path_structure)

    # Xuất PNG cho UI wireframe (Dashboard)
    success_ui = export_ui_wireframe_png(output_path_ui)

    # Xuất PNG UI cho từng page
    success_ui_pages = export_page_ui_wireframes(ui_pages_dir)

    if success_structure and success_ui and success_ui_pages:
        print()
        print("=" * 60)
        print("Hoàn thành! Đã tạo đầy đủ file PNG cho báo cáo:")
        print(f"  - Structure wireframe        : {output_path_structure}")
        print(f"  - UI wireframe (Dashboard)   : {output_path_ui}")
        print(f"  - UI wireframes (per page)   : trong '{ui_pages_dir}', file 'echoviet_ui_*.png'")
        print("=" * 60)
    else:
        print()
        print("=" * 60)
        print("Có lỗi khi tạo một hoặc cả hai file PNG. Vui lòng kiểm tra lại cài đặt Graphviz.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
