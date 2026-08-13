#!/usr/bin/env node
/**
 * Accessibility Quality Gate — validates frontend against WCAG 2.1 AA.
 *
 * Checks:
 *   - Color contrast ratios
 *   - ARIA labels and attributes
 *   - Keyboard navigation (tab order, focus management)
 *   - Form labels and associations
 *   - Alt text on images
 *   - Heading hierarchy
 *   - Arabic/RTL specific: text direction, number formatting
 *
 * Usage:
 *   node config/quality-gates/accessibility-gate.js --url http://localhost:3000
 *   node config/quality-gates/accessibility-gate.js --url http://localhost:3000 --json
 *   node config/quality-gates/accessibility-gate.js --report-file axe-report.json
 *
 * Exit codes:
 *   0 — all checks pass (no critical/serious violations)
 *   1 — one or more critical or serious violations found
 */

const { execFileSync } = require('child_process');
const fs = require('fs');
const path = require('path');
const process = require('process');

function validateHttpUrl(value) {
  let parsed;
  try {
    parsed = new URL(value);
  } catch {
    throw new Error('Target must be a valid URL');
  }
  if (!['http:', 'https:'].includes(parsed.protocol)) {
    throw new Error('Target URL must use http or https');
  }
  return parsed.toString();
}

const GREEN = '\x1b[92m';
const RED = '\x1b[91m';
const YELLOW = '\x1b[93m';
const CYAN = '\x1b[96m';
const BOLD = '\x1b[1m';
const RESET = '\x1b[0m';

const args = process.argv.slice(2);
let targetUrl = null;
let jsonOutput = false;
let reportFile = null;
let verbose = false;

for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case '--url':
      targetUrl = args[++i];
      break;
    case '--json':
      jsonOutput = true;
      break;
    case '--report-file':
      reportFile = args[++i];
      break;
    case '--verbose':
    case '-v':
      verbose = true;
      break;
  }
}

if (!targetUrl && !reportFile) {
  console.error('Usage: node accessibility-gate.js --url <url> [--json] [--report-file <file>]');
  process.exit(1);
}

/**
 * Run axe-core against the target page using Puppeteer.
 */
async function runAxeScan(url) {
  const safeUrl = validateHttpUrl(url);
  const safeUrlLiteral = JSON.stringify(safeUrl);
  console.log(`Running axe-core scan against ${safeUrl}...`);
  let result;

  try {
    // Try using Puppeteer + axe-core via npx
    const script = `
      const puppeteer = require('puppeteer');
      const { AxeBuilder } = require('@axe-core/puppeteer');
      const fs = require('fs');

      (async () => {
        const browser = await puppeteer.launch({
          headless: 'new',
          args: ['--no-sandbox', '--disable-setuid-sandbox'],
        });
        const page = await browser.newPage();
        await page.setBypassCSP(true);
        await page.goto(${safeUrlLiteral}, { waitUntil: 'networkidle0', timeout: 30000 });
        const results = await new AxeBuilder({ page }).analyze();
        await browser.close();
        fs.writeFileSync('/tmp/axe-results.json', JSON.stringify(results, null, 2));
        console.log('Scan complete: ' + results.violations.length + ' violations');
      })();
    `;

    const tmpFile = '/tmp/axe-scan.js';
    fs.writeFileSync(tmpFile, script);
    execFileSync('node', ['axe-scan.js'], { cwd: '/tmp', stdio: 'pipe', timeout: 60000 });
    result = JSON.parse(fs.readFileSync('/tmp/axe-results.json', 'utf8'));
  } catch (e) {
    console.warn(YELLOW + '⚠ Puppeteer/axe-core not available, running simplified checks' + RESET);
    result = runSimplifiedChecks(safeUrl);
  }

  return result;
}

/**
 * Run simplified HTML validation when axe-core is not available.
 */
