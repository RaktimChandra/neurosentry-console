import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * Catches render-time errors anywhere in the subtree and shows a friendly
 * fallback instead of a white screen. Logs the stack to the browser console
 * so devs can still see it.
 */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // eslint-disable-next-line no-console
    console.error("[ErrorBoundary] caught", error, info);
  }

  handleReset = () => this.setState({ error: null });
  handleReload = () => window.location.reload();

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="h-full flex items-center justify-center p-8">
        <div className="panel max-w-lg w-full">
          <div className="panel-header">
            <span>Something went wrong</span>
            <span className="led led-red" />
          </div>
          <div className="p-6 space-y-4">
            <p className="text-slate-300 text-sm">
              The dashboard encountered an unexpected error. You can try again or
              reload the page.
            </p>
            <pre className="mono text-xs text-slate-500 p-3 bg-ink-900 border border-ink-700 rounded overflow-x-auto">
              {this.state.error.message}
            </pre>
            <div className="flex gap-2">
              <button
                onClick={this.handleReset}
                className="px-4 py-2 text-sm rounded border border-signal-green/40 text-signal-green hover:bg-signal-green/10"
              >
                Try again
              </button>
              <button
                onClick={this.handleReload}
                className="px-4 py-2 text-sm rounded border border-ink-600 text-slate-300 hover:bg-ink-800"
              >
                Reload page
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }
}
