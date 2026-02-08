# Plan: Convert Obsidian Blog to Static HTML Site

## Context

The website kamilelukosiute.com is currently built with Obsidian Publish (JavaScript-heavy, markdown content). The goal is to rebuild it as a minimal, readable static HTML site that:
- Works without JavaScript (except for LaTeX rendering)
- Is readable by AI crawlers
- Maintains classic, simple design (white background, Times New Roman)
- Preserves old URLs via redirects

The blog contains 8 posts in markdown format with:
- LaTeX math equations ($$...$$)
- Code blocks (Python, C++)
- Images using Obsidian wiki-link syntax (![[filename.png]])
- YAML frontmatter with metadata

## Critical Files to Modify/Create

### Files to Create:
1. **HTML template** - Reusable template with Times New Roman, white background, KaTeX for LaTeX, mobile-responsive CSS
2. **8 blog post HTML files** in `/posts/` directory
3. **`/posts/index.html`** - Index page listing all posts by category
4. **Redirect pages** - 8 redirect directories with index.html files pointing from old URLs to new HTML pages
5. **`/images/`** directory - All post images (extracted from user's Obsidian vault)
6. **Updated `/index.html`** - Homepage with links to blog posts on the site

### Existing Files Referenced:
- `/Users/kamile/code/new-website/port-posts/` - 8 markdown source files
- `/Users/kamile/code/new-website/TASK.md` - Original project requirements
- `/Users/kamile/code/new-website/url-mapping.md` - Old URLs that need redirects

## Implementation Approach

### 1. HTML Template Design

Create a simple, classic HTML template with:
- **Typography**: Times New Roman, 18px base font size, 1.7 line-height
- **Layout**:
  - Desktop: Content centered in middle portion of screen (~640px max-width column with auto margins)
  - Mobile: Full-screen width with minimal side padding
  - White background
- **Responsive**: Viewport meta tag, fluid padding, no media queries needed
- **LaTeX rendering**: KaTeX from CDN (only JavaScript needed)
- **Code styling**: Light gray background, monospace font
- **Images**: max-width 100%, centered

Template structure:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Post Title] - Kamilė Lukošiūtė</title>
    <meta name="description" content="[Post description from frontmatter]">

    <!-- Open Graph / Social Cards (from frontmatter if available) -->
    <meta property="og:title" content="[Post Title]">
    <meta property="og:description" content="[Post description]">
    <meta property="og:image" content="[og:image or cover from frontmatter]">
    <meta property="og:type" content="article">

    <!-- KaTeX for LaTeX -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
    <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/contrib/auto-render.min.js"></script>

    <style>
        /* Inline CSS with Times New Roman, white bg, responsive layout */
    </style>
</head>
<body>
    <div class="container">
        <header><a href="/">← kamilelukosiute.com</a></header>
        <article>
            <h1>[Title]</h1>
            [Content]
        </article>
        <footer><a href="/posts/">← All posts</a></footer>
    </div>
    <script>
        /* KaTeX auto-render for $...$ and $$...$$ delimiters */
    </script>
