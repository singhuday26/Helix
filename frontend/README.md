# Helix Frontend

Professional React UI for the Helix Speculative Decoding Inference Engine.

## Features

- ✨ **Real-Time Streaming**: Server-Sent Events (SSE) for live token generation
- 📚 **Educational Content**: Interactive 5-level explanation of speculative decoding
- 🎨 **Professional Design**: Minimalist, modern UI with Tailwind CSS
- ⚡ **Performance Metrics**: Live visualization of tokens/sec, acceptance rate, and latency
- 📱 **Responsive**: Works on desktop, tablet, and mobile

## Tech Stack

- **React 18**: Modern UI framework
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Framer Motion**: Smooth animations
- **React Router**: Navigation

## Quick Start

### Prerequisites

- Node.js 18+ and npm/yarn
- Helix backend running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── Hero.jsx           # Hero section with stats
│   │   ├── Education.jsx      # 5-level educational content
│   │   ├── LiveDemo.jsx       # SSE streaming demo
│   │   └── Footer.jsx         # Footer with links
│   ├── App.jsx                # Main app component
│   ├── main.jsx               # Entry point
│   └── index.css              # Tailwind styles
├── index.html
├── package.json
├── vite.config.js             # Vite config with proxy
└── tailwind.config.js         # Tailwind theme config
```

## Features Breakdown

### Hero Section

- Project branding and stats
- Animated gradient text
- Call-to-action buttons
- Performance metrics (3-5x speedup, 30-50% memory saved)

### Education Section

Interactive cards explaining the 5 levels:

1. **🟢 Level 1: The Basics** - Autoregressive generation
2. **🟡 Level 2: The Bottleneck** - Memory bandwidth bound
3. **🟠 Level 3: The Solution** - Speculative decoding
4. **🔴 Level 4: The Optimization** - KV Cache
5. **🟣 Level 5: The Boss Move** - PagedAttention

Each level has:

- Analogy for easy understanding
- Code examples
- Key insights
- Technical jargon translation

### Live Demo Section

- **Prompt input** with example prompts
- **Real-time streaming output** via SSE
- **Performance metrics**:
  - Tokens generated
  - Time elapsed
  - Tokens per second
  - Acceptance rate (% of draft tokens accepted)
- **Error handling** with user-friendly messages

### SSE Implementation

```javascript
// Connect to streaming endpoint
const response = await fetch('/generate/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ prompt, max_tokens: 100, ... }),
})

// Read SSE stream
const reader = response.body.getReader()
const decoder = new TextDecoder()

while (true) {
  const { done, value } = await reader.read()
  if (done) break

  // Parse SSE events (data: {...})
  const lines = decoder.decode(value).split('\n')
  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const event = JSON.parse(line.slice(6))
      // Update UI with token
      setOutput(prev => prev + event.token)
    }
  }
}
```

## Design Philosophy

### Minimalist & Professional

- Dark theme with subtle gradients
- Clear hierarchy and spacing
- Smooth animations (Framer Motion)
- Accessible color contrast

### Educational Focus

- Jargon-free explanations
- Progressive complexity (5 levels)
- Visual analogies (chef metaphor)
- Cheat sheet for quick reference

### Performance-First

- Vite for instant dev server
- Code splitting
- Optimized bundles
- Lazy loading

## API Integration

The frontend connects to these backend endpoints:

- `POST /generate/stream` - SSE streaming generation
- `POST /generate` - Standard generation (fallback)
- `GET /health` - Health check
- `GET /metrics` - Engine metrics

Vite proxy configuration handles CORS:

```javascript
// vite.config.js
server: {
  proxy: {
    '/generate': 'http://localhost:8000',
    '/health': 'http://localhost:8000',
    '/metrics': 'http://localhost:8000',
  },
}
```

## Customization

### Colors

Edit `tailwind.config.js` to change the color scheme:

```javascript
theme: {
  extend: {
    colors: {
      primary: { ... },  // Main accent color
      dark: { ... },     // Background shades
    },
  },
}
```

### Content

Edit the `levels` array in `Education.jsx` to modify educational content.

### Animations

Adjust Framer Motion props in components:

```jsx
<motion.div
  initial={{ opacity: 0, y: 30 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.8 }}
>
```

## Troubleshooting

### CORS Issues

Make sure the backend has CORS enabled:

```python
# src/api.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### SSE Not Working

- Check backend is running on port 8000
- Verify `/generate/stream` endpoint exists
- Check browser console for errors
- Try standard `/generate` endpoint first

### Build Errors

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

## Contributing

1. Follow React best practices
2. Use functional components and hooks
3. Keep components small and focused
4. Use Tailwind utility classes
5. Add PropTypes for type safety
6. Write descriptive commit messages

## License

Part of the Helix project. See main repository for license details.
