"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api";
import { 
  Swords, 
  RefreshCw, 
  Play, 
  HelpCircle, 
  Coins, 
  Clock, 
  CheckCircle,
  TrendingDown
} from "lucide-react";
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from "recharts";

interface BenchmarkRunResult {
  accuracy: number;
  latency_avg_ms: number;
  remote_tokens: number;
  local_tokens: number;
  cost_usd: number;
}

interface BenchmarkHistoryItem {
  id: number;
  benchmark_name: string;
  timestamp: string;
  total_tasks: number;
  accuracy: number;
  remote_tokens: number;
  local_tokens: number;
  cost: number;
  savings: number;
  latency_avg: number;
  config_json: string; // contains the full runs details
}

export default function BenchmarksPage() {
  const [history, setHistory] = useState<BenchmarkHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Active Selected Run
  const [selectedRun, setSelectedRun] = useState<BenchmarkHistoryItem | null>(null);
  
  // Custom Run settings
  const [runName, setRunName] = useState("Developer Suite Sweep");
  const [threshold, setThreshold] = useState(0.8);

  const fetchBenchmarks = async (selectFirst = false) => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/api/benchmarks`);
      if (!res.ok) throw new Error("Failed to fetch benchmark runs.");
      const json = await res.json();
      setHistory(json);
      if (json.length > 0 && (selectFirst || !selectedRun)) {
        setSelectedRun(json[0]);
      }
    } catch (err: any) {
      setError(err.message || "Failed to reach backend API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBenchmarks(true);
  }, []);

  const triggerBenchmark = async () => {
    setRunning(true);
    setError(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/benchmark`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          benchmark_name: runName,
          threshold: threshold
        })
      });
      if (!res.ok) throw new Error("Failed running benchmark sweep.");
      await fetchBenchmarks(true);
    } catch (err: any) {
      setError(err.message || "Error running benchmark sweep.");
    } finally {
      setRunning(false);
    }
  };

  // Parse custom configurations
  let parsedResults: Record<string, BenchmarkRunResult> | null = null;
  if (selectedRun?.config_json) {
    try {
      parsedResults = JSON.parse(selectedRun.config_json);
    } catch (e) {}
  }

  // Formatting for Recharts
  const accuracyData = parsedResults ? [
    { name: "Always Local", Accuracy: parsedResults.always_local.accuracy },
    { name: "Always Remote", Accuracy: parsedResults.always_remote.accuracy },
    { name: "TriForge Router", Accuracy: parsedResults.triforge_router.accuracy }
  ] : [];

  const latencyData = parsedResults ? [
    { name: "Always Local", Latency: parsedResults.always_local.latency_avg_ms },
    { name: "Always Remote", Latency: parsedResults.always_remote.latency_avg_ms },
    { name: "TriForge Router", Latency: parsedResults.triforge_router.latency_avg_ms }
  ] : [];

  const costData = parsedResults ? [
    { name: "Always Local", Cost: parsedResults.always_local.cost_usd },
    { name: "Always Remote", Cost: parsedResults.always_remote.cost_usd },
    { name: "TriForge Router", Cost: parsedResults.triforge_router.cost_usd }
  ] : [];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-zinc-800 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Benchmark Harness</h1>
          <p className="text-zinc-400 text-sm mt-1">Run automatic sweeps comparing pure local, remote, and hybrid routing</p>
        </div>
        <button 
          onClick={() => fetchBenchmarks()}
          disabled={loading || running}
          className="bg-zinc-800 hover:bg-zinc-700 text-white font-semibold text-xs px-4 py-2.5 rounded-lg flex items-center gap-2 border border-zinc-700 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Runs</span>
        </button>
      </div>

      {/* Control Panel */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-lg space-y-4">
        <h3 className="font-bold text-sm text-white uppercase tracking-wider flex items-center gap-2">
          <Play className="w-4 h-4 text-amber-500 fill-current" />
          Run Benchmarks Sweep
        </h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-semibold text-zinc-400 mb-1.5 uppercase">Sweep Label</label>
            <input 
              type="text" 
              value={runName} 
              onChange={(e) => setRunName(e.target.value)}
              className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-xs text-white"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-zinc-400 mb-1.5 uppercase">Consistency Threshold ({threshold})</label>
            <input 
              type="range" 
              min="0.1" 
              max="1.0" 
              step="0.05" 
              value={threshold} 
              onChange={(e) => setThreshold(parseFloat(e.target.value))}
              className="w-full h-2 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-amber-500 mt-2.5"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={triggerBenchmark}
              disabled={running || loading}
              className="w-full bg-gradient-to-r from-amber-500 to-red-500 hover:from-amber-600 hover:to-red-600 disabled:from-zinc-800 disabled:to-zinc-800 text-white font-semibold text-xs p-3 rounded-lg flex items-center justify-center gap-2 shadow-lg shadow-amber-500/10 transition active:scale-95"
            >
              {running ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Sweeping Dataset (Calling Models)...</span>
                </>
              ) : (
                <>
                  <Swords className="w-4 h-4" />
                  <span>Execute Benchmark Sweep</span>
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <p className="text-xs text-red-400 bg-red-950/20 border border-red-800/40 p-2.5 rounded-lg">
            {error}
          </p>
        )}
      </div>

      {loading && history.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-12 text-zinc-500">
          <RefreshCw className="w-8 h-8 animate-spin text-amber-500 mb-2" />
          <span className="text-xs font-semibold">Loading comparative benchmarks history...</span>
        </div>
      ) : history.length === 0 ? (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-10 text-center max-w-xl mx-auto">
          <Swords className="w-10 h-10 text-zinc-700 mx-auto mb-3" />
          <h4 className="text-base font-bold text-white">No Benchmarks Logged</h4>
          <p className="text-xs text-zinc-500 mt-1">
            Trigger a sweep using the control panel above. This runs sample evaluation tasks from sample_tasks.json.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* History Sidebar */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-lg space-y-4 h-fit">
            <h3 className="font-bold text-xs text-zinc-400 uppercase tracking-wide border-b border-zinc-800 pb-2.5">
              Historical Sweep Runs
            </h3>
            
            <div className="space-y-2 max-h-[360px] overflow-y-auto pr-1">
              {history.map((run) => (
                <div 
                  key={run.id}
                  onClick={() => setSelectedRun(run)}
                  className={`p-3 rounded-lg border text-left cursor-pointer transition ${
                    selectedRun?.id === run.id 
                      ? "bg-zinc-800 border-amber-500/45 text-white" 
                      : "bg-zinc-950/50 border-zinc-850 hover:bg-zinc-850/30 text-zinc-400"
                  }`}
                >
                  <p className="text-xs font-bold truncate">{run.benchmark_name}</p>
                  <p className="text-[10px] text-zinc-500 mt-1">
                    {new Date(run.timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                  </p>
                  <div className="flex gap-3 mt-2 text-[9px] text-zinc-400 font-mono">
                    <span>Acc: {run.accuracy}%</span>
                    <span>Saved: ${run.savings}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Visualization Section */}
          <div className="lg:col-span-3 space-y-6">
            {selectedRun && (
              <>
                {/* Run Details Cards */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 shadow-md">
                    <p className="text-[10px] font-bold text-zinc-500 uppercase">Overall Accuracy</p>
                    <p className="text-xl font-extrabold text-white mt-1 flex items-center gap-1.5">
                      <CheckCircle className="w-5 h-5 text-emerald-500" />
                      {selectedRun.accuracy}%
                    </p>
                  </div>
                  <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 shadow-md">
                    <p className="text-[10px] font-bold text-zinc-500 uppercase">Avg Latency</p>
                    <p className="text-xl font-extrabold text-white mt-1 flex items-center gap-1.5">
                      <Clock className="w-5 h-5 text-zinc-500" />
                      {selectedRun.latency_avg.toFixed(0)} ms
                    </p>
                  </div>
                  <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 shadow-md">
                    <p className="text-[10px] font-bold text-zinc-500 uppercase">Remote API Cost</p>
                    <p className="text-xl font-extrabold text-white mt-1 flex items-center gap-1.5">
                      <Coins className="w-5 h-5 text-zinc-500" />
                      ${selectedRun.cost.toFixed(4)}
                    </p>
                  </div>
                  <div className="bg-gradient-to-tr from-amber-950/20 to-zinc-900 border border-amber-800/30 rounded-xl p-4 shadow-md">
                    <p className="text-[10px] font-bold text-amber-500 uppercase">Savings Achieved</p>
                    <p className="text-xl font-extrabold text-amber-400 mt-1 flex items-center gap-1.5">
                      <TrendingDown className="w-5 h-5 text-amber-400 animate-pulse" />
                      ${selectedRun.savings.toFixed(4)}
                    </p>
                  </div>
                </div>

                {/* Performance Charts */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Accuracy Chart */}
                  <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 shadow-lg space-y-4">
                    <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wide block">Accuracy Comparison (%)</span>
                    <div className="h-44">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={accuracyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                          <XAxis dataKey="name" stroke="#71717a" fontSize={9} />
                          <YAxis stroke="#71717a" fontSize={9} />
                          <Tooltip contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a" }} />
                          <Bar dataKey="Accuracy" fill="#10b981" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Latency Chart */}
                  <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 shadow-lg space-y-4">
                    <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wide block">Avg Latency Comparison (ms)</span>
                    <div className="h-44">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={latencyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                          <XAxis dataKey="name" stroke="#71717a" fontSize={9} />
                          <YAxis stroke="#71717a" fontSize={9} />
                          <Tooltip contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a" }} />
                          <Bar dataKey="Latency" fill="#eab308" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>

                  {/* Cost Chart */}
                  <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 shadow-lg space-y-4">
                    <span className="text-[10px] font-bold text-zinc-400 uppercase tracking-wide block">Est. Cost Comparison ($)</span>
                    <div className="h-44">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={costData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                          <XAxis dataKey="name" stroke="#71717a" fontSize={9} />
                          <YAxis stroke="#71717a" fontSize={9} />
                          <Tooltip contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a" }} />
                          <Bar dataKey="Cost" fill="#3b82f6" />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>

                <div className="bg-zinc-900/50 border border-zinc-800/80 rounded-xl p-5 text-xs text-zinc-400 flex items-start gap-3">
                  <HelpCircle className="w-5 h-5 text-zinc-500 shrink-0 mt-0.5" />
                  <div>
                    <h5 className="font-bold text-zinc-300">Evaluating router efficiency</h5>
                    <p className="leading-relaxed mt-1">
                      Our hybrid routing engine achieves near-equivalent accuracy as pure remote calling, but with a fraction of the cost. Local queries are zero-cost, and escalations run on verify-draft which reduces the remote output completion tokens substantially.
                    </p>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
