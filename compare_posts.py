import asyncio
from playwright.async_api import async_playwright
import os
from pathlib import Path

# Map old URLs to new URLs
posts = [
    {
        'name': 'american-character',
        'old_path': '/essays/American+Character/index.html',
        'new_path': '/posts/american-character.html'
    },
    {
        'name': 'design-for-defenders',
        'old_path': '/llms/Design+for+the+defenders+you+care+about+or+risk+being+useless/index.html',
        'new_path': '/posts/design-for-the-defenders-you-care-about-or-risk-being-useless.html'
    },
    {
        'name': 'building-evals-cybersecurity',
        'old_path': '/llms/Building+evaluations+for+cybersecurity+assistance/index.html',
        'new_path': '/posts/building-evaluations-for-cybersecurity-assistance.html'
    },
    {
        'name': 'spending-money-on-evals',
        'old_path': '/llms/You+need+to+be+spending+more+money+on+evals/index.html',
        'new_path': '/posts/you-need-to-be-spending-more-money-on-evals.html'
    },
    {
        'name': 'standardized-tests',
        'old_path': '/llms/Maybe+don\'t+give+language+models+standardized+tests/index.html',
        'new_path': '/posts/maybe-dont-give-language-models-standardized-tests.html'
    },
    {
        'name': 'neutron-star-mergers',
        'old_path': '/physics/Neutron+star+mergers+and+fast+surrogate+modeling/index.html',
        'new_path': '/posts/neutron-star-mergers-and-fast-surrogate-modeling.html'
    },
    {
        'name': 'bcewithlogits',
        'old_path': '/pytorch/What+does+BCEWithLogits+actually+do%3F/index.html',
        'new_path': '/posts/what-does-bcewithlogits-actually-do.html'
    },
    {
        'name': 'tensor-view',
        'old_path': '/pytorch/When+can+a+tensor+be+view()ed%3F/index.html',
        'new_path': '/posts/when-can-a-tensor-be-viewed.html'
    }
]

async def take_scrolling_screenshots(page, url, output_prefix, screenshot_dir):
    print(f"\nNavigating to: {url}")
    await page.goto(url, wait_until='networkidle')

    # Wait a bit for any dynamic content
    await asyncio.sleep(2)

    # Check if this is an Obsidian Publish site with scrollable container
    scrollable_element = await page.evaluate('''
        () => {
            // Try to find Obsidian Publish scrollable container
            const obsidianContainer = document.querySelector('.markdown-preview-view, .view-content, .markdown-source-view, .mod-active .markdown-preview-sizer');
            if (obsidianContainer && obsidianContainer.scrollHeight > obsidianContainer.clientHeight) {
                return '.markdown-preview-view, .view-content, .markdown-source-view, .mod-active .markdown-preview-sizer';
            }
            return null;
        }
    ''')

    if scrollable_element:
        # Obsidian Publish site - scroll the inner container
        print("Detected Obsidian Publish site with scrollable container")
        total_height = await page.evaluate(f'''
            document.querySelector('{scrollable_element}').scrollHeight
        ''')
    else:
        # Regular site - scroll the window
        total_height = await page.evaluate('''
            Math.max(
                document.body.scrollHeight,
                document.documentElement.scrollHeight,
                document.body.offsetHeight,
                document.documentElement.offsetHeight
            )
        ''')

    viewport_height = page.viewport_size['height']
    print(f"Total height: {total_height}px, Viewport: {viewport_height}px")

    # Take screenshot of the top
    await page.screenshot(path=os.path.join(screenshot_dir, f"{output_prefix}_01_top.png"))

    # Calculate how many screenshots we need (with overlap)
    overlap = 100  # pixels of overlap
    scroll_step = viewport_height - overlap
    num_screenshots = (total_height + scroll_step - 1) // scroll_step

    screenshot_num = 2
    current_scroll = 0

    # Scroll and take screenshots
    for i in range(1, num_screenshots):
        current_scroll += scroll_step

        # Don't scroll past the bottom
        if current_scroll + viewport_height > total_height:
            current_scroll = total_height - viewport_height

        if scrollable_element:
            # Scroll the Obsidian container
            await page.evaluate(f'''
                document.querySelector('{scrollable_element}').scrollTop = {current_scroll}
            ''')
        else:
            # Scroll the window
            await page.evaluate(f'window.scrollTo(0, {current_scroll})')

        await asyncio.sleep(0.5)  # Wait for any lazy-loaded content

        screenshot_num_str = str(screenshot_num).zfill(2)
        await page.screenshot(
            path=os.path.join(screenshot_dir, f"{output_prefix}_{screenshot_num_str}.png")
        )

        print(f"Screenshot {screenshot_num}/{num_screenshots}: scrolled to {current_scroll}px")
        screenshot_num += 1

        # If we've reached the bottom, stop
        if current_scroll >= total_height - viewport_height:
            break

    # Reset scroll position
    if scrollable_element:
        await page.evaluate(f"document.querySelector('{scrollable_element}').scrollTop = 0")
    else:
        await page.evaluate('window.scrollTo(0, 0)')

async def main():
    base_dir = Path(__file__).parent
    screenshot_dir = base_dir / 'screenshots_comparison'

    # Create screenshot directory
    screenshot_dir.mkdir(exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        for post in posts:
            print(f"\n{'=' * 80}")
            print(f"Processing: {post['name']}")
            print('=' * 80)

            # Take screenshots of OLD version (from live site)
            old_url = f"https://kamilelukosiute.com{post['old_path'].replace('/index.html', '')}"
            print('\n--- OLD VERSION ---')
            await take_scrolling_screenshots(page, old_url, f"{post['name']}_OLD", str(screenshot_dir))

            # Take screenshots of NEW version (from local files)
            new_file = (base_dir / post['new_path'].lstrip('/')).resolve()
            new_url = new_file.as_uri()
            print('\n--- NEW VERSION ---')
            await take_scrolling_screenshots(page, new_url, f"{post['name']}_NEW", str(screenshot_dir))

        await browser.close()

        print(f"\n{'=' * 80}")
        print(f"Done! Screenshots saved to: {screenshot_dir}")
        print('=' * 80)

if __name__ == '__main__':
    asyncio.run(main())
