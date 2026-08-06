"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import ReactMarkdown from "react-markdown";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell } from 'recharts';

type ResearchRun = {
  id: string;
  query: string;
  status: string;
  created_at: string;
};

type Report = {
  id: string;
  version: number;
  content: string;
  created_at: string;
};

type Project = {
  id: string;
  name: string;
  created_at: string;
  runs: ResearchRun[];
  reports: Report[];
};

export default function ProjectWorkspace() {
  const params = useParams();
  const projectId = params.id as string;
  const [project, setProject] = useState<Project | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Chat state
  const [chatMessage, setChatMessage] = useState("");
  const [chatHistory, setChatHistory] = useState<{role: 'user' | 'agent', text: string}[]>([]);
  const [isChatting, setIsChatting] = useState(false);

  // Evidence state
  const [evidenceData, setEvidenceData] = useState<any>(null);
  const [selectedCitation, setSelectedCitation] = useState<string | null>(null);

  useEffect(() => {
    const fetchProject = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/projects/${projectId}`);
        if (res.ok) {
          const data = await res.json();
          setProject(data);
        }
      } catch (e) {
        console.error("Failed to fetch project", e);
      } finally {
        setIsLoading(false);
      }
    };

    const fetchEvidence = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/projects/${projectId}/evidence`);
        if (res.ok) {
          const data = await res.json();
          setEvidenceData(data);
        }
      } catch (e) {}
    };

    fetchProject();
    fetchEvidence();
  }, [projectId]);

  const handleChat = async () => {
    if (!chatMessage) return;
    const msg = chatMessage;
    setChatMessage("");
    setChatHistory(prev => [...prev, {role: 'user', text: msg}]);
    setIsChatting(true);
    try {
      const res = await fetch(`http://localhost:8000/api/projects/${projectId}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: msg })
      });
      const data = await res.json();
      setChatHistory(prev => [...prev, {role: 'agent', text: data.answer}]);
    } catch(e) {
      setChatHistory(prev => [...prev, {role: 'agent', text: "Failed to fetch response."}]);
    } finally {
      setIsChatting(false);
    }
  };

  const renderers = {
    a: ({node, ...props}: any) => {
      if (props.href && props.children && props.children[0] && String(props.children[0]).match(/^(\[\d+\]|\d+)$/)) {
        return (
          <button 
            className="text-blue-400 bg-blue-900/30 px-1 mx-1 rounded text-xs hover:bg-blue-800/50"
            onClick={(e) => {
              e.preventDefault();
              setSelectedCitation(props.href);
            }}
          >
            {props.children}
          </button>
        );
      }
      return <a {...props} target="_blank" rel="noopener noreferrer" className="text-blue-400 hover:underline" />
    },
    code: ({node, inline, className, children, ...props}: any) => {
      const match = /language-(\w+)/.exec(className || '');
      if (!inline && match && match[1] === 'chart') {
        try {
          const data = JSON.parse(String(children).replace(/\n$/, ''));
          const chart = data.chart;
          const chartData = chart.labels.map((l: string, i: number) => ({ name: l, value: chart.values[i] }));
          const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];
          
          return (
            <div className="h-64 w-full bg-neutral-900 p-4 rounded-lg my-6 border border-neutral-800">
              <h4 className="text-center font-medium mb-4 text-neutral-200">{chart.title}</h4>
              <ResponsiveContainer width="100%" height="80%">
                {chart.type === 'bar' ? (
                  <BarChart data={chartData}>
                    <XAxis dataKey="name" stroke="#888" fontSize={12} />
                    <YAxis stroke="#888" fontSize={12} />
                    <Tooltip contentStyle={{backgroundColor: '#111', border: '1px solid #333', borderRadius: '8px'}} />
                    <Bar dataKey="value" fill="#3b82f6" radius={[4,4,0,0]} />
                  </BarChart>
                ) : chart.type === 'pie' ? (
                  <PieChart>
                    <Pie data={chartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={60} label>
                      {chartData.map((entry: any, index: number) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{backgroundColor: '#111', border: '1px solid #333', borderRadius: '8px'}} />
                  </PieChart>
                ) : (
                  <LineChart data={chartData}>
                    <XAxis dataKey="name" stroke="#888" fontSize={12} />
                    <YAxis stroke="#888" fontSize={12} />
                    <Tooltip contentStyle={{backgroundColor: '#111', border: '1px solid #333', borderRadius: '8px'}} />
                    <Line type="monotone" dataKey="value" stroke="#3b82f6" strokeWidth={2} />
                  </LineChart>
                )}
              </ResponsiveContainer>
            </div>
          );
        } catch(e) {
          return <pre className="bg-red-900/20 text-red-400 p-2 text-xs">Chart parsing error</pre>
        }
      }
      return <code className={className} {...props}>{children}</code>
    }
  };

  if (isLoading) return <div className="p-8 text-neutral-500 flex items-center justify-center min-h-screen">Loading workspace...</div>;
  if (!project) return <div className="p-8 text-red-500">Project not found</div>;

  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100 flex relative overflow-hidden">
      {/* Sidebar: Projects & History */}
      <aside className="w-64 border-r border-neutral-800 p-4 space-y-6 shrink-0 flex flex-col h-screen overflow-y-auto">
        <div>
          <h2 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">Project</h2>
          <div className="font-medium text-white truncate">{project.name}</div>
        </div>

        <div>
          <h2 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">Research Runs</h2>
          <div className="space-y-2">
            {project.runs.map(run => (
              <div key={run.id} className="text-sm border border-neutral-800 bg-neutral-900/50 p-3 rounded-lg">
                <div className="truncate text-blue-400 font-medium" title={run.query}>{run.query}</div>
                <div className="text-xs text-neutral-500 flex justify-between mt-2">
                  <span>{run.status}</span>
                  <span>{new Date(run.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-screen overflow-hidden">
        {/* Research Header */}
        <header className="border-b border-neutral-800 p-4 flex justify-between items-center bg-neutral-900/20">
          <div className="flex gap-4 items-center">
            <div className="text-sm font-medium text-neutral-400">Timeline:</div>
            <div className="flex items-center gap-2 text-xs">
               <span className="px-3 py-1 bg-green-900/30 text-green-400 rounded-full border border-green-900/50">Planning</span>
               <span className="text-neutral-600">→</span>
               <span className="px-3 py-1 bg-blue-900/30 text-blue-400 rounded-full border border-blue-900/50">Search & Extract</span>
               <span className="text-neutral-600">→</span>
               <span className="px-3 py-1 bg-purple-900/30 text-purple-400 rounded-full border border-purple-900/50">Write & Review</span>
            </div>
          </div>
          
          <div className="flex gap-2">
            <span className="text-xs text-neutral-500 mr-2 flex items-center">Export:</span>
            <a href={`http://localhost:8000/api/projects/${projectId}/export?format=markdown`} className="px-3 py-1.5 bg-neutral-800 text-xs font-medium text-neutral-300 rounded hover:bg-neutral-700 transition-colors">MD</a>
            <a href={`http://localhost:8000/api/projects/${projectId}/export?format=html`} className="px-3 py-1.5 bg-neutral-800 text-xs font-medium text-neutral-300 rounded hover:bg-neutral-700 transition-colors">HTML</a>
            <a href={`http://localhost:8000/api/projects/${projectId}/export?format=pdf`} className="px-3 py-1.5 bg-neutral-800 text-xs font-medium text-neutral-300 rounded hover:bg-neutral-700 transition-colors">PDF</a>
          </div>
        </header>

        {/* Workspace Body */}
        <div className="flex-1 p-8 overflow-y-auto flex gap-6">
          <div className="flex-1 max-w-4xl mx-auto">
            {project.reports.length > 0 ? (
              <div className="bg-neutral-900/50 border border-neutral-800 p-10 rounded-2xl shadow-xl">
                <h2 className="text-lg font-medium text-neutral-300 border-b border-neutral-800/50 pb-4 mb-6 flex justify-between items-center">
                  <span>Interactive Report</span>
                  <span className="text-sm text-neutral-500 bg-neutral-800 px-2 py-1 rounded">v{project.reports[0].version}</span>
                </h2>
                <div className="prose prose-invert prose-blue max-w-none text-neutral-300 prose-headings:text-neutral-100 prose-a:text-blue-400">
                  <ReactMarkdown components={renderers}>{project.reports[0].content}</ReactMarkdown>
                </div>
              </div>
            ) : (
               <div className="text-center text-neutral-500 mt-20 flex flex-col items-center">
                 <div className="w-12 h-12 border-4 border-blue-500/30 border-t-blue-500 rounded-full animate-spin mb-4"></div>
                 No report generated yet. Research is currently running...
               </div>
            )}
          </div>
          
          {/* Chat Sidebar */}
          {project.reports.length > 0 && (
            <div className="w-80 shrink-0 border border-neutral-800 bg-neutral-900/30 rounded-2xl flex flex-col h-[calc(100vh-8rem)]">
              <div className="p-4 border-b border-neutral-800">
                <h3 className="font-medium text-neutral-200">Chat with Report</h3>
                <p className="text-xs text-neutral-500 mt-1">Ask questions based on the extracted evidence.</p>
              </div>
              
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {chatHistory.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`text-sm p-3 rounded-lg max-w-[90%] ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-neutral-800 text-neutral-200'}`}>
                      {msg.text}
                    </div>
                  </div>
                ))}
                {isChatting && (
                  <div className="flex justify-start">
                    <div className="text-sm p-3 rounded-lg bg-neutral-800 text-neutral-400 animate-pulse">Thinking...</div>
                  </div>
                )}
              </div>
              
              <div className="p-4 border-t border-neutral-800">
                <input 
                  type="text" 
                  value={chatMessage}
                  onChange={e => setChatMessage(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleChat()}
                  placeholder="Ask a question..."
                  className="w-full bg-neutral-950 border border-neutral-800 rounded-lg px-4 py-2 text-sm text-neutral-200 focus:outline-none focus:border-blue-500"
                />
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Evidence Slide-over Modal */}
      {selectedCitation && (
        <div className="absolute inset-0 bg-black/50 backdrop-blur-sm z-50 flex justify-end">
          <div className="w-[450px] bg-neutral-900 border-l border-neutral-800 h-full p-6 shadow-2xl overflow-y-auto flex flex-col animate-in slide-in-from-right duration-200">
            <div className="flex justify-between items-center mb-6">
              <h3 className="font-medium text-lg text-white">Source Evidence</h3>
              <button onClick={() => setSelectedCitation(null)} className="text-neutral-500 hover:text-white">✕</button>
            </div>
            
            <div className="bg-neutral-950 p-3 rounded text-sm text-neutral-400 break-all mb-6 border border-neutral-800">
              URL: <a href={selectedCitation} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">{selectedCitation}</a>
            </div>
            
            <h4 className="text-sm font-semibold text-neutral-500 uppercase tracking-wider mb-3">Extracted Claims</h4>
            
            <div className="space-y-3">
              {evidenceData && evidenceData[selectedCitation] ? (
                evidenceData[selectedCitation].map((ev: any, i: number) => (
                  <div key={i} className="bg-neutral-800/50 p-4 rounded-lg border border-neutral-700/50">
                    <div className="text-sm text-neutral-200 mb-2">{ev.statement}</div>
                    <div className="flex justify-between text-xs mt-2">
                      <span className="text-blue-400 bg-blue-900/30 px-2 py-0.5 rounded uppercase">{ev.category}</span>
                      <span className="text-neutral-500">Confidence: {(ev.confidence * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-neutral-500 text-sm italic">No specific claims found for this source in the local knowledge base.</div>
              )}
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
