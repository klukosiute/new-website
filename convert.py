#!/usr/bin/env python3
"""
Convert Obsidian markdown blog posts to static HTML.

This script converts markdown files with YAML frontmatter to HTML using
the template from Phase 1. It handles:
- YAML frontmatter parsing
- Obsidian image syntax (![[filename.png | options]])
- LaTeX math (preserves $...$ and $$...$$ for KaTeX)
- Code syntax highlighting with Pygments
- Open Graph meta tags from frontmatter
"""

import re
import yaml
from pathlib import Path
from typing import Dict, Optional, Tuple
import markdown
from markdown.extensions import fenced_code, footnotes, tables
from markdown.extensions.codehilite import CodeHiliteExtension

# Template CSS and HTML structure
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Kamilė Lukošiūtė</title>
    <meta name="description" content="{description}">

    <!-- Open Graph / Social Cards -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    {og_image_meta}
    <meta property="og:type" content="article">

    <!-- KaTeX for LaTeX -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>

    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Times New Roman', Times, serif;
            font-size: 16px;
            line-height: 1.7;
            color: #222;
            background: #fff;
            padding: 20px;
        }}

        .container {{
            max-width: 640px;
            margin: 0 auto;
        }}

        header {{
            margin-bottom: 2em;
            padding-bottom: 1em;
            border-bottom: 1px solid #ddd;
        }}

        header a {{
            color: #222;
            text-decoration: none;
        }}

        header a:hover {{
            text-decoration: underline;
        }}

        h1 {{
            font-size: 2em;
            margin: 0.67em 0 0.3em 0;
            font-weight: bold;
            line-height: 1.2;
        }}

        h2 {{
            font-size: 1.5em;
            margin: 0.83em 0;
            font-weight: bold;
            line-height: 1.2;
        }}

        h3 {{
            font-size: 1.25em;
            margin: 1em 0;
            font-weight: bold;
            line-height: 1.2;
        }}

        p {{
            margin-bottom: 0.75em;
        }}

        a {{
            color: #0000EE;
            text-decoration: underline;
        }}

        a:visited {{
            color: #551A8B;
        }}

        a:hover {{
            color: #0000EE;
        }}

        code {{
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
            background: #f5f5f5;
            padding: 2px 5px;
            border-radius: 3px;
        }}

        pre {{
            background: #f5f5f5;
            padding: 1em;
            overflow-x: auto;
            margin: 1em 0;
            border-radius: 5px;
        }}

        pre code {{
            background: none;
            padding: 0;
        }}

        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 1.5em auto;
        }}

        blockquote {{
            border-left: 3px solid #ddd;
            padding-left: 1em;
            margin: 1em 0;
            font-style: italic;
            color: #555;
        }}

        ul, ol {{
            margin-left: 2em;
            margin-bottom: 1em;
        }}

        li {{
            margin-bottom: 0.5em;
        }}

        .subtitle {{
            font-style: italic;
            font-size: 1.1em;
            line-height: 1.4;
            color: #555;
            margin-bottom: 0.2em;
        }}

        .date {{
            color: #666;
            font-style: italic;
            font-size: 0.9em;
            margin-bottom: 1em;
        }}

        footer {{
            margin-top: 3em;
            padding-top: 1em;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
            color: #666;
        }}

        /* LaTeX math blocks */
        .katex-display {{
            margin: 1.5em 0;
            overflow-x: auto;
            overflow-y: hidden;
        }}

        /* Footnotes styling */
        .footnote {{
            font-size: 0.9em;
        }}

        .footnotes {{
            margin-top: 3em;
            padding-top: 1em;
            border-top: 1px solid #ddd;
            font-size: 0.9em;
        }}

        sup {{
            line-height: 0;
        }}

        /* Mobile optimization */
        @media (max-width: 480px) {{
            body {{
                padding: 10px;
                font-size: 16px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <a href="/">← kamilelukosiute.com</a>
        </header>

        <article>
            <h1>{title}</h1>
            {subtitle_html}
            {date_html}
            {content}
        </article>

        <footer>
            <p><a href="/posts/">← All posts</a></p>
        </footer>
    </div>

    <!-- Initialize KaTeX auto-render -->
    <script>
        document.addEventListener("DOMContentLoaded", function() {{
            renderMathInElement(document.body, {{
                delimiters: [
                    {{left: "$$", right: "$$", display: true}},
                    {{left: "$", right: "$", display: false}}
                ],
                throwOnError: false
            }});
        }});
    </script>
</body>
</html>
"""


def parse_frontmatter(content: str) -> Tuple[Dict, str]:
    """
    Parse YAML frontmatter from markdown content.

    Returns:
        (frontmatter_dict, markdown_content)
    """
    if not content.startswith('---'):
        return {}, content

    # Find the end of frontmatter
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    frontmatter_str = parts[1]
    markdown_content = parts[2].strip()

    try:
        frontmatter = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError:
        frontmatter = {}

    return frontmatter, markdown_content


def convert_obsidian_images(content: str) -> str:
    """
    Convert Obsidian image syntax to HTML img tags.

    Patterns:
    - ![[image.png]] → <img src="/images/image.png">
    - ![[image.png | 200]] → <img src="/images/image.png" style="max-width: 200px">
    - ![[image.png | center | 400]] → centered with max-width
    """
    # Pattern: ![[filename.ext | options]]
    pattern = r'!\[\[([^\]|]+?)(?:\s*\|\s*([^\]]+?))?\]\]'

    def replace_image(match):
        filename = match.group(1).strip()
        options = match.group(2).strip() if match.group(2) else None

        # Build img tag
        img_src = f"/images/{filename}"

        if not options:
            return f'<img src="{img_src}" alt="{filename}">'

        # Parse options (can be: "200", "center | 400", "center", etc.)
        opts = [o.strip() for o in options.split('|')]

        styles = []
        is_centered = False

        for opt in opts:
            if opt.lower() == 'center':
                is_centered = True
            elif opt.isdigit():
                styles.append(f"max-width: {opt}px")

        style_str = "; ".join(styles)
        if is_centered:
            style_str = f"{style_str}; display: block; margin: 0 auto" if style_str else "display: block; margin: 0 auto"

        if style_str:
            return f'<img src="{img_src}" style="{style_str}" alt="{filename}">'
        else:
            return f'<img src="{img_src}" alt="{filename}">'

    return re.sub(pattern, replace_image, content)


def generate_slug(filename: str) -> str:
    """
    Generate URL slug from filename.

    Example: "When can a tensor be view()ed?.md" → "when-can-a-tensor-be-viewed"
    """
    # Remove extension
    slug = filename.replace('.md', '')

    # Convert to lowercase
    slug = slug.lower()

    # Remove special characters and replace spaces with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)

    return slug.strip('-')


def convert_inline_footnotes(content: str) -> str:
    """
    Convert Pandoc-style inline footnotes ^[text] to reference-style footnotes.
    Example: ^[some text] becomes [^1] with [^1]: some text at the end.
    """
    footnote_counter = [0]  # Use list to allow modification in nested function
    footnote_references = []

    def replace_footnote(match):
        footnote_counter[0] += 1
        footnote_num = footnote_counter[0]
        footnote_text = match.group(1)

        # Store the footnote reference
        footnote_references.append(f"[^{footnote_num}]: {footnote_text}")

        # Return the reference marker
        return f"[^{footnote_num}]"

    # Replace all inline footnotes with reference markers
    pattern = r'\^\[([^\]]+)\]'
    content = re.sub(pattern, replace_footnote, content)

    # Append footnote references at the end if any were found
    if footnote_references:
        content += "\n\n" + "\n".join(footnote_references) + "\n"

    return content


def protect_latex_math(content: str) -> Tuple[str, Dict[str, str]]:
    """
    Temporarily replace LaTeX math with placeholders to protect from markdown processing.
    Returns (protected_content, replacements_dict)
    """
    import hashlib
    replacements = {}
    counter = [0]

    def make_placeholder(match):
        counter[0] += 1
        placeholder = f"LATEX_MATH_PLACEHOLDER_{counter[0]}_"
        replacements[placeholder] = match.group(0)
        return placeholder

    # Protect display math $$...$$ (must come before inline math)
    content = re.sub(r'\$\$(.+?)\$\$', make_placeholder, content, flags=re.DOTALL)

    # Protect inline math $...$
    content = re.sub(r'\$(.+?)\$', make_placeholder, content)

    return content, replacements


def restore_latex_math(content: str, replacements: Dict[str, str]) -> str:
    """
    Restore LaTeX math from placeholders.
    """
    for placeholder, original in replacements.items():
        content = content.replace(placeholder, original)
    return content


def fix_malformed_code_fences(content: str) -> str:
    """
    Fix code fences that are missing newlines after the language identifier.
    Example: ```pythoncode -> ```python\ncode
    """
    # Match ```language followed immediately by non-whitespace
    pattern = r'```(\w+)([^\n])'
    replacement = r'```\1\n\2'
    return re.sub(pattern, replacement, content)


def convert_markdown_to_html(content: str) -> str:
    """
    Convert markdown to HTML using Python markdown library.
    Preserves LaTeX math for KaTeX rendering.
    """
    # First convert inline footnotes to reference-style
    content = convert_inline_footnotes(content)

    # Protect LaTeX math from markdown processing
    content, math_replacements = protect_latex_math(content)

    # Configure markdown with extensions
    md = markdown.Markdown(
        extensions=[
            'fenced_code',
            'footnotes',
            'tables',
            CodeHiliteExtension(
                noclasses=True,  # Inline styles for syntax highlighting
                pygments_style='default'
            )
        ]
    )

    # Convert to HTML
    html = md.convert(content)

    # Restore LaTeX math
    html = restore_latex_math(html, math_replacements)

    return html


def extract_date_from_content(content: str) -> Optional[str]:
    """
    Extract publication date from content (usually at the end).
    Looks for patterns like "*Originally Published Mar 16, 2022*"
    """
    # Try pattern with "on" FIRST (more specific)
    date_pattern_with_on = r'\*Originally Published on (.+?)\*'
    match = re.search(date_pattern_with_on, content)

    if match:
        return match.group(1)

    # Then try pattern without "on" (more general)
    date_pattern = r'\*Originally Published (.+?)\*'
    match = re.search(date_pattern, content)

    if match:
        return match.group(1)

    return None


def get_social_card_image(frontmatter: Dict) -> Optional[str]:
    """
    Extract social card image from frontmatter.
    Checks og:image, twitter:image, and cover fields.
    """
    # Check various fields that might contain social card
    for field in ['og:image', 'twitter:image', 'cover']:
        if field in frontmatter:
            image_path = frontmatter[field]
            # Convert files/filename.png to /images/filename.png
            if image_path.startswith('files/'):
                filename = image_path.replace('files/', '')
                return f"/images/{filename}"
            return f"/images/{image_path}"

    return None


def convert_post(md_file_path: Path, output_dir: Path) -> Path:
    """
    Convert a single markdown post to HTML.

    Returns:
        Path to the generated HTML file
    """
    # Read markdown file
    content = md_file_path.read_text(encoding='utf-8')

    # Parse frontmatter
    frontmatter, markdown_content = parse_frontmatter(content)

    # Extract metadata
    title = frontmatter.get('title', md_file_path.stem)
    description = frontmatter.get('description', '')

    # Extract subtitle if present (one or more consecutive italic lines after title)
    subtitle_lines = []
    # Match title line followed by optional blank lines, then one or more italic lines
    subtitle_match = re.search(r'^#\s+.+$\n+((?:\*.+?\*\n?)+)', markdown_content, re.MULTILINE)
    if subtitle_match:
        # Extract all italic lines
        subtitle_block = subtitle_match.group(1)
        # Find each individual italic line
        for line_match in re.finditer(r'\*(.+?)\*', subtitle_block):
            subtitle_lines.append(line_match.group(1))

    # If title not in frontmatter, extract from first # heading
    if not frontmatter.get('title'):
        heading_match = re.search(r'^#\s+(.+)$', markdown_content, re.MULTILINE)
        if heading_match:
            title = heading_match.group(1)
            # Remove the heading from content to avoid duplication
            markdown_content = re.sub(r'^#\s+.+$\n?', '', markdown_content, count=1, flags=re.MULTILINE)

    # Remove subtitle from content to avoid duplication
    if subtitle_lines:
        # Remove each subtitle line
        for line in subtitle_lines:
            markdown_content = re.sub(r'\*' + re.escape(line) + r'\*\n?', '', markdown_content, count=1)

    # Extract date if present
    date = extract_date_from_content(markdown_content)
    if date:
        # Remove date from content (both patterns)
        markdown_content = re.sub(r'\*Originally Published on .+?\*\s*$', '', markdown_content)
        markdown_content = re.sub(r'\*Originally Published .+?\*\s*$', '', markdown_content)
        date_html = f'<p class="date">{date}</p>'
    else:
        date_html = ''

    # Build subtitle HTML if present (one <p> per line)
    if subtitle_lines:
        subtitle_html = '\n            '.join(f'<p class="subtitle">{line}</p>' for line in subtitle_lines)
    else:
        subtitle_html = ''

    # Get social card image
    social_card = get_social_card_image(frontmatter)
    if social_card:
        og_image_meta = f'<meta property="og:image" content="{social_card}">'
    else:
        og_image_meta = ''

    # Convert Obsidian image syntax
    markdown_content = convert_obsidian_images(markdown_content)

    # Convert markdown to HTML
    html_content = convert_markdown_to_html(markdown_content)

    # Generate slug
    slug = generate_slug(md_file_path.name)

    # Fill in template
    html = HTML_TEMPLATE.format(
        title=title,
        description=description or f"Blog post: {title}",
        og_image_meta=og_image_meta,
        subtitle_html=subtitle_html,
        date_html=date_html,
        content=html_content
    )

    # Write HTML file
    output_file = output_dir / f"{slug}.html"
    output_file.write_text(html, encoding='utf-8')

    print(f"✓ Converted: {md_file_path.name} → {output_file.name}")

    return output_file


def main():
    """Main conversion function."""
    # Paths
    script_dir = Path(__file__).parent
    posts_dir = script_dir / 'port-posts'
    output_dir = script_dir / 'posts'

    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)

    # Get all markdown files
    md_files = sorted(posts_dir.glob('*.md'))

    if not md_files:
        print(f"No markdown files found in {posts_dir}")
        return

    print(f"Found {len(md_files)} posts to convert\n")

    # Convert each post
    for md_file in md_files:
        try:
            convert_post(md_file, output_dir)
        except Exception as e:
            print(f"✗ Error converting {md_file.name}: {e}")

    print(f"\n✓ Conversion complete! HTML files in {output_dir}")


if __name__ == '__main__':
    main()
