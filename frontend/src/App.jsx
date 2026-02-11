import React, { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";
import LoadingScreen from "./components/LoadingScreen";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import Features from "./components/Features";
import Footer from "./components/Footer";
import ComparisonPage from "./pages/ComparisonPage";
import TechnologyPage from "./pages/TechnologyPage";
import PlaygroundPage from "./pages/PlaygroundPage";
import PagedAttentionPage from "./pages/PagedAttentionPage";

// Redirect component for external URLs - opens in new tab and navigates back
const ExternalRedirect = ({ to }) => {
  useEffect(() => {
    window.open(to, "_blank", "noopener,noreferrer");
    window.history.back();
  }, [to]);
  return (
    <div className="min-h-screen bg-void-950 flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-helix-500 mx-auto mb-4"></div>
        <p className="text-gray-400">Opening API Documentation in new tab...</p>
      </div>
    </div>
  );
};

// Landing Page Component
const LandingPage = () => (
  <div className="min-h-screen bg-void-950 relative overflow-hidden">
    {/* Global DNA Helix Background Decoration */}
    <div className="helix-bg-decoration" aria-hidden="true" />
    <Navbar />
    <Hero />
    <Features />
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
          <Route path="/technology" element={<TechnologyPage />} />
          <Route path="/paged-attention" element={<PagedAttentionPage />} />
          <Route path="/playground" element={<PlaygroundPage />} />
          <Route
            path="/docs"
            element={<ExternalRedirect to="http://localhost:8000/docs" />}
          />
          <Route
            path="/redoc"
            element={<ExternalRedirect to="http://localhost:8000/redoc" />}
          />
        </Routes>
      </Router>
    </ErrorBoundary>
  );
}

export default App;
