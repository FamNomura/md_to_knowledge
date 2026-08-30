import os
import re
from datetime import datetime
from pathlib import Path

def clean_markdown_text(text: str) -> str:
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    text = re.sub(r"[`#*_{}\[\]()<>+!|-]", "", text)
    return re.sub(r"\s+", " ", text).strip()

def extract_metadata(file_path: Path):
    file_name = file_path.stem
    date_match = re.match(r"^(\d{4}[-_]?\d{2}[-_]?\d{2})", file_name)
    if date_match:
        raw_date = date_match.group(1).replace("_", "-")
        try:
            formatted_date = datetime.strptime(raw_date, "%Y%m%d").strftime("%Y-%m-%d") if len(raw_date) == 8 else datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y-%m-%d")
        except ValueError:
            formatted_date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d")
    else:
        formatted_date = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%Y-%m-%d")

    title = None
    preview_lines = []
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if title is None and stripped.startswith("# "):
                title = stripped[2:].strip()
                continue
            if stripped and not stripped.startswith("#"):
                clean = clean_markdown_text(stripped)
                if clean:
                    preview_lines.append(clean)
                if len(" ".join(preview_lines)) > 120:
                    break

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
    
    posts_dir.mkdir(parents=True, exist_ok=True)
    md_files = [p for p in posts_dir.glob("*.md") if p.is_file()]

    articles = []
    for p in md_files:
        try:
            articles.append(extract_metadata(p))
        except Exception:
            pass

    articles.sort(key=lambda x: x["date"], reverse=True)

    content_lines = [
        "# 📚 AI Knowledge Hub",
        "",
        "> 生成AIの回答やメモをまとめたアーカイブです。右上の検索バーから全文検索できます。",
        "",
        "## 📝 記事一覧 (新しい順)",
        ""
    ]

    if not articles:
        content_lines.append("*まだ記事がありません。`docs/posts/` に Markdown ファイルを追加してください。*")
    else:
        for item in articles:
            content_lines.append(f"### [{item['title']}]({item['rel_path']})")
            content_lines.append(f"**📅 作成日:** `{item['date']}`  ")
            if item["preview"]:
                content_lines.append(f"{item['preview']}  ")
            content_lines.append("")

    with open(output_index, "w", encoding="utf-8") as f:
        f.write("\n".join(content_lines))

if __name__ == "__main__":
    main()
