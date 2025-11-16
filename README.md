# UDiscovery - AI-Powered Student Pipeline Optimization

A complete platform for universities to autonomously discover and evaluate prospective graduate students using AI agents and Kaggle datasets.

## AI Agents Pipeline

The UDiscovery platform uses a 5-agent CrewAI pipeline that works sequentially to discover and evaluate candidates:

1. **University Strategy Analyst** (Trait Inferrer)
   - Analyzes university program goals and requirements
   - Creates a detailed candidate blueprint with ideal traits
   - Generates Kaggle search keywords for data sourcing

2. **Data Sourcing Specialist** (Kaggle Scout)
   - Searches Kaggle datasets using the generated keywords
   - Identifies relevant datasets containing candidate profiles
   - Returns a list of potential data sources

3. **Dataset Quality Analyst** (Dataset Evaluator)
   - Evaluates the discovered datasets
   - Selects the single best dataset for candidate analysis
   - Ensures data quality and relevance

4. **Data Engineer** (Data Ingestion)
   - Prepares the selected dataset for analysis
   - Handles data formatting and structure
   - Ensures data is ready for candidate evaluation

5. **Admissions Propensity Modeler** (Ranking Agent)
   - Scores candidates against the ideal profile blueprint
   - Ranks the top 10 most promising candidates
   - Provides detailed justifications for each candidate's score and match

The pipeline executes sequentially, with each agent building on the previous agent's output to produce a final ranked list of candidates with scores, backgrounds, and matching explanations.

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
├── backend/                      # AI agentic pipeline
│   ├── agents_pipeline.py        # Working 5-agent pipeline
│   ├── demo_runner.py          # Demo runner for web interface
│   ├── run_demo_cli.py          # CLI interface
│   ├── .env                      # Environment variables (API keys)
│   └── requirements.txt         # Python dependencies
└── README.md                     # This file
```

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
   cd backend
   python3.12 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Environment Variables**:
   Create a `.env` file in `backend/`:
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
