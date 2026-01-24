import React from "react";

const Footer = () => {
  return (
    <footer className="bg-dark-950 border-t border-dark-800 py-12">
      <div className="section-container">
        <div className="grid md:grid-cols-3 gap-8 mb-8">
          <div>
            <h3 className="text-xl font-bold gradient-text mb-4">Helix</h3>
            <p className="text-dark-400 text-sm">
              Speculative Decoding Inference Engine for fast LLM inference on
              edge devices.
            </p>
          </div>

          <div>
            <h4 className="font-semibold text-dark-300 mb-4">Technology</h4>
            <ul className="space-y-2 text-sm text-dark-400">
              <li>• Speculative Decoding</li>
              <li>• PagedAttention</li>
              <li>• DirectML (AMD GPU)</li>
              <li>• FastAPI + React</li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold text-dark-300 mb-4">Resources</h4>
            <ul className="space-y-2 text-sm">
              <a
                href="/docs"
                className="block text-primary-400 hover:text-primary-300 transition-colors"
              >
                API Documentation
              </a>
              <a
                href="https://github.com"
                className="block text-primary-400 hover:text-primary-300 transition-colors"
              >
                GitHub Repository
              </a>
              <a
                href="#education"
                className="block text-primary-400 hover:text-primary-300 transition-colors"
              >
                Learn How It Works
              </a>
            </ul>
          </div>
        </div>

        <div className="pt-8 border-t border-dark-800 text-center text-dark-500 text-sm">
          <p>
            Built with ❤️ for the AI community. Powered by PyTorch, DirectML,
            and TinyLlama.
          </p>
          <p className="mt-2">
            © 2026 Helix Project. From "AI Beginner" to "Systems Architect" in
            24 hours.
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
