import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import ErrorBoundary from "./components/ErrorBoundary";
import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import Features from "./components/Features";
import Technology from "./components/Technology";
import Playground from "./components/Playground";
import Footer from "./components/Footer";
import ComparisonPage from "./pages/ComparisonPage";

// Landing Page Component
const LandingPage = () => (
  <div className="min-h-screen bg-void-950">
    <Navbar />
    <Hero />
    <Features />
    <Technology />
    <Playground />
    <Footer />
  </div>
);

function App() {
  return (
    <ErrorBoundary>
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
