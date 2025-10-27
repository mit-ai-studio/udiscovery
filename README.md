# UDiscovery - AI-Powered Student Pipeline Optimization

A complete platform for universities to autonomously discover and evaluate prospective graduate students using AI agents and Kaggle datasets.

## Features

- **Modern, Responsive Design**: Clean, professional interface that works on all devices
- **Interactive Elements**: Smooth scrolling, animated visualizations, and modal forms
- **AI-Powered Demo**: Interactive demo page where users can test the UDiscovery pipeline
- **5-Agent CrewAI Pipeline**: Automated candidate discovery using specialized AI agents
- **Kaggle Integration**: Automatic dataset discovery and candidate scoring
- **Form Handling**: Demo requests, waitlist signups, and sign-in functionality
- **Professional Copy**: Targeted messaging for university enrollment professionals

## Project Structure

```
udiscovery/
├── frontend/                    # Landing page and web interface
│   ├── package.json             # Node.js dependencies
│   ├── server.js                # Express server
│   └── public/                  # Static files
│       ├── index.html           # Main landing page
│       ├── demo.html            # Interactive demo page
│       ├── signin.html          # Sign-in page
│       ├── css/styles.css
│       └── js/main.js
├── backend/backend/              # AI agentic pipeline
│   ├── test_real_agents.py      # Working 5-agent pipeline
│   ├── demo_runner.py          # Demo runner for web interface
│   ├── run_demo_cli.py          # CLI interface
│   ├── .env                      # Environment variables (API keys)
│   └── requirements.txt         # Python dependencies
└── README.md                     # This file
```

## Sections

1. **Navigation Bar**: Logo, navigation links, Sign In and Request Demo buttons
2. **Hero Section**: Main value proposition with animated data visualization
3. **The Problem**: Pain points for university enrollment offices
4. **The Solution**: How UDiscovery's AI Discovery Agent works
5. **The Vision**: Future features and waitlist signup
6. **Final CTA**: Demo request and sign-in links
7. **Sign-In Page**: Dedicated authentication page

## Getting Started

### Frontend Setup

1. **Install Dependencies**:
   ```bash
   cd frontend
   npm install
   ```

2. **Start the Server**:
   ```bash
   npm start
   ```

3. **View the Site**:
   Open your browser to `http://localhost:3000`

### Backend Setup

1. **Create Virtual Environment**:
   ```bash
   cd backend/backend
   python3.12 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   Create a `.env` file in `backend/backend/`:
   ```env
   GOOGLE_API_KEY=your_google_api_key_here
   KAGGLE_USERNAME=your_kaggle_username
   KAGGLE_KEY=your_kaggle_api_key
   ```

### Running the Interactive Demo

1. Start the frontend server
2. Navigate to `http://localhost:3000/demo`
3. Choose either the HGSE pre-configured goal or enter your own custom goal
4. Click "Generate Demo" to run the 5-agent pipeline
5. View the top candidates and their scores

## API Endpoints

- `GET /` - Landing page
- `GET /demo` - Interactive demo page
- `GET /signin` - Sign-in page
- `POST /api/demo-request` - Handle demo requests
- `POST /api/run-demo` - Execute the UDiscovery pipeline with a custom goal
- `POST /api/waitlist` - Handle waitlist signups
- `POST /api/signin` - Handle user authentication

## Technologies Used

### Frontend
- **HTML5, CSS3, Vanilla JavaScript**
- **Node.js, Express.js**
- Custom CSS with modern design patterns
- Inter font family for professional typography

### Backend
- **Python 3.12** with virtual environment
- **CrewAI** for multi-agent orchestration
- **Google Gemini (gemini-2.0-flash)** LLM
- **Kaggle API** for dataset discovery
- **Pandas** for data manipulation

## Design Features

- **Gradient Backgrounds**: Modern purple-blue gradients
- **Smooth Animations**: CSS animations and transitions
- **Responsive Grid**: CSS Grid and Flexbox layouts
- **Interactive Modals**: Form submissions with loading states
- **Professional Typography**: Clean, readable font hierarchy

## Future Enhancements

- Database integration for form submissions
- Email notifications via Nodemailer
- User authentication system
- Dashboard integration
- Analytics tracking

## Development

For development with auto-restart:
```bash
npm run dev
```

## License

MIT License - See LICENSE file for details
