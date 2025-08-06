/**
 * Framework verification test for Node.js projects.
 *
 * This test ensures the AI-First SDLC framework is properly set up.
 * It can run in empty repositories and passes basic CI/CD validation.
 *
 * Replace this test with real project tests as you develop your application.
 *
 * Run with: npm test (if configured) or node framework.test.js
 */

const fs = require('fs');
const path = require('path');

/**
 * Test framework structure exists
 */
function testFrameworkStructure() {
    const requiredFiles = [
        'README.md',
        'CLAUDE.md'
    ];

    const requiredDirs = [
        'docs/feature-proposals',
        'retrospectives'
    ];

    // Check required files
    for (const filePath of requiredFiles) {
        if (!fs.existsSync(filePath)) {
            throw new Error(`Required file missing: ${filePath}`);
        }
    }

    // Check required directories
    for (const dirPath of requiredDirs) {
        if (!fs.existsSync(dirPath) || !fs.statSync(dirPath).isDirectory()) {
            throw new Error(`Required directory missing: ${dirPath}`);
        }
    }
}

/**
 * Test CLAUDE.md has required content
 */
function testClaudeMdContent() {
    if (!fs.existsSync('CLAUDE.md')) {
        throw new Error('CLAUDE.md not found');
    }

    const content = fs.readFileSync('CLAUDE.md', 'utf8').toLowerCase();

    const requiredPatterns = [
        'claude.md',
        'ai development',
        'git workflow',
        'never push directly to main'
    ];

    for (const pattern of requiredPatterns) {
        if (!content.includes(pattern)) {
            throw new Error(`CLAUDE.md missing required pattern: ${pattern}`);
        }
    }
}

/**
 * Test .gitignore exists and has AI patterns
 */
function testGitignoreExists() {
    if (!fs.existsSync('.gitignore')) {
        console.log('Warning: .gitignore not found (run setup-smart.py to create)');
        return;
    }

    const content = fs.readFileSync('.gitignore', 'utf8').toLowerCase();

    const aiPatterns = ['.claude', '.cursor', '.aider'];
    const foundPatterns = aiPatterns.filter(pattern => content.includes(pattern));

    if (foundPatterns.length === 0) {
        console.log('Info: Consider adding AI tool patterns to .gitignore');
    }
}

/**
 * Test Node.js environment
 */
function testNodeEnvironment() {
    const nodeVersion = process.version;
    const majorVersion = parseInt(nodeVersion.substring(1).split('.')[0]);

    if (majorVersion < 16) {
        throw new Error(`Node.js 16+ recommended, found ${nodeVersion}`);
    }

    // Check if package.json exists
    if (fs.existsSync('package.json')) {
        try {
            const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
            if (!pkg.name) {
                console.log('Info: Consider adding project name to package.json');
            }
        } catch (e) {
            throw new Error('Invalid package.json format');
        }
    }
}

/**
 * Test git repository
 */
function testGitRepository() {
    if (!fs.existsSync('.git') || !fs.statSync('.git').isDirectory()) {
        throw new Error('Not a git repository (run \'git init\')');
    }
}

/**
 * Main test runner
 */
function main() {
    const tests = [
        { name: 'Framework Structure', fn: testFrameworkStructure },
        { name: 'CLAUDE.md Content', fn: testClaudeMdContent },
        { name: 'Gitignore Exists', fn: testGitignoreExists },
        { name: 'Node Environment', fn: testNodeEnvironment },
        { name: 'Git Repository', fn: testGitRepository }
    ];

    console.log('🔍 Running AI-First SDLC framework verification...');

    let passed = 0;
    let failed = 0;

    for (const test of tests) {
        try {
            test.fn();
            console.log(`✅ ${test.name}`);
            passed++;
        } catch (error) {
            console.log(`❌ ${test.name}: ${error.message}`);
            failed++;
        }
    }

    console.log(`\n📊 Results: ${passed} passed, ${failed} failed`);

    if (failed === 0) {
        console.log('🎉 Framework verification complete! Ready for development.');
        process.exit(0);
    } else {
        console.log('🔧 Please fix the issues above before proceeding.');
        process.exit(1);
    }
}

// Support both direct execution and Jest testing
if (require.main === module) {
    main();
} else {
    // Export for Jest or other test runners
    module.exports = {
        testFrameworkStructure,
        testClaudeMdContent,
        testGitignoreExists,
        testNodeEnvironment,
        testGitRepository
    };
}