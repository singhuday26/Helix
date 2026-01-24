import React, { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";
import LoadingScreen from "./components/LoadingScreen";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import Features from "./components/Features";
import Technology from "./components/Technology";
import Playground from "./components/Playground";
import Footer from "./components/Footer";
import ComparisonPage from "./pages/ComparisonPage";

// Landing Page Component
const LandingPage = () => (
  <div className="min-h-screen bg-void-950 relative overflow-hidden">
    {/* Global DNA Helix Background Decoration */}
    <div className="helix-bg-decoration" aria-hidden="true" />
    <Navbar />
    <Hero />
    <Features />
    <Technology />
    <Playground />
    <Footer />
  </div>
);

function App() {
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if this is the first visit
    const hasVisited = sessionStorage.getItem("hasVisited");
    if (hasVisited) {
      setIsLoading(false);
    }
  }, []);

  const handleLoadComplete = () => {
    sessionStorage.setItem("hasVisited", "true");
    setIsLoading(false);
  };

  return (
    <ErrorBoundary>
      {isLoading && <LoadingScreen onLoadComplete={handleLoadComplete} />}
      <Router>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/comparison" element={<ComparisonPage />} />
        </Routes>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
