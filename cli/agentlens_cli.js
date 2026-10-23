#!/usr/bin/env node

/**
 * AgentLens Node.js CLI
 * Usage:
 *   node agentlens_cli.js --repo owner/repo
 *   npx agentlens --repo owner/repo
 */

const https = require('https');

function parseArgs() {
  const args = process.argv.slice(2);
  const options = {
    repo: process.env.AGENTLENS_REPO || process.env.GITHUB_REPOSITORY || '',
    token: process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '',
    format: 'markdown'
  };

  for (let i = 0; i < args.length; i++) {
    if (args[i] === '--repo' || args[i] === '-r') options.repo = args[++i];
    else if (args[i] === '--token' || args[i] === '-t') options.token = args[++i];
    else if (args[i] === '--format' || args[i] === '-f') options.format = args[++i];
  }
  return options;
}

const opts = parseArgs();
if (!opts.repo || !opts.repo.includes('/')) {
  console.error('Usage: node agentlens_cli.js --repo owner/repo [--token GITHUB_TOKEN]');
  process.exit(1);
}

const reqOpts = {
  hostname: 'api.github.com',
  path: `/repos/${opts.repo}/issues?state=open&per_page=50`,
  method: 'GET',
  headers: {
    'User-Agent': 'AgentLens-Node-CLI/1.0',
    'Accept': 'application/vnd.github.v3+json',
    ...(opts.token ? { 'Authorization': `Bearer ${opts.token}` } : {})
  }
};

https.get(reqOpts, (res) => {
  let body = '';
  res.on('data', chunk => body += chunk);
  res.on('end', () => {
    try {
      const data = JSON.parse(body);
      if (!Array.isArray(data)) {
        console.error('GitHub API error:', data.message || body);
        process.exit(1);
      }

      const issues = data.filter(i => !i.pull_request);
      if (opts.format === 'json') {
        console.log(JSON.stringify(issues, null, 2));
        return;
      }

      console.log(`\n# 🎯 Open AgentLens Issues for ${opts.repo} (${issues.length})\n`);
      issues.forEach(i => {
        console.log(`- **#${i.number}**: ${i.title}`);
        console.log(`  Link: ${i.html_url}`);
      });
      console.log('\nUse python3 cli/fetch_issues.py for deep DOM directive parsing.\n');
    } catch (e) {
      console.error('Failed to parse response:', e.message);
    }
  });
}).on('error', err => {
  console.error('Request failed:', err.message);
});
