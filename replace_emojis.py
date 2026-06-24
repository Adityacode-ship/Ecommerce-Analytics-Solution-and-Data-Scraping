import os

file_path = r'e:\data set for analytics\current\app.py'

replacements = {
    "📊": "◱",    # Analytics/Charts
    "📍": "⌖",    # Location/Maps
    "📥": "⭳",    # Download/Upload
    "⚙️": "⚙",   # Settings
    "🔍": "⌕",    # Search
    "🖥️": "⎚",   # Headless/Monitor
    "⏱️": "◷",   # Delay/Timer
    "🚀": "►",    # Run/Scrape
    "🔄": "⟳",    # Refresh/Loading
    "✅": "✓",    # Success
    "❌": "✕",    # Error
    "⬇️": "⭳",   # Download
    "📂": "◫",    # Folder/Loading
    "📋": "⊟",    # Data Preview
    "🧹": "⌫",    # Cleaning
    "📈": "⭈",    # Trend
    "📤": "⭱",    # Export
    "🗑️": "⍛",   # Trash/Removed
    "🔢": "⊞",    # Numerical
    "🗓️": "▦",   # Calendar/Time
    "🔥": "◈",    # Heatmap
    "💰": "◆",    # Revenue
    "📦": "▣",    # Orders
    "🎯": "◎",    # Target/AOV
    "📖": "ℹ",    # Instructions
    "🧭": "❖",    # Navigation
    "☁️": "☁"     # Cloud
}

with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

for old, new in replacements.items():
    text = text.replace(old, new)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)

print("Icons replaced successfully.")