function runSimplifiedChecks(url) {
  const safeUrl = validateHttpUrl(url);
  const violations = [];

  try {
    const html = execFileSync(
      'curl',
      ['--fail', '--silent', '--show-error', '--location', '--max-time', '15', '--', safeUrl],
      { timeout: 15000 },
    ).toString();
    if (!html) {
      violations.push({
        id: 'page-unreachable',
        impact: 'critical',
        tags: ['critical'],
        description: `Could not fetch ${safeUrl}`,
        nodes: [{ html: safeUrl }],
      });
      return { violations, passes: [], incomplete: [] };
    }

    // Check for lang attribute (Arabic sites should have dir and lang)
    if (!html.match(/lang\s*=\s*["']ar["']/i)) {
      violations.push({
        id: 'html-lang',
        impact: 'serious',
        tags: ['wcag2aa', 'wcag311'],
        description: 'Page should have lang="ar" attribute for Arabic sites',
        nodes: [{ html: html.substring(0, 200) }],
      });
    }

    // Check for dir attribute (RTL)
    if (!html.match(/dir\s*=\s*["']rtl["']/i) && html.includes('ar')) {
      violations.push({
        id: 'dir-attribute',
        impact: 'serious',
        tags: ['wcag2aa', 'rtl'],
        description: 'Arabic page should have dir="rtl" attribute',
        nodes: [{ html: html.substring(0, 200) }],
      });
    }

    // Check for missing alt text on images
    const imgRegex = /<img[^>]+(?:src\s*=\s*["']([^"']+)["'])(?:(?!alt)[^>])*>/gi;
    let match;
    while ((match = imgRegex.exec(html)) !== null) {
      const imgTag = match[0];
      if (!imgTag.includes('alt=') || imgTag.match(/alt\s*=\s*["']\s*["']/)) {
        violations.push({
          id: 'image-alt',
          impact: 'serious',
          tags: ['wcag2aa', 'wcag111'],
          description: 'Image missing alt text: ' + (match[1] || 'unknown'),
          nodes: [{ html: imgTag.substring(0, 100), target: [match[1]] }],
        });
      }
    }

    // Check for form labels
    const formInputRegex = /<input[^>]+type\s*=\s*["'](?:text|email|password|tel|number|search|url)["'][^>]*>/gi;
    while ((match = formInputRegex.exec(html)) !== null) {
      const inputTag = match[0];
      const hasAriaLabel = inputTag.includes('aria-label=');
      const hasAriaLabelledby = inputTag.includes('aria-labelledby=');
      if (!hasAriaLabel && !hasAriaLabelledby) {
        violations.push({
          id: 'form-label',
          impact: 'critical',
          tags: ['wcag2aa', 'wcag412'],
          description: 'Form input missing accessible label',
          nodes: [{ html: inputTag.substring(0, 100) }],
        });
      }
    }

    // Check heading hierarchy (h1 should be first)
    const h1s = (html.match(/<h1[^>]*>/gi) || []).length;
    const h2s = (html.match(/<h2[^>]*>/gi) || []).length;
    if (h1s === 0) {
      violations.push({
        id: 'heading-order',
        impact: 'serious',
        tags: ['wcag2aa', 'wcag131'],
        description: 'Page missing h1 heading',
        nodes: [{ html: html.substring(0, 200) }],
      });
    }

    // Check color contrast (basic inline style detection)
    const lowContrastColors = ['#999', '#aaa', '#bbb', '#ccc', '#ddd', '#eee'];
    for (const color of lowContrastColors) {
      const colorRegex = new RegExp(`color\\s*:\\s*${color}\\b`, 'gi');
      if (colorRegex.test(html)) {
        violations.push({
          id: 'color-contrast',
          impact: 'serious',
          tags: ['wcag2aa', 'wcag143'],
          description: `Potential low contrast color used: ${color}`,
          nodes: [],
        });
        break;
      }
    }

  } catch (e) {
    violations.push({
      id: 'scan-error',
      impact: 'critical',
      tags: ['critical'],
      description: `Scan error: ${e.message}`,
      nodes: [],
    });
  }

  return { violations, passes: [], incomplete: [] };
}

/**
 * Check for RTL/Arabic specific issues.
 */
function checkArabicRTL(html) {
  const issues = [];

  if (!html) return issues;

  // Check text direction
  if (!html.match(/dir\s*=\s*["'](rtl|auto)["']/i)) {
    issues.push({
      id: 'rtl-direction',
      impact: 'serious',
      tags: ['rtl', 'i18n'],
      description: 'Arabic content should use dir="rtl" or dir="auto"',
    });
  }

  // Check for Arabic number formatting awareness
  const arabicChars = html.match(/[\u0600-\u06FF\u0750-\u077F]/);
  if (arabicChars) {
    const hasNumberFormatting = html.includes('Intl.NumberFormat') ||
      html.includes('toLocaleString') ||
      html.includes('ar-') ||
      html.includes('arab');
    if (!hasNumberFormatting) {
      issues.push({
        id: 'number-formatting',
        impact: 'serious',
        tags: ['rtl', 'i18n'],
        description: 'Arabic content present but no Arabic number formatting detected (Intl.NumberFormat with ar)',
      });
    }
  }

  return issues;
}

/**
 * Classify violations by severity.
 */
function classifyViolations(violations) {
  const critical = [];
  const serious = [];
  const moderate = [];
  const minor = [];

  for (const v of violations) {
    const impact = v.impact || 'minor';
    switch (impact) {
      case 'critical':
        critical.push(v);
        break;
      case 'serious':
        serious.push(v);
        break;
      case 'moderate':
        moderate.push(v);
        break;
      default:
        minor.push(v);
    }
  }

  return { critical, serious, moderate, minor };
}

/**
 * Print report and return exit code.
 */
function printReport(results, rtlIssues, jsonOutput) {
  const allViolations = results.violations || [];
  const { critical, serious, moderate, minor } = classifyViolations(allViolations);

  // Add RTL issues as serious
  const rtlSerious = rtlIssues.filter(i => i.impact === 'serious');
  serious.push(...rtlSerious);

  const passed = critical.length === 0 && serious.length === 0;

  if (jsonOutput) {
    const report = {
      timestamp: new Date().toISOString(),
      passed,
      summary: { critical: critical.length, serious: serious.length, moderate: moderate.length, minor: minor.length, total: allViolations.length + rtlIssues.length },
      violations: allViolations,
      rtlIssues,
    };
    console.log(JSON.stringify(report, null, 2));
    return passed ? 0 : 1;
  }

  console.log(`\n${BOLD}═══ Accessibility Quality Gate Report ═══${RESET}\n`);

  if (passed && allViolations.length === 0 && rtlIssues.length === 0) {
    console.log(`  ${GREEN}All accessibility checks passed!${RESET}\n`);
    return 0;
  }

  if (critical.length > 0) {
    console.log(`  ${BOLD}${RED}Critical Violations (${critical.length}):${RESET}`);
    for (const v of critical) {
      console.log(`    ${RED}✗${RESET} [${v.id}] ${v.description}`);
      if (v.nodes && v.nodes.length > 0 && verbose) {
        console.log(`       ${CYAN}Element:${RESET} ${(v.nodes[0].html || '').substring(0, 120)}`);
      }
    }
    console.log();
  }

  if (serious.length > 0) {
    console.log(`  ${BOLD}${YELLOW}Serious Violations (${serious.length}):${RESET}`);
    for (const v of serious) {
      const tag = v.tags && v.tags.includes('rtl') ? ' [RTL]' : '';
      console.log(`    ${YELLOW}⚠${RESET} [${v.id}]${tag} ${v.description}`);
    }
    console.log();
  }

  if (moderate.length > 0 && verbose) {
    console.log(`  ${BOLD}Moderate (${moderate.length}):${RESET}`);
    for (const v of moderate) {
      console.log(`    ${CYAN}ℹ${RESET} [${v.id}] ${v.description}`);
    }
    console.log();
  }

  console.log(`  Summary: ${RED}${critical.length} critical${RESET}, ${YELLOW}${serious.length} serious${RESET}, ${moderate.length} moderate, ${minor.length} minor`);
  console.log();

  return passed ? 0 : 1;
}

async function main() {
  let results;
  let html = '';

  if (reportFile) {
    results = JSON.parse(fs.readFileSync(reportFile, 'utf8'));
  } else {
    results = await runAxeScan(targetUrl);
    try {
      const safeTargetUrl = validateHttpUrl(targetUrl);
      html = execFileSync(
        'curl',
        ['--fail', '--silent', '--show-error', '--location', '--max-time', '15', '--', safeTargetUrl],
        { timeout: 15000 },
      ).toString();
    } catch (e) { /* ignore */ }
  }

  const rtlIssues = checkArabicRTL(html);
  const exitCode = printReport(results, rtlIssues, jsonOutput);
  process.exit(exitCode);
}

main().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
