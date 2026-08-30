import os
import re
from datetime import datetime
from pathlib import Path

# ==========================================
# [DEBUG CONFIGURATION] 一括切り替えフラグ
# ==========================================
DEBUG = True

def log_debug(message: str, log_file: Path):
    if not DEBUG:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)
# ==========================================

def clean_markdown_text(text: str) -> str:
    """プレビュー用にMarkdown記号やObsidianリンクを除去"""
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)  # [[Link|Text]] -> Text
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)          # [Text](url) -> Text
    text = re.sub(r"[`#*_{}\[\]()<>+!|-]", "", text)              # 各種記号削除
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_metadata(file_path: Path):
    """Markdownからタイトル、日付、プレビューを自動抽出"""
    file_name = file_path.stem
    
    # 1. 日付の抽出 (ファイル名冒頭の YYYY-MM-DD または YYYYMMDD を優先)
    date_match = re.match(r"^(\d{4}[-_]?\d{2}[-_]?\d{2})", file_name)
    if date_match:
        raw_date = date_match.group(1).replace("_", "-")
        try:
            if len(raw_date) == 8:  # YYYYMMDD
                formatted_date = datetime.strptime(raw_date, "%Y%m%d").strftime("%Y-%m-%d")
            else:
                formatted_date = datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            formatted_date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d")
    else:
        formatted_date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d")

    # 2. タイトルと本文プレビューの抽出
    title = None
    preview_lines = []
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            # 1行目の # 見出しをタイトルとして取得
            if title is None and stripped.startswith("# "):
                title = stripped[2:].strip()
                continue
            
            # 見出し以外の本文行をプレビュー用として収集
            if stripped and not stripped.startswith("#"):
                clean = clean_markdown_text(stripped)
                if clean:
                    preview_lines.append(clean)
                if len(" ".join(preview_lines)) > 120:
                    break

    # 見出しがない場合はファイル名（日付除外）をタイトルにフォールバック
    if not title:
        fallback = re.sub(r"^\d{4}[-_]?\d{2}[-_]?\d{2}[-_]?", "", file_name)
        title = fallback if fallback else file_name

    preview = " ".join(preview_lines)[:120] + ("..." if preview_lines else "")
    return {
        "title": title,
        "date": formatted_date,
        "preview": preview,
        "rel_path": f"posts/{file_path.name}"
    }

def main():
    root_dir = Path(__file__).resolve().parent.parent
    posts_dir = root_dir / "docs" / "posts"
    output_index = root_dir / "docs" / "index.md"
    
    # ログ出力先初期化 (log/debug_log_YYYYMMDD_HHMMSS.txt)
    log_dir = root_dir / "log"
    log_dir.mkdir(exist_ok=True)
    current_time_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"debug_log_{current_time_str}.txt"
    
    log_debug(f"Process started. Scanning directory: {posts_dir}", log_file)

    if not posts_dir.exists():
        posts_dir.mkdir(parents=True, exist_ok=True)
        log_debug(f"Created posts directory: {posts_dir}", log_file)

    # .md ファイルの走査（attachmentsフォルダ等を除く）
    md_files = [p for p in posts_dir.glob("*.md") if p.is_file()]
    log_debug(f"Found {len(md_files)} markdown files.", log_file)

    articles = []
    for p in md_files:
        try:
            meta = extract_metadata(p)
            articles.append(meta)
            log_debug(f"Parsed: {p.name} -> Title: {meta['title']}, Date: {meta['date']}", log_file)
        except Exception as e:
            log_debug(f"Error parsing {p.name}: {str(e)}", log_file)

    # 日付降順でソート
    articles.sort(key=lambda x: x["date"], reverse=True)

    # index.md の組み立て
    content_lines = [
        "# 📚 AI Knowledge Hub",
        "",
        "> 生成AIのプロンプト出力や日々の技術ナレッジをまとめたサイトです。",
        "> 右上の検索バーから全文検索が可能です。",
        "",
        "## 📝 記事一覧 (新しい順)",
        ""
    ]

    if not articles:
        content_lines.append("*まだ記事がありません。`docs/posts/` に Markdown ファイルを追加してください。*")
    else:
        for item in articles:
            content_lines.append(f"### [{item['title']}]({item['rel_path']})")
            content_lines.append(f"**📅 公開日:** `{item['date']}`  ")
            if item["preview"]:
                content_lines.append(f"{item['preview']}  ")
            content_lines.append("")

    with open(output_index, "w", encoding="utf-8") as f:
        f.write("\n".join(content_lines))

    log_debug(f"Successfully generated {output_index} with {len(articles)} articles.", log_file)
    print(f"Generated index.md with {len(articles)} articles.")

if __name__ == "__main__":
    main()