</body>
</html>
```

### 2. LaTeX Rendering: KaTeX

Use **KaTeX** (not MathJax) because:
- Faster rendering (milliseconds vs seconds)
- Lighter weight
- Handles all LaTeX in these posts (equations, matrices, fractions)

Configuration:
- Include KaTeX CSS + JS from CDN
- Use auto-render extension
- **Delimiters**:
  - `$$...$$` for display/block equations
  - `$...$` for inline math (posts use this extensively, e.g., `$d, d+1, \dots$`)
- Preserve markdown's LaTeX as-is, KaTeX renders client-side
- Auto-render is smart enough to not treat random `$` symbols (like prices) as math

### 3. Conversion Strategy: Semi-Automated

**Approach**: Create Python script to convert markdown → HTML, then manually review

**Script functionality** (convert.py - not committed to repo):
- Parse YAML frontmatter (title, date, description, og:image, twitter:image, cover)
- Extract social card image if present in frontmatter
- Convert markdown to HTML using Python's `markdown` library with extensions:
  - `fenced_code` - code blocks
  - `footnotes` - footnote references
  - `tables` - table support
- Use **Pygments** for server-side syntax highlighting (no client JS needed)
- Convert Obsidian image syntax:
  - `![[image.png | 200]]` → `<img src="/images/image.png" style="max-width: 200px">`
  - `![[image.png]]` → `<img src="/images/image.png">`
  - `![[image.png | center | 400]]` → `<img src="/images/image.png" style="max-width: 400px; display: block; margin: 0 auto;">`
- Preserve `$$...$$` and `$...$` unchanged for KaTeX
- Insert into HTML template with Open Graph meta tags
- Generate slug from filename (lowercase, hyphens, remove special chars)

**Posts with social cards** (from frontmatter):
- American Character → `files/Pasted image 20240214111428.png`
- Building evaluations for cybersecurity assistance → `files/cybsersec_card.png`
- Design for the defenders... → `files/defense_card.png`
- Maybe don't give language models standardized tests → `files/evals_card.png`

**Manual review after conversion**:
- Check LaTeX renders correctly
- Verify images load
- Fix any markdown parsing issues
- Test mobile layout

### 4. File Structure

```
/Users/kamile/code/new-website/
├── index.html                     # Homepage (update to link to posts)
├── posts/
│   ├── index.html                 # Posts listing by category
│   ├── when-can-a-tensor-be-viewed.html
│   ├── what-does-bcewithlogits-actually-do.html
│   ├── design-for-defenders.html
│   ├── building-evaluations-for-cybersecurity.html
│   ├── you-need-to-spend-more-on-evals.html
│   ├── maybe-dont-give-llms-tests.html
│   ├── american-character.html
│   └── neutron-star-mergers.html
├── images/
│   ├── matrix.png
│   ├── matrix_memory.png
│   ├── matrix_transpose.png
│   ├── exp_func.png
│   └── [other images]
├── llms/
│   ├── Design+for+the+defenders+you+care+about+or+risk+being+useless/
│   │   └── index.html (redirect to /posts/design-for-defenders.html)
│   └── [3 more redirect directories]
├── pytorch/
│   ├── When+can+a+tensor+be+view()ed%3F/
│   │   └── index.html (redirect to /posts/when-can-a-tensor-be-viewed.html)
│   └── [1 more redirect directory]
├── physics/
│   └── Neutron+star+mergers+and+fast+surrogate+modeling/
│       └── index.html (redirect)
├── essays/
│   └── American+Character/
│       └── index.html (redirect)
└── CNAME                          # For GitHub Pages custom domain
```

### 5. URL Structure

**New post URLs**: `/posts/slug.html`

Slug generation:
- Convert filename to lowercase
- Replace spaces with hyphens
- Remove special characters (?, !, parentheses)
- Examples:
  - "When can a tensor be view()ed?.md" → `/posts/when-can-a-tensor-be-viewed.html`
  - "What does BCEWithLogits actually do?.md" → `/posts/what-does-bcewithlogits-actually-do.html`

### 6. Redirect Implementation

For each of 8 old URLs, create directory structure with `index.html` containing meta refresh:

**Example**: `/llms/Design+for+the+defenders+you+care+about+or+risk+being+useless/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url=/posts/design-for-defenders.html">
    <link rel="canonical" href="https://kamilelukosiute.com/posts/design-for-defenders.html">
    <title>Redirecting...</title>
</head>
<body>
    <p>This page has moved. If you are not redirected automatically,
       <a href="/posts/design-for-defenders.html">click here</a>.</p>
</body>
</html>
```

**Old URL → New URL mapping**:
1. `/llms/Design+for+the+defenders+you+care+about+or+risk+being+useless` → `/posts/design-for-defenders.html`
2. `/llms/Building+evaluations+for+cybersecurity+assistance` → `/posts/building-evaluations-for-cybersecurity.html`
3. `/llms/You+need+to+be+spending+more+money+on+evals` → `/posts/you-need-to-spend-more-on-evals.html`
4. `/llms/Maybe+don't+give+language+models+standardized+tests` → `/posts/maybe-dont-give-llms-tests.html`
5. `/essays/American+Character` → `/posts/american-character.html`
6. `/physics/Neutron+star+mergers+and+fast+surrogate+modeling` → `/posts/neutron-star-mergers.html`
7. `/pytorch/What+does+BCEWithLogits+actually+do%3F` → `/posts/what-does-bcewithlogits-actually-do.html`
8. `/pytorch/When+can+a+tensor+be+view()ed%3F` → `/posts/when-can-a-tensor-be-viewed.html`

Note: Special characters in URLs:
- `?` encoded as `%3F`
- `(` encoded as `%28`
- `)` encoded as `%29`

### 7. Image Handling

**Images location**: `/Users/kamile/kamilelukosiute/files`

**Step 1**: Extract list of all images referenced in posts
- Parse all 8 markdown files
- Find all `![[filename.png]]` references in post content
- Find all social card images in frontmatter (`og:image`, `twitter:image`, `cover`)
- Create comprehensive list

**Step 2**: Copy images from Obsidian vault
- Copy all referenced images from `/Users/kamile/kamilelukosiute/files` to `/images/`
- Ensure images are web-optimized (<500KB if possible)

**Step 3**: Update references in HTML conversion
- Convert Obsidian syntax to HTML `<img>` tags
- All images reference `/images/filename.png`
- Preserve size constraints from original syntax

### 8. Posts Index Page

Create `/posts/index.html` with:
- Simple list of all posts grouped by category
- Categories: "AI & Cybersecurity" and "Other Topics"
- Include dates where available
- Link to each post HTML file

Content structure:
```
Blog Posts

AI & Cybersecurity
- Design for the defenders you care about... (Dec 8, 2025)
- Building evaluations for cybersecurity assistance (WIP)
- You need to be spending more money on evals
- Maybe don't give language models standardized tests

Other Topics
- American Character
- Neutron star mergers and fast surrogate modeling (Dec 11, 2021)
- What does BCEWithLogits actually do? (Apr 14, 2022)
- When can a tensor be view()ed? (Mar 16, 2022)
```

