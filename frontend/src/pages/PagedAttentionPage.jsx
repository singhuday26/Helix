import React from "react";
import Navbar from "../components/Navbar";
import PagedAttention from "../components/PagedAttention";
import Footer from "../components/Footer";

const PagedAttentionPage = () => {
  return (
    <div className="min-h-screen bg-void-950 relative overflow-hidden">
      {/* Global DNA Helix Background Decoration */}
      <div className="helix-bg-decoration" aria-hidden="true" />
      <Navbar />
      <main className="pt-16">
        <PagedAttention />
      </main>
      <Footer />
    </div>
  );
};

export default PagedAttentionPage;
