from flask import Flask, request, render_template_string, redirect, url_for
import os

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024  # 2 MB limit

ALLOWED_EXTENSIONS = {"html", "htm"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>HTML Code Viewer</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link
        href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap"
        rel="stylesheet"
    />
    <style>
        *, *::before, *::after {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: "DM Sans", sans-serif;
            background-color: #f5f4f0;
            color: #1a1a1a;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 48px 20px 64px;
        }

        header {
            text-align: center;
            margin-bottom: 40px;
        }

        header h1 {
            font-size: 1.9rem;
            font-weight: 600;
            letter-spacing: -0.5px;
            color: #111;
        }

        header p {
            margin-top: 8px;
            font-size: 0.95rem;
            color: #666;
        }

        .card {
            background: #ffffff;
            border: 1px solid #e0ddd6;
            border-radius: 14px;
            padding: 32px;
            width: 100%;
            max-width: 700px;
            box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
        }

        /* ── Upload zone ── */
        .upload-zone {
            border: 2px dashed #c9c5bb;
            border-radius: 10px;
            padding: 40px 24px;
            text-align: center;
            background: #faf9f6;
            transition: border-color 0.2s, background 0.2s;
            cursor: pointer;
        }

        .upload-zone:hover,
        .upload-zone.drag-over {
            border-color: #888;
            background: #f2f1ec;
        }

        .upload-zone input[type="file"] {
            display: none;
        }

        .upload-icon {
            font-size: 2.4rem;
            margin-bottom: 12px;
            display: block;
        }

        .upload-zone label {
            display: block;
            cursor: pointer;
        }

        .upload-zone .upload-main-text {
            font-size: 1rem;
            font-weight: 500;
            color: #333;
        }

        .upload-zone .upload-sub-text {
            font-size: 0.85rem;
            color: #888;
            margin-top: 6px;
        }

        .selected-file-name {
            margin-top: 12px;
            font-size: 0.85rem;
            color: #555;
            font-family: "DM Mono", monospace;
        }

        .btn-primary {
            display: block;
            width: 100%;
            margin-top: 20px;
            padding: 13px;
            background: #1a1a1a;
            color: #fff;
            font-family: "DM Sans", sans-serif;
            font-size: 0.95rem;
            font-weight: 500;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.18s, transform 0.1s;
        }

        .btn-primary:hover {
            background: #333;
        }

        .btn-primary:active {
            transform: scale(0.99);
        }

        /* ── Error banner ── */
        .error-banner {
            background: #fff1f1;
            border: 1px solid #f5c2c2;
            color: #b00020;
            border-radius: 8px;
            padding: 12px 16px;
            font-size: 0.9rem;
            margin-bottom: 20px;
        }

        /* ── Code viewer ── */
        .code-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
        }

        .code-filename {
            font-size: 0.88rem;
            font-weight: 500;
            color: #555;
            font-family: "DM Mono", monospace;
            background: #f0ede7;
            padding: 4px 10px;
            border-radius: 6px;
        }

        .btn-copy {
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            background: #f0ede7;
            border: 1px solid #ddd8cf;
            border-radius: 7px;
            font-family: "DM Sans", sans-serif;
            font-size: 0.88rem;
            font-weight: 500;
            color: #333;
            cursor: pointer;
            transition: background 0.15s, border-color 0.15s;
        }

        .btn-copy:hover {
            background: #e6e2da;
            border-color: #c9c5bb;
        }

        .btn-copy.copied {
            background: #e8f5e9;
            border-color: #a5d6a7;
            color: #2e7d32;
        }

        .code-block-wrapper {
            position: relative;
            background: #faf9f7;
            border: 1px solid #e5e2da;
            border-radius: 10px;
            overflow: hidden;
        }

        pre {
            overflow-x: auto;
            overflow-y: auto;
            max-height: 520px;
            padding: 20px 22px;
            font-family: "DM Mono", monospace;
            font-size: 0.82rem;
            line-height: 1.75;
            color: #2d2d2d;
            white-space: pre;
        }

        .upload-another {
            display: inline-block;
            margin-top: 24px;
            font-size: 0.88rem;
            color: #888;
            text-decoration: none;
            border-bottom: 1px solid #ccc;
            padding-bottom: 1px;
            transition: color 0.15s, border-color 0.15s;
        }

        .upload-another:hover {
            color: #333;
            border-color: #555;
        }
    </style>
