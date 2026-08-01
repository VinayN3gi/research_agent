"use client";

import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";

type Source = {
  title: string;
  url: string;
};

type ResearchResponse = {
  report: string;
  sources: Source[];
};

export default function Home() {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("Idle");
  const [report, setReport] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Fake statuses array to cycle through while loading
  const fakeStatuses = [
    "Planning...",
    "Searching...",
    "Reading...",
    "Writing..."
  ];

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isLoading) {
      let index = 0;
      setStatus(fakeStatuses[0]);
      interval = setInterval(() => {
        index = (index + 1) % fakeStatuses.length;
        setStatus(fakeStatuses[index]);
      }, 5000); // cycle every 5 seconds
    } else if (!isLoading && report) {
      setStatus("Completed");
    } else {
      setStatus("Idle");
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isLoading, report]);

  const handleResearch = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    setReport("");
    setSources([]);

    try {
      const res = await fetch("http://localhost:8000/api/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const data: ResearchResponse = await res.json();
      setReport(data.report);
      setSources(data.sources || []);
    } catch (error: any) {
      console.error(error);
      setReport(`**Error:** ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100 p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="border-b border-neutral-800 pb-4">
          <h1 className="text-3xl font-bold tracking-tight text-white">Deep Research Agent</h1>
          <p className="text-neutral-400 mt-2">Phase 1 Minimal Pipeline</p>
        </header>

        {/* Input Section */}
        <section className="bg-neutral-900 border border-neutral-800 p-6 rounded-xl space-y-4">
          <label className="block text-sm font-medium text-neutral-300">
            Research Topic
          </label>
          <div className="flex gap-4">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., Latest AI IDEs"
              disabled={isLoading}
              className="flex-1 bg-neutral-950 border border-neutral-700 text-white px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleResearch}
              disabled={isLoading || !query.trim()}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium px-6 py-2 rounded-lg transition-colors"
            >
              {isLoading ? "Working..." : "Research"}
            </button>
          </div>
        </section>

        {/* Status Section */}
        <section className="bg-neutral-900 border border-neutral-800 p-6 rounded-xl flex items-center justify-between">
          <span className="text-sm font-medium text-neutral-400">Status</span>
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
            status === 'Idle' ? 'bg-neutral-800 text-neutral-300' :
            status === 'Completed' ? 'bg-green-900/50 text-green-400' :
            'bg-blue-900/50 text-blue-400 animate-pulse'
          }`}>
            {status}
          </span>
        </section>

        {/* Output Section */}
        <section className="bg-neutral-900 border border-neutral-800 p-6 rounded-xl space-y-4">
          <h2 className="text-lg font-medium text-neutral-300 border-b border-neutral-800 pb-2">Output</h2>
          <div className="prose prose-invert max-w-none text-neutral-200 min-h-25">
            {report ? (
              <ReactMarkdown>{report}</ReactMarkdown>
            ) : (
              <p className="text-neutral-500 italic text-sm">(empty)</p>
            )}
          </div>
        </section>

        {/* Sources Section */}
        {sources.length > 0 && (
          <section className="bg-neutral-900 border border-neutral-800 p-6 rounded-xl space-y-4">
            <h2 className="text-lg font-medium text-neutral-300 border-b border-neutral-800 pb-2">Sources Used</h2>
            <ul className="space-y-2">
              {sources.map((src, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-neutral-400">
                  <span className="text-green-500 mt-0.5">✓</span>
                  <div>
                    <a href={src.url} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline font-medium">
                      {src.title || src.url}
                    </a>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </main>
  );
}
