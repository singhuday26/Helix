import React from "react";
import Navbar from "../components/Navbar";
import Technology from "../components/Technology";
import Footer from "../components/Footer";

const TechnologyPage = () => {
  return (
    <div className="min-h-screen bg-void-950 relative overflow-hidden">
      {/* Global DNA Helix Background Decoration */}
      <div className="helix-bg-decoration" aria-hidden="true" />
      <Navbar />
      <main className="pt-16">
        <Technology />
      </main>
      <Footer />
    </div>
  );
};

export default TechnologyPage;