</head>
<body>

    <header>
        <h1>HTML Code Viewer</h1>
        <p>Upload an HTML file to view and copy its source code.</p>
    </header>

    <div class="card">

        {% if error %}
        <div class="error-banner">⚠ {{ error }}</div>
        {% endif %}

        {% if not code %}

        <!-- ── Upload form ── -->
        <form
            method="POST"
            action="/"
            enctype="multipart/form-data"
            id="uploadForm"
        >
            <div
                class="upload-zone"
                id="dropZone"
                onclick="document.getElementById('fileInput').click()"
            >
                <span class="upload-icon">📄</span>
                <label for="fileInput">
                    <span class="upload-main-text">Click to choose a file</span>
                    <span class="upload-sub-text">or drag and drop it here · .html / .htm only</span>
                </label>
                <input
                    type="file"
                    id="fileInput"
                    name="file"
                    accept=".html,.htm"
                    onchange="handleFileSelect(this)"
                />
                <div class="selected-file-name" id="fileName"></div>
            </div>

            <button type="submit" class="btn-primary">View Source Code →</button>
        </form>

        {% else %}

        <!-- ── Code viewer ── -->
        <div class="code-header">
            <span class="code-filename">{{ filename }}</span>
            <button class="btn-copy" id="copyBtn" onclick="copyCode()">
                <span id="copyIcon">⎘</span>
                <span id="copyLabel">Copy Code</span>
            </button>
        </div>

        <div class="code-block-wrapper">
            <pre id="codeContent">{{ code }}</pre>
        </div>

        <a href="/" class="upload-another">← Upload another file</a>

        {% endif %}

    </div>

    <script>
        // ── Drag-and-drop ──
        const dropZone = document.getElementById("dropZone");

        if (dropZone) {
            dropZone.addEventListener("dragover", (e) => {
                e.preventDefault();
                dropZone.classList.add("drag-over");
            });

            dropZone.addEventListener("dragleave", () => {
                dropZone.classList.remove("drag-over");
            });

            dropZone.addEventListener("drop", (e) => {
                e.preventDefault();
                dropZone.classList.remove("drag-over");

                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    const input = document.getElementById("fileInput");
                    input.files = files;
                    handleFileSelect(input);
                }
            });
        }

        // ── Show selected filename ──
        function handleFileSelect(input) {
            const nameEl = document.getElementById("fileName");
            if (input.files.length > 0) {
                nameEl.textContent = "Selected: " + input.files[0].name;
            }
        }

        // ── Copy code ──
        function copyCode() {
            const code = document.getElementById("codeContent").innerText;
            navigator.clipboard.writeText(code).then(() => {
                const btn = document.getElementById("copyBtn");
                const label = document.getElementById("copyLabel");
                const icon = document.getElementById("copyIcon");

                btn.classList.add("copied");
                label.textContent = "Copied!";
                icon.textContent = "✓";

                setTimeout(() => {
                    btn.classList.remove("copied");
                    label.textContent = "Copy Code";
                    icon.textContent = "⎘";
                }, 2000);
            });
        }
    </script>

</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("file")

        if not file or file.filename == "":
            return render_template_string(HTML_TEMPLATE, error="No file selected.", code=None)

        if not allowed_file(file.filename):
            return render_template_string(
                HTML_TEMPLATE,
                error="Only .html and .htm files are accepted.",
                code=None,
            )

        try:
            raw_bytes = file.read()
            code_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return render_template_string(
                HTML_TEMPLATE,
                error="Could not read the file. Make sure it is a valid UTF-8 HTML file.",
                code=None,
            )

        return render_template_string(
            HTML_TEMPLATE,
            code=code_text,
            filename=file.filename,
            error=None,
        )

    return render_template_string(HTML_TEMPLATE, code=None, error=None)


if __name__ == "__main__":
    app.run(debug=True, port=5000)