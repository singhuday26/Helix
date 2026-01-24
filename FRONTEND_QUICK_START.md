# Frontend Quick Start Guide

## 🚀 Run the Frontend

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Open http://localhost:3000 in browser
```

## 📁 Key Files to Know

| File                                | Purpose               | Edit When...              |
| ----------------------------------- | --------------------- | ------------------------- |
| `src/App.jsx`                       | Main layout & routing | Adding/removing sections  |
| `src/components/LiveDemo.jsx`       | Interactive demo      | Changing demo behavior    |
| `src/components/SettingsPanel.jsx`  | Parameter controls    | Adding new settings       |
| `src/components/ComparisonMode.jsx` | Benchmark comparison  | Changing comparison logic |
| `src/components/BatchDemo.jsx`      | Batch processing      | Modifying batch UI        |
| `src/components/PerformanceViz.jsx` | Charts & metrics      | Updating visualizations   |
| `src/index.css`                     | Global styles         | Theming changes           |
| `tailwind.config.js`                | Design tokens         | Color/spacing updates     |
| `vite.config.js`                    | Build config          | Proxy/build settings      |

## 🎨 Component Usage Examples

### PerformanceChart

```jsx
import { PerformanceChart } from "./components/PerformanceViz";

const [chartData, setChartData] = useState([]);

// Update during streaming
setChartData((prev) => [...prev, { time: 1.5, value: 42.3 }]);

// Render
<PerformanceChart data={chartData} width={600} height={200} />;
```

### MetricCard

```jsx
import { MetricCard } from "./components/PerformanceViz";

<MetricCard
  label="Tokens/sec"
  value={42.5}
  unit="/s"
  trend={0.25} // 25% improvement
  color="primary"
/>;
```

### SettingsPanel

```jsx
import SettingsPanel from "./components/SettingsPanel";

const [config, setConfig] = useState({
  max_tokens: 50,
  temperature: 0.7,
  speculation_depth: 4,
  use_speculative: true,
});

<SettingsPanel config={config} onChange={setConfig} disabled={isGenerating} />;
```

## 🎯 Common Tasks

### Add a New Section

1. Create component in `src/components/`
2. Import in `src/App.jsx`
3. Add to render in correct order
4. Update navigation links if needed

### Change Colors

1. Edit `tailwind.config.js` - `theme.extend.colors`
2. Use new color: `className="text-yourcolor-400"`
3. Or update CSS variables in `src/index.css`

### Add API Endpoint

1. Update `vite.config.js` proxy if needed
2. Use fetch in component: `fetch('/your-endpoint')`
3. Handle response with try/catch
4. Update UI based on response

### Modify Settings

1. Edit `SettingsPanel.jsx`
2. Add to `settings` array with config
3. Update help text
4. Use in API calls

## 🐛 Troubleshooting

### "Backend not reachable"

```bash
# Check backend is running
cd .. && python run.py
# Backend should be at http://localhost:8000
```

### "Module not found"

```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

### "Port 3000 already in use"

```bash
# Kill process or use different port
npm run dev -- --port 3001
```

### "Chart not rendering"

- Check browser console for errors
- Verify data format: `[{time: number, value: number}]`
- Ensure canvas is visible in DOM

### "Settings not updating"

- Check `onChange` is called
- Verify state is updated in parent
- Check for disabled prop blocking changes

## 📊 Performance Tips

### Optimize Chart Rendering

```jsx
// Limit data points
const chartData = allData.slice(-100); // Last 100 points only
```

### Debounce Settings Changes

```jsx
import { useDebounce } from "use-debounce";

const [debouncedConfig] = useDebounce(config, 300);
// Use debouncedConfig for API calls
```

### Lazy Load Components

```jsx
import { lazy, Suspense } from "react";

const BatchDemo = lazy(() => import("./components/BatchDemo"));

<Suspense fallback={<div>Loading...</div>}>
  <BatchDemo />
</Suspense>;
```

## 🎨 Styling Quick Reference

### Tailwind Classes

```jsx
// Layout
className = "flex items-center justify-between gap-4";
className = "grid grid-cols-2 md:grid-cols-4 gap-6";

// Colors
className = "bg-dark-900 text-primary-400 border-dark-700";

// Spacing
className = "p-6 m-4 space-y-3";

// Typography
className = "text-2xl font-bold tracking-wide";

// Animations
className = "transition-all duration-300 hover:scale-105";
```

### Framer Motion

```jsx
<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  transition={{ duration: 0.5 }}
>
  Content
</motion.div>
```

## 🔧 Build & Deploy

### Build for Production

```bash
npm run build
# Output: dist/
```

### Preview Production Build

```bash
npm run preview
# Test production build locally
```

### Deploy (Example: Vercel)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Environment variables
# Set VITE_API_URL in Vercel dashboard
```

## 📝 Code Conventions

### File Naming

- Components: PascalCase (`LiveDemo.jsx`)
- Utils: camelCase (`apiClient.js`)
- Styles: kebab-case (`custom-styles.css`)

### Component Structure

```jsx
import React, { useState } from "react";
import { motion } from "framer-motion";

const MyComponent = ({ prop1, prop2 }) => {
  // 1. State
  const [state, setState] = useState(null);

  // 2. Effects
  useEffect(() => {
    // ...
  }, []);

  // 3. Handlers
  const handleClick = () => {
    // ...
  };

  // 4. Render helpers
  const renderContent = () => {
    // ...
  };

  // 5. Main render
  return <div>{/* ... */}</div>;
};

export default MyComponent;
```

### State Management

```jsx
// Simple local state
const [value, setValue] = useState(initial);

// Complex state
const [state, setState] = useState({
  field1: value1,
  field2: value2,
});

// Update complex state
setState((prev) => ({ ...prev, field1: newValue }));
```

## 🎓 Learning Resources

### React

- [React Docs](https://react.dev)
- [Hooks Reference](https://react.dev/reference/react)

### Tailwind CSS

- [Tailwind Docs](https://tailwindcss.com/docs)
- [Tailwind Cheatsheet](https://nerdcave.com/tailwind-cheat-sheet)

### Framer Motion

- [Framer Motion Docs](https://www.framer.com/motion/)
- [Animation Examples](https://www.framer.com/motion/examples/)

### Vite

- [Vite Docs](https://vitejs.dev)
- [Vite Config](https://vitejs.dev/config/)

## ✅ Pre-Commit Checklist

- [ ] Code runs without errors
- [ ] No console warnings
- [ ] Responsive on mobile/tablet/desktop
- [ ] Animations are smooth
- [ ] API calls have error handling
- [ ] Loading states implemented
- [ ] Accessibility considered
- [ ] Comments for complex logic
- [ ] No hardcoded values (use config)

## 🎉 You're Ready!

The frontend is fully functional and ready for:

- ✅ Local development
- ✅ Demo presentations
- ✅ Production deployment
- ✅ Further enhancements

**Happy coding! 🚀**
