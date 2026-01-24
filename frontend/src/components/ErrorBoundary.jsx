import React from "react";

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    this.setState({
      error: error,
      errorInfo: errorInfo,
    });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-void-950 flex items-center justify-center px-4">
          <div className="max-w-2xl w-full">
            <div className="p-8 rounded-2xl bg-white/[0.02] border border-helix-reject/30">
              <div className="flex items-center gap-4 mb-6">
                <div className="flex-shrink-0 w-16 h-16 bg-helix-reject/20 rounded-full flex items-center justify-center">
                  <svg
                    className="w-8 h-8 text-helix-reject"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                </div>
                <div>
                  <h1 className="text-3xl font-bold text-white mb-2">
                    Something went wrong
                  </h1>
                  <p className="text-gray-400">
                    The application encountered an unexpected error.
                  </p>
                </div>
              </div>

              <div className="mb-6">
                <div className="bg-void-950 rounded-lg p-4 border border-helix-reject/20">
                  <div className="text-sm font-mono text-helix-reject mb-2">
                    {this.state.error && this.state.error.toString()}
                  </div>
                  {this.state.errorInfo && (
                    <details className="mt-3">
                      <summary className="text-xs text-gray-500 cursor-pointer hover:text-gray-400">
                        Show error details
                      </summary>
                      <pre className="mt-3 text-xs text-gray-600 overflow-x-auto">
                        {this.state.errorInfo.componentStack}
                      </pre>
                    </details>
                  )}
                </div>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={() => window.location.reload()}
                  className="px-6 py-3 bg-white text-void-950 font-medium rounded-lg hover:bg-gray-100 transition-colors flex items-center gap-2"
                >
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                    />
                  </svg>
                  Reload Page
                </button>
                <button
                  onClick={() =>
                    this.setState({
                      hasError: false,
                      error: null,
                      errorInfo: null,
                    })
                  }
                  className="px-6 py-3 text-white font-medium rounded-lg border border-white/20 hover:bg-white/5 transition-colors"
                >
                  Try Again
                </button>
              </div>

              <div className="mt-6 pt-6 border-t border-dark-800">
                <p className="text-sm text-dark-500">
                  If this problem persists, please check:
                </p>
                <ul className="mt-2 space-y-1 text-sm text-dark-500">
                  <li>• Backend server is running on http://localhost:8000</li>
                  <li>• Network connection is stable</li>
                  <li>• Browser console for additional errors</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