### 9. Homepage Updates

Update `/index.html` to link to blog posts hosted on the site:

In "Blog posts about AI:" section, change from plain text to hyperlinks:
- "Design for the defenders you care about..." → link to `/posts/design-for-defenders.html`
- "Building evaluations for cybersecurity assistance" → link to `/posts/building-evaluations-for-cybersecurity.html`
- etc.

Same for "Blog posts about other topics:" section.

### 10. Example Post: "When can a tensor be view()ed?"

This post will serve as the reference implementation. It contains all three key features:

**Images**:
- `![[matrix.png | 200]]`
- `![[matrix_transpose.png|150]]`
- `![[matrix_memory.png]]`

**LaTeX**:
```
$$\text{stride}[i] = \text{stride}[i+1] \times \text{size}[i+1]$$
```

**Code blocks**:
```python
z = torch.arange(12).reshape(3,4)
print(z)
```

**Inline code**: `.view()`, `torch.Tensor.stride(dim)`

Source: [/Users/kamile/code/new-website/port-posts/When can a tensor be view()ed?.md](port-posts/When can a tensor be view()ed?.md)

## Implementation Steps

### Phase 1: Create Template and Example Post
1. Create HTML template with all styling and Open Graph meta tags
2. Manually convert "When can a tensor be view()ed?" post as proof of concept
3. Test LaTeX rendering with KaTeX (both `$...$` inline and `$$...$$` display)
4. Test on mobile (resize browser)
5. Verify images work (will need image files from `/Users/kamile/kamilelukosiute/files`)
**→ STOP HERE and show user for review and iteration**

### Phase 2: Write Conversion Script
1. Write `convert.py` with markdown → HTML conversion
2. Handle YAML frontmatter parsing (including social card metadata)
3. Implement Obsidian image syntax conversion
4. Configure Pygments for code highlighting
5. Add Open Graph meta tag population from frontmatter
6. Test on one post, refine
**→ STOP HERE and show user for review**

### Phase 3: Convert All Posts
1. Run conversion script on all 8 posts
2. Manual review of each HTML file
3. Fix any LaTeX rendering issues
4. Verify code highlighting
5. Check image references

### Phase 4: Get Images from Obsidian Vault
1. Ask user for Obsidian vault path
2. Extract list of all image filenames needed
3. Copy images from vault to `/images/`
4. Optimize images if needed
5. Verify all images load in posts

### Phase 5: Create Infrastructure
1. Create `/posts/index.html` listing all posts
2. Create 8 redirect directories with index.html files
3. Update homepage `/index.html` with links to posts
4. Add CNAME file for GitHub Pages

### Phase 6: Test and Verify
1. Test locally with `python -m http.server`
2. Check all posts render correctly
3. Verify all LaTeX equations render
4. Test all redirects work
5. Test on mobile (resize browser)
6. Verify all internal links work

## Verification/Testing

**Local testing**:
```bash
cd /Users/kamile/code/new-website
python3 -m http.server 8000
# Visit http://localhost:8000
```

**Checklist**:
- [ ] All 8 posts render correctly
- [ ] LaTeX equations display in all posts
- [ ] All images load
- [ ] Code blocks have syntax highlighting
- [ ] Mobile layout works (test at 375px width)
- [ ] All 8 redirects work (old URL → new HTML page)
- [ ] Homepage links to all posts
- [ ] Posts index page lists all posts
- [ ] No 404 errors
- [ ] KaTeX loads from CDN

**Cross-browser**:
- Test in Chrome/Edge
- Test in Firefox
- Test in Safari (if available)

## Key Decisions Summary

1. **LaTeX**: KaTeX from CDN (fast, lightweight, adequate coverage)
2. **Code highlighting**: Pygments server-side (no extra JS)
3. **Conversion**: Python script + manual review
4. **Template**: Inline CSS in each HTML file
5. **URL structure**: `/posts/slug.html`
6. **Redirects**: Meta refresh, relative URLs to new posts on same domain
7. **Images**: Single `/images/` directory, copied from Obsidian vault
8. **Mobile**: Responsive by default, no media queries needed
9. **JavaScript**: Only KaTeX (for math rendering)
10. **Hosting**: GitHub Pages from repo root

## Notes

- Conversion script (`convert.py`) is a tool and doesn't need to be committed
- Images location: `/Users/kamile/kamilelukosiute/files`
- All 8 posts are hosted on the site (not migrating to Substack)
- Old URLs redirect to new HTML pages on same domain
- Keep design minimal and classic (no fancy features)
- Social cards: Parse from frontmatter when available; 4 posts have them, 4 don't
- Stop after Phase 1 and Phase 2 for user review before continuing
- **Layout requirement**: Blog posts and index page should be centered column on desktop (middle third/three-quarters of screen), full-screen on mobile
