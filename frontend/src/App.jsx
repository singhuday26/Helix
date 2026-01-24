import React from "react";
import { BrowserRouter as Router } from "react-router-dom";
import Hero from "./components/Hero";
import Education from "./components/Education";
import LiveDemo from "./components/LiveDemo";
import Footer from "./components/Footer";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-dark-950">
        <Hero />
        <Education />
        <LiveDemo />
        <Footer />
      </div>
    </Router>
  );
}

export default App;
