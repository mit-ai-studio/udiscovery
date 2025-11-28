const express = require('express');
const path = require('path');
const nodemailer = require('nodemailer');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/signin', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'signin.html'));
});

app.get('/demo', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'demo.html'));
});

// Demo request endpoint
app.post('/api/demo-request', (req, res) => {
    const { name, email, university, role, message } = req.body;
    
    // In a real implementation, you would:
    // 1. Save to database
    // 2. Send email notification
    // 3. Add to CRM
    
    console.log('Demo request received:', { name, email, university, role, message });
    
    res.json({ 
        success: true, 
        message: 'Thank you for your interest! We\'ll be in touch soon.' 
    });
});

// Waitlist signup endpoint
app.post('/api/waitlist', (req, res) => {
    const { email, interests } = req.body;
    
    console.log('Waitlist signup:', { email, interests });
    
    res.json({ 
        success: true, 
        message: 'You\'ve been added to our waitlist!' 
    });
});

// Sign in endpoint (placeholder)
app.post('/api/signin', (req, res) => {
    const { email, password, dataLink } = req.body;
    
    // In a real implementation, you would:
    // 1. Validate credentials
    // 2. Check data link format
    // 3. Authenticate user
    
    console.log('Sign in attempt:', { email, dataLink });
    
    res.json({ 
        success: true, 
        message: 'Sign in successful! Redirecting to dashboard...' 
    });
});

// Test endpoint to verify server is working
app.get('/api/test', (req, res) => {
    res.json({ 
        success: true, 
        message: 'Server is running!',
        timestamp: new Date().toISOString()
    });
});

// Run demo endpoint
app.post('/api/run-demo', async (req, res) => {
    // Set a longer timeout for batch processing (30 minutes)
    req.setTimeout(30 * 60 * 1000);
    res.setTimeout(30 * 60 * 1000);
    
    const { university_goal } = req.body;
    
    if (!university_goal) {
        return res.json({ 
            success: false, 
            error: 'University goal is required' 
        });
    }
    
    // Flag to prevent multiple responses
    let responseSent = false;
    const sendResponse = (data) => {
        if (!responseSent) {
            responseSent = true;
            res.json(data);
        }
    };
    
    try {
        // Execute Python demo runner
        const { spawn } = require('child_process');
        const path = require('path');
        const fs = require('fs');
        
        const backendPath = path.join(__dirname, '..', 'backend');
        const scriptPath = path.join(backendPath, 'run_demo_cli.py');
        
        // Check if script exists
        if (!fs.existsSync(scriptPath)) {
            return sendResponse({
                success: false,
                error: `Python script not found at: ${scriptPath}`
            });
        }
        
        // Try multiple Python paths (prioritize venv)
        const pythonPaths = [
            path.join(backendPath, 'venv', 'bin', 'python3'),
            path.join(backendPath, 'venv', 'bin', 'python'),
            'python3',
            'python'
        ];
        
        let pythonPath = null;
        for (const p of pythonPaths) {
            if (p.startsWith('/') || p.includes('venv')) {
                // Absolute path or venv path - check if exists
                if (fs.existsSync(p)) {
                    pythonPath = p;
                    break;
                }
            } else {
                // System command - try to find it
                try {
                    const { execSync } = require('child_process');
                    execSync(`which ${p}`, { stdio: 'ignore' });
                    pythonPath = p;
                    break;
                } catch (e) {
                    continue;
                }
            }
        }
        
        if (!pythonPath) {
            return sendResponse({
                success: false,
                error: 'Python not found. Please ensure Python 3 is installed.'
            });
        }
        
        console.log(`Using Python: ${pythonPath}`);
        console.log(`Script path: ${scriptPath}`);
        console.log(`Working directory: ${backendPath}`);
        
        // Execute the Python script with the university goal
        const pythonProcess = spawn(pythonPath, [
            '-u',  // Unbuffered stdout
            scriptPath,
            JSON.stringify(university_goal)
        ], {
            cwd: backendPath,
            env: { 
                ...process.env, 
                PYTHONUNBUFFERED: '1', 
                PYTHONIOENCODING: 'utf-8',
                NO_COLOR: '1',
                TERM: 'dumb'  // Disable color output
            },
            stdio: ['ignore', 'pipe', 'pipe']  // stdin:ignore to prevent lock issues with daemon threads
        });
        
        let resultData = '';
        let errorData = '';
        
        pythonProcess.stdout.on('data', (data) => {
            resultData += data.toString();
            // Log progress for debugging
            console.log('Python stdout:', data.toString().substring(0, 200));
        });
        
        pythonProcess.stderr.on('data', (data) => {
            // Capture stderr for error messages
            const errorText = data.toString();
            errorData += errorText;
            // Log errors immediately
            console.error('Python stderr:', errorText);
        });
        
        // Handle process errors (e.g., Python not found)
        pythonProcess.on('error', (error) => {
            console.error('Python process spawn error:', error);
            sendResponse({
                success: false,
                error: `Failed to start Python process: ${error.message}. Make sure Python 3 is installed and accessible.`
            });
        });
        
        pythonProcess.on('close', (code) => {
            console.log(`Python process exited with code ${code}`);
            console.log(`Result data length: ${resultData.length}`);
            console.log(`Error data length: ${errorData.length}`);
            
            if (code === 0) {
                try {
                    // Try to extract JSON from the output
                    // Look for the last valid JSON object
                    const lines = resultData.split('\n');
                    let jsonFound = false;
                    let jsonLine = '';
                    
                    // Try to find JSON in reverse order
                    for (let i = lines.length - 1; i >= 0; i--) {
                        const line = lines[i].trim();
                        if (line.startsWith('{') || line.startsWith('[')) {
                            try {
                                JSON.parse(line);
                                jsonLine = line;
                                jsonFound = true;
                                break;
                            } catch (e) {
                                continue;
                            }
                        }
                    }
                    
                    if (jsonFound) {
                        const result = JSON.parse(jsonLine);
                        sendResponse(result);
                    } else {
                        // If no single-line JSON, try to parse the whole thing
                        const result = JSON.parse(resultData.trim());
                        sendResponse(result);
                    }
                } catch (e) {
                    console.error('Failed to parse result:', e);
                    console.error('Result data preview:', resultData.substring(0, 1000));
                    console.error('Error data:', errorData.substring(0, 1000));
                    sendResponse({
                        success: false,
                        error: `Failed to parse result: ${e.message}. Output: ${resultData.substring(0, 500)}. Errors: ${errorData.substring(0, 500)}`
                    });
                }
            } else {
                // Include error output for debugging
                const errorPreview = errorData.substring(0, 2000);
                const resultPreview = resultData.substring(0, 500);
                console.error('Python script failed:', { code, errorPreview, resultPreview });
                sendResponse({
                    success: false,
                    error: `Python script failed with code ${code}. Error: ${errorPreview}`
                });
            }
        });
        
    } catch (error) {
        console.error('Top-level error in /api/run-demo:', error);
        sendResponse({ 
            success: false, 
            error: error.message 
        });
    }
});

app.listen(PORT, () => {
    console.log(`UDiscovery landing page running on http://localhost:${PORT}`);
});
