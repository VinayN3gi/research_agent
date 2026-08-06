"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

type Project = {
  id: string;
  name: string;
  created_at: string;
};

export default function ProjectsDashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/projects");
        if (res.ok) {
          const data = await res.json();
          setProjects(data);
        }
      } catch (e) {
        console.error("Failed to fetch projects", e);
      } finally {
        setIsLoading(false);
      }
    };
    fetchProjects();
  }, []);

  return (
    <main className="min-h-screen bg-neutral-950 text-neutral-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-8">
        <header className="border-b border-neutral-800 pb-4 flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-white">Research Workspace</h1>
            <p className="text-neutral-400 mt-2">Manage your persistent research projects</p>
          </div>
          <Link href="/" className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-lg transition-colors">
            + New Project
          </Link>
        </header>

        {isLoading ? (
          <div className="text-neutral-500">Loading projects...</div>
        ) : projects.length === 0 ? (
          <div className="bg-neutral-900 border border-neutral-800 p-12 text-center rounded-xl">
            <h2 className="text-xl font-medium text-neutral-300">No projects yet</h2>
            <p className="text-neutral-500 mt-2">Start your first research query to create a project.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((p) => (
              <Link key={p.id} href={`/projects/${p.id}`} className="bg-neutral-900 border border-neutral-800 p-6 rounded-xl hover:border-blue-500 transition-colors group">
                <h2 className="text-lg font-medium text-white group-hover:text-blue-400">{p.name}</h2>
                <p className="text-sm text-neutral-500 mt-2">
                  Created {new Date(p.created_at).toLocaleDateString()}
                </p>
              </Link>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
