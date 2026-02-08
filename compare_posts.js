const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

// Map old URLs to new URLs
const posts = [
  {
    name: 'american-character',
    oldPath: '/essays/American+Character/index.html',
    newPath: '/posts/american-character.html'
  },
  {
    name: 'design-for-defenders',
    oldPath: '/llms/Design+for+the+defenders+you+care+about+or+risk+being+useless/index.html',
    newPath: '/posts/design-for-the-defenders-you-care-about-or-risk-being-useless.html'
  },
  {
    name: 'building-evals-cybersecurity',
    oldPath: '/llms/Building+evaluations+for+cybersecurity+assistance/index.html',
    newPath: '/posts/building-evaluations-for-cybersecurity-assistance.html'
  },
  {
    name: 'spending-money-on-evals',
    oldPath: '/llms/You+need+to+be+spending+more+money+on+evals/index.html',
    newPath: '/posts/you-need-to-be-spending-more-money-on-evals.html'
  },
  {
    name: 'standardized-tests',
    oldPath: '/llms/Maybe+don\'t+give+language+models+standardized+tests/index.html',
    newPath: '/posts/maybe-dont-give-language-models-standardized-tests.html'
  },
  {
    name: 'neutron-star-mergers',
    oldPath: '/physics/Neutron+star+mergers+and+fast+surrogate+modeling/index.html',
    newPath: '/posts/neutron-star-mergers-and-fast-surrogate-modeling.html'
  },
  {
    name: 'bcewithlogits',
    oldPath: '/pytorch/What+does+BCEWithLogits+actually+do%3F/index.html',
    newPath: '/posts/what-does-bcewithlogits-actually-do.html'
  },
  {
    name: 'tensor-view',
    oldPath: '/pytorch/When+can+a+tensor+be+view()ed%3F/index.html',
    newPath: '/posts/when-can-a-tensor-be-viewed.html'
  }
];

async function takeScrollingScreenshots(page, url, outputPrefix, screenshotDir) {
  console.log(`\nNavigating to: ${url}`);
  await page.goto(url, { waitUntil: 'networkidle' });

  // Wait a bit for any dynamic content
  await page.waitForTimeout(1000);

  // Get the total height of the page
  const totalHeight = await page.evaluate(() => document.body.scrollHeight);
  const viewportHeight = page.viewportSize().height;

  console.log(`Total height: ${totalHeight}px, Viewport: ${viewportHeight}px`);

  // Take screenshot of the top
  await page.screenshot({
    path: path.join(screenshotDir, `${outputPrefix}_01_top.png`),
    fullPage: false
  });

  // Calculate how many screenshots we need (with overlap)
  const overlap = 100; // pixels of overlap
  const scrollStep = viewportHeight - overlap;
  const numScreenshots = Math.ceil(totalHeight / scrollStep);

  let screenshotNum = 2;
  let currentScroll = 0;

  // Scroll and take screenshots
  for (let i = 1; i < numScreenshots; i++) {
    currentScroll += scrollStep;

    // Don't scroll past the bottom
    if (currentScroll + viewportHeight > totalHeight) {
      currentScroll = totalHeight - viewportHeight;
    }

    await page.evaluate((y) => window.scrollTo(0, y), currentScroll);
    await page.waitForTimeout(500); // Wait for any lazy-loaded content

    const screenshotNumStr = screenshotNum.toString().padStart(2, '0');
    await page.screenshot({
      path: path.join(screenshotDir, `${outputPrefix}_${screenshotNumStr}.png`),
      fullPage: false
    });

    console.log(`Screenshot ${screenshotNum}/${numScreenshots}: scrolled to ${currentScroll}px`);
    screenshotNum++;

    // If we've reached the bottom, stop
    if (currentScroll >= totalHeight - viewportHeight) {
      break;
    }
  }

  // Reset scroll position
  await page.evaluate(() => window.scrollTo(0, 0));
}

async function main() {
  const screenshotDir = path.join(__dirname, 'screenshots_comparison');

  // Create screenshot directory
  if (!fs.existsSync(screenshotDir)) {
    fs.mkdirSync(screenshotDir);
  }

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1920, height: 1080 }
  });
  const page = await context.newPage();

  const baseUrl = `file://${__dirname}`;

  for (const post of posts) {
    console.log(`\n${'='.repeat(80)}`);
    console.log(`Processing: ${post.name}`);
    console.log('='.repeat(80));

    // Take screenshots of OLD version
    const oldUrl = `${baseUrl}${post.oldPath}`;
    console.log('\n--- OLD VERSION ---');
    await takeScrollingScreenshots(page, oldUrl, `${post.name}_OLD`, screenshotDir);

    // Take screenshots of NEW version
    const newUrl = `${baseUrl}${post.newPath}`;
    console.log('\n--- NEW VERSION ---');
    await takeScrollingScreenshots(page, newUrl, `${post.name}_NEW`, screenshotDir);
  }

  await browser.close();

  console.log(`\n${'='.repeat(80)}`);
  console.log('Done! Screenshots saved to:', screenshotDir);
  console.log('='.repeat(80));
}

main().catch(console.error);
