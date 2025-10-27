const express = require('express');
const path = require('path');
const nodemailer = require('nodemailer');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.static('public'));
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

// Run demo endpoint
app.post('/api/run-demo', async (req, res) => {
    const { university_goal } = req.body;
    
    if (!university_goal) {
        return res.json({ 
            success: false, 
            error: 'University goal is required' 
        });
    }
    
    try {
        // Execute Python demo runner
        const { spawn } = require('child_process');
        const path = require('path');
        
        const backendPath = path.join(__dirname, '..', 'backend', 'backend');
        const scriptPath = path.join(backendPath, 'run_demo_cli.py');
        const venvPython = path.join(backendPath, 'venv', 'bin', 'python3');
        
        // Use virtual environment Python if available, otherwise fall back to system python3
        const fs = require('fs');
        const pythonPath = fs.existsSync(venvPython) ? venvPython : 'python3';
        
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
            stdio: ['pipe', 'pipe', 'pipe']  // Explicit stdio
        });
        
        let resultData = '';
        let errorData = '';
        
        pythonProcess.stdout.on('data', (data) => {
            resultData += data.toString();
        });
        
        pythonProcess.stderr.on('data', (data) => {
            // Capture stderr for error messages
            errorData += data.toString();
        });
        
        pythonProcess.on('close', (code) => {
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
                        res.json(result);
                    } else {
                        // If no single-line JSON, try to parse the whole thing
                        const result = JSON.parse(resultData.trim());
                        res.json(result);
                    }
                } catch (e) {
                    res.json({
                        success: false,
                        error: `Failed to parse result: ${e.message}. Output: ${resultData.substring(0, 500)}`
                    });
                }
            } else {
                // Include error output for debugging
                const errorPreview = errorData.substring(0, 1000);
                res.json({
                    success: false,
                    error: `Python script failed with code ${code}. Error: ${errorPreview}`
                });
            }
        });
        
    } catch (error) {
        res.json({ 
            success: false, 
            error: error.message 
        });
    }
});

app.listen(PORT, () => {
    console.log(`UDiscovery landing page running on http://localhost:${PORT}`);
});
