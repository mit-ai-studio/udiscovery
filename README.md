# UDiscovery - AI-Powered Student Pipeline Optimization

A complete platform for universities to autonomously discover and evaluate prospective graduate students using AI agents and Kaggle datasets.

## Features

- **Modern, Responsive Design**: Clean, professional interface that works on all devices
- **Interactive Elements**: Smooth scrolling, animated visualizations, and modal forms
- **Form Handling**: Demo requests, waitlist signups, and sign-in functionality
- **Professional Copy**: Targeted messaging for university enrollment professionals
- **Node.js Backend**: Easy integration with future backend services

## Project Structure

```
udiscovery/
├── frontend/             # Landing page and web interface
│   ├── package.json      # Node.js dependencies
│   ├── server.js         # Express server
│   └── public/           # Static files
│       ├── index.html    # Main landing page
│       ├── signin.html   # Sign-in page
│       ├── css/styles.css
│       └── js/main.js
├── backend/              # AI agentic pipeline
│   ├── tools.py          # Kaggle integration tools
│   ├── agents.py         # 5 specialized AI agents
│   ├── tasks.py          # Sequential workflow tasks
│   ├── main.py           # Pipeline orchestration
│   ├── requirements.txt  # Python dependencies
│   └── README.md         # Backend documentation
└── README.md             # This file
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

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Start the Server**:
   ```bash
   npm start
   ```

3. **View the Site**:
   Open your browser to `http://localhost:3000`

## API Endpoints

- `POST /api/demo-request` - Handle demo requests
- `POST /api/waitlist` - Handle waitlist signups
- `POST /api/signin` - Handle user authentication

## Technologies Used

- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Backend**: Node.js, Express.js
- **Styling**: Custom CSS with modern design patterns
- **Fonts**: Inter font family for professional typography

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
