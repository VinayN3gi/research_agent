"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import ReactMarkdown from "react-markdown";

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
    fetchProject();
  }, [projectId]);

  if (isLoading) return <div className="p-8 text-neutral-500">Loading workspace...</div>;
  if (!project) return <div className="p-8 text-red-500">Project not found</div>;

  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100 flex">
      {/* Sidebar */}
      <aside className="w-64 border-r border-neutral-800 p-4 space-y-6 shrink-0">
        <div>
          <h2 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">Project</h2>
          <div className="font-medium text-white truncate">{project.name}</div>
        </div>

        <div>
          <h2 className="text-xs font-semibold text-neutral-500 uppercase tracking-wider mb-2">Research Runs</h2>
          <div className="space-y-2">
            {project.runs.map(run => (
              <div key={run.id} className="text-sm border border-neutral-800 bg-neutral-900 p-2 rounded">
                <div className="truncate text-blue-400 font-medium" title={run.query}>{run.query}</div>
                <div className="text-xs text-neutral-500 flex justify-between mt-1">
                  <span>{run.status}</span>
                  <span>{new Date(run.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Research Timeline Header */}
        <header className="border-b border-neutral-800 p-6 flex gap-4 overflow-x-auto items-center">
          <div className="text-sm font-medium text-neutral-400 mr-4">Timeline:</div>
          <div className="flex items-center gap-2">
             <span className="px-3 py-1 bg-green-900/50 text-green-400 rounded-full text-xs">Planning</span>
             <span className="text-neutral-600">→</span>
             <span className="px-3 py-1 bg-blue-900/50 text-blue-400 rounded-full text-xs">Search</span>
             <span className="text-neutral-600">→</span>
             <span className="px-3 py-1 bg-neutral-800 text-neutral-400 rounded-full text-xs">Extraction</span>
             <span className="text-neutral-600">→</span>
             <span className="px-3 py-1 bg-neutral-800 text-neutral-400 rounded-full text-xs">Reflection</span>
             <span className="text-neutral-600">→</span>
             <span className="px-3 py-1 bg-neutral-800 text-neutral-400 rounded-full text-xs">Writing</span>
          </div>
        </header>

        {/* Workspace Body */}
        <div className="flex-1 p-6 overflow-y-auto">
          {project.reports.length > 0 ? (
            <div className="bg-neutral-900 border border-neutral-800 p-6 rounded-xl space-y-4">
              <h2 className="text-lg font-medium text-neutral-300 border-b border-neutral-800 pb-2 flex justify-between">
                <span>Final Report</span>
                <span className="text-sm text-neutral-500">v{project.reports[0].version}</span>
              </h2>
              <div className="prose prose-invert max-w-none text-neutral-200 min-h-25">
                <ReactMarkdown>{project.reports[0].content}</ReactMarkdown>
              </div>
            </div>
          ) : (
             <div className="text-center text-neutral-500 mt-20">No report generated yet. Research might be running...</div>
          )}
        </div>
      </div>
    </main>
  );
}
