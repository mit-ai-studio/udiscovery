# UDiscovery - AI-Powered Student Pipeline Optimization

A complete platform for universities to autonomously discover and evaluate prospective graduate students using AI agents and Kaggle datasets.

## AI Agents Pipeline

The UDiscovery platform uses a multi-agent CrewAI pipeline that works sequentially to discover and evaluate candidates. The platform supports two pipeline configurations:

### Kaggle Pipeline (5 Agents)

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
   - Downloads and prepares the selected dataset for analysis
   - Handles data formatting and structure
   - Ensures data is ready for candidate evaluation

5. **Graduate Program Application Probability Modeler** (Prospection Agent)
   - Estimates the probability that each candidate will apply to the graduate program
   - Uses logistic regression and probabilistic modeling
   - Provides structured output including:
     - Predicted application probability (0.0-1.0)
     - Propensity segment (high/medium/low)
     - Key positive drivers (factors increasing application likelihood)
     - Key negative drivers (factors decreasing application likelihood)
     - Assumptions and warnings about predictions
   - Ranks the top 10 most promising candidates with detailed justifications

### Synthetic Dataset Pipeline (3 Agents)

For faster testing and development, UDiscovery also supports a streamlined pipeline using a local synthetic dataset:

1. **University Strategy Analyst** (Trait Inferrer)
   - Same as Kaggle pipeline - analyzes goals and creates candidate blueprint

2. **Data Loader Agent**
   - Loads and prepares the synthetic candidate dataset (`dataset/synt_prospect_5k.csv`)
   - Provides candidate profiles with fields including: experience, education, GPA, demographics, and more

3. **Graduate Program Application Probability Modeler** (Prospection Agent)
   - Same probability modeling as Kaggle pipeline
   - Works with synthetic data structure to predict application probabilities

The pipeline executes sequentially, with each agent building on the previous agent's output to produce a final ranked list of candidates with application probabilities, backgrounds, and detailed matching explanations.

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
│   ├── agents_pipeline.py        # Kaggle pipeline orchestrator
│   ├── synthetic_agents_pipeline.py  # Synthetic dataset pipeline orchestrator
│   ├── trait_inferrer.py         # Trait inferrer agent module
│   ├── kaggle_pipeline.py        # Kaggle-related agents and tasks
│   ├── synthetic_pipeline.py      # Synthetic dataset loading module
│   ├── propensity_modeler.py     # Prospection agent (probability modeler) module
│   ├── demo_runner.py            # Demo runner for web interface
│   ├── run_demo_cli.py           # CLI interface
│   ├── .env                      # Environment variables (API keys)
│   └── requirements.txt          # Python dependencies
├── dataset/                      # Data files
│   └── synt_prospect_5k.csv      # Synthetic candidate dataset (5000 candidates)
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
4. Click "Generate Demo" to run the pipeline (currently uses synthetic dataset pipeline)
5. View the top candidates with:
   - Application probability scores (0-100%)
   - Propensity segments (high/medium/low)
   - Detailed backgrounds
   - Key positive and negative drivers
   - Assumptions and warnings

**Note**: The demo currently uses the synthetic dataset pipeline for faster execution. To use the Kaggle pipeline, modify `demo_runner.py` to import from `agents_pipeline` instead of `synthetic_agents_pipeline`.

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
- **Kaggle API** for dataset discovery (Kaggle pipeline)
- **Pandas** for data manipulation
- **Logistic Regression/Probabilistic Modeling** for application probability prediction
- **Synthetic Dataset Support** for faster testing and development

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
