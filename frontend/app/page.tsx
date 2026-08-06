"use client";

import { useState, useEffect } from "react";
import ReactMarkdown from "react-markdown";

type Source = {
  title: string;
  url: string;
};

export default function Home() {
  const [query, setQuery] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  
  // Real-time Status state
  const [stage, setStage] = useState<string>("Idle");
  const [statusMessage, setStatusMessage] = useState<string>("");
  const [iteration, setIteration] = useState<number>(0);
  const [currentProgress, setCurrentProgress] = useState<number>(0);
  const [totalProgress, setTotalProgress] = useState<number>(0);
  
  // Results
  const [report, setReport] = useState("");
  const [sources, setSources] = useState<Source[]>([]);
  const [reflectionThoughts, setReflectionThoughts] = useState<any[]>([]);
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    if (!jobId) return;

    const eventSource = new EventSource(`http://localhost:8000/api/research/${jobId}/events`);

    eventSource.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        const { type, data } = parsed;

        if (type === "status") {
          setStage(data.stage);
          setStatusMessage(data.message);
          
          // Generate a log entry similar to backend logging using local time
          const now = new Date();
          const time = now.getHours().toString().padStart(2, '0') + ':' +
                       now.getMinutes().toString().padStart(2, '0') + ':' +
                       now.getSeconds().toString().padStart(2, '0') + '.' +
                       now.getMilliseconds().toString().padStart(3, '0');
          const logEntry = `${time} - [INFO] - ${data.stage || 'system'} - ${data.message}`;
          setLogs(prev => [...prev, logEntry]);

          if (data.iteration) setIteration(data.iteration);
          if (data.current !== undefined) setCurrentProgress(data.current);
          if (data.total !== undefined) setTotalProgress(data.total);
        } else if (type === "plan") {
          // Do something with plan if needed
        } else if (type === "reflection") {
          setReflectionThoughts(prev => [...prev, data]);
        } else if (type === "complete") {
          setReport(data.report);
          setSources(data.sources || []);
          setStage("Completed");
          setStatusMessage("Report generated successfully.");
          setIsLoading(false);
          eventSource.close();
        } else if (type === "error") {
          setReport(`**Error:** ${data.message}`);
          setStage("Error");
          setIsLoading(false);
          eventSource.close();
        }
      } catch (err) {
        console.error("Failed to parse SSE event", err);
      }
    };

    eventSource.onerror = () => {
      console.error("SSE connection lost");
      eventSource.close();
      setIsLoading(false);
    };

    return () => {
      eventSource.close();
    };
  }, [jobId]);

  const handleResearch = async () => {
    if (!query.trim()) return;

    setIsLoading(true);
    setReport("");
    setSources([]);
    setReflectionThoughts([]);
    setLogs([]);
    setStage("Starting...");
    setStatusMessage("Initializing job...");

    try {
      const res = await fetch("http://localhost:8000/api/research", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status}`);
      }

      const data = await res.json();
      setJobId(data.job_id);
    } catch (error: any) {
      console.error(error);
      setReport(`**Error starting job:** ${error.message}`);
      setStage("Error");
      setIsLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100 p-8 font-sans">
      <div className="max-w-4xl mx-auto space-y-8">
        <header className="border-b border-neutral-800 pb-4">
          <h1 className="text-3xl font-bold tracking-tight text-white">Deep Research Agent</h1>
          <p className="text-neutral-400 mt-2">Phase 2: Intelligent Reflection Loop</p>
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
              placeholder="e.g., Cursor vs Windsurf capabilities"
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

        {/* Real-Time Progress Section */}
        <section className="bg-neutral-900 border border-neutral-800 p-6 rounded-xl space-y-4">
          <div className="flex items-center justify-between border-b border-neutral-800 pb-4">
            <span className="text-sm font-medium text-neutral-400">Research Status</span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              stage === 'Idle' ? 'bg-neutral-800 text-neutral-300' :
              stage === 'Completed' ? 'bg-green-900/50 text-green-400' :
              stage === 'Error' ? 'bg-red-900/50 text-red-400' :
              'bg-blue-900/50 text-blue-400 animate-pulse'
            }`}>
              {stage.toUpperCase()} {iteration > 0 && stage !== 'Completed' && `(Round ${iteration})`}
            </span>
          </div>

          <div className="text-neutral-300 font-mono text-sm py-2 mb-2">
            {statusMessage || "Awaiting task..."}
            {totalProgress > 0 && stage !== 'Completed' && (
              <span className="ml-2 text-blue-400">
                [{currentProgress} / {totalProgress}]
              </span>
            )}
          </div>
          
          {/* Terminal Console Logs */}
          <div className="bg-[#0c0c0c] border border-neutral-800 rounded-lg p-4 h-64 overflow-y-auto font-mono text-xs text-green-400/90 flex flex-col-reverse">
            <div className="whitespace-pre-wrap">
              {logs.length > 0 ? logs.join("\n") : "System initialized. Standing by..."}
            </div>
          </div>
          
          {/* Reflection Thoughts Log */}
          {reflectionThoughts.length > 0 && (
            <div className="mt-4 pt-4 border-t border-neutral-800">
              <h4 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">Agent Thoughts</h4>
              <div className="space-y-2">
                {reflectionThoughts.map((thought, idx) => (
                  <div key={idx} className="text-sm bg-neutral-950 p-3 rounded border border-neutral-800">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={thought.enough_information ? "text-green-400" : "text-amber-400"}>
                        {thought.enough_information ? "✓ Sufficient info gathered" : "⚠️ Need more info"}
                      </span>
                    </div>
                    {!thought.enough_information && thought.missing_topics && (
                      <div className="text-neutral-400 mt-1">
                        <span className="text-neutral-500">Missing: </span>
                        {thought.missing_topics.join(", ")}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </section>

        {/* Output Section */}
        <section className="bg-neutral-900 border border-neutral-800 p-6 rounded-xl space-y-4">
          <h2 className="text-lg font-medium text-neutral-300 border-b border-neutral-800 pb-2">Final Report</h2>
          <div className="prose prose-invert max-w-none text-neutral-200 min-h-25">
            {report ? (
              <ReactMarkdown>{report}</ReactMarkdown>
            ) : (
              <p className="text-neutral-500 italic text-sm">Report will appear here when complete...</p>
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
