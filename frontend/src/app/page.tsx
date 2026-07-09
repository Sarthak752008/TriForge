"use client";

import { useEffect, useState } from "react";
import { 
  Zap, 
  TrendingUp, 
  Coins, 
  Cpu, 
  Database, 
  Clock, 
  RefreshCw,
  HelpCircle,
  AlertCircle
} from "lucide-react";
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, Legend, Cell, PieChart, Pie
} from "recharts";

interface DailyStat {
  date: string;
  requests: number;
  latency_ms: number;
  cost_usd: number;
  savings_usd: number;
}

interface AnalyticsData {
  total_requests: number;
  local_requests: number;
  remote_requests: number;
  escalated_requests: number;
  tokens_spent_remote: number;
  tokens_spent_local: number;
  tokens_saved_local: number;
  estimated_cost_usd: number;
  estimated_savings_usd: number;
  cache_hit_rate: number;
  average_latency_ms: number;
  daily_stats: DailyStat[];
}

export default function Dashboard() {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/api/analytics");
      if (!res.ok) throw new Error("Failed to fetch analytics statistics.");
      const json = await res.json();
      setData(json);
    } catch (err: any) {
      setError(err.message || "Failed to reach backend API. Make sure FastAPI server is running on http://localhost:8000.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-screen text-zinc-400">
        <RefreshCw className="w-8 h-8 animate-spin text-amber-500 mb-3" />
        <p className="text-sm font-semibold tracking-wide">Compiling analytics metrics...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 max-w-7xl mx-auto space-y-6">
        <div className="flex justify-between items-center border-b border-zinc-800 pb-5">
          <div>
            <h1 className="text-3xl font-extrabold text-white tracking-tight">Analytics Dashboard</h1>
            <p className="text-zinc-400 text-sm mt-1">Real-time Hybrid router performance monitoring</p>
          </div>
          <button 
            onClick={fetchAnalytics}
            className="bg-zinc-800 hover:bg-zinc-700 text-white font-semibold text-xs px-4 py-2 rounded-lg flex items-center gap-2 border border-zinc-700 transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Connection</span>
          </button>
        </div>

        <div className="bg-red-950/20 border border-red-800/80 rounded-xl p-6 flex gap-4 items-start text-red-200">
          <AlertCircle className="w-6 h-6 shrink-0 text-red-500" />
          <div>
            <h3 className="font-bold text-red-400 text-base">Backend Connection Failed</h3>
            <p className="text-sm text-red-300/80 mt-1 leading-relaxed">
              Could not fetch data from the FastAPI server. Please check that your backend service is running locally on port 8000 (e.g. by running uvicorn) or inside the Docker environment.
            </p>
            <p className="text-xs text-red-400/70 mt-3 font-mono">
              Error details: {error}
            </p>
          </div>
        </div>
      </div>
    );
  }

  const {
    total_requests,
    local_requests,
    remote_requests,
    escalated_requests,
    tokens_spent_remote,
    tokens_spent_local,
    tokens_saved_local,
    estimated_cost_usd,
    estimated_savings_usd,
    cache_hit_rate,
    average_latency_ms,
    daily_stats
  } = data;

  // Pie chart data
  const pieData = [
    { name: "Pure Local", value: local_requests - escalated_requests, color: "#10b981" },
    { name: "Pure Remote", value: remote_requests, color: "#3b82f6" },
    { name: "Escalated", value: escalated_requests, color: "#f59e0b" },
  ].filter(item => item.value > 0);

  // If no requests have been logged yet
  const hasData = total_requests > 0;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-zinc-800 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Analytics Dashboard</h1>
          <p className="text-zinc-400 text-sm mt-1">Real-time monitoring of model routing, token usage, and cost efficiency</p>
        </div>
        <button 
          onClick={fetchAnalytics}
          className="bg-zinc-800 hover:bg-zinc-700 text-white font-semibold text-xs px-4 py-2.5 rounded-lg flex items-center gap-2 border border-zinc-700 transition-all active:scale-95"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Data</span>
        </button>
      </div>

      {!hasData ? (
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-12 text-center max-w-2xl mx-auto space-y-4">
          <Zap className="w-12 h-12 text-amber-500 mx-auto animate-pulse" />
          <h3 className="text-xl font-bold text-white">No Statistics Found</h3>
          <p className="text-zinc-400 text-sm leading-relaxed">
            The router logs are currently empty. Head over to the Chat Interface page to submit prompts, or trigger a benchmark sweep to generate database entries.
          </p>
          <a
            href="/chat"
            className="inline-block bg-gradient-to-r from-amber-500 to-red-500 hover:from-amber-600 hover:to-red-600 text-white font-semibold text-sm px-6 py-3 rounded-lg shadow-lg hover:shadow-amber-500/25 transition"
          >
            Start Chatting
          </a>
        </div>
      ) : (
        <>
          {/* KPI Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            {/* Money Saved */}
            <div className="bg-gradient-to-br from-emerald-950/40 to-zinc-900 border border-emerald-800/30 rounded-xl p-5 shadow-lg relative overflow-hidden group">
              <div className="absolute right-4 top-4 bg-emerald-500/10 text-emerald-400 p-2 rounded-lg border border-emerald-500/20 group-hover:scale-110 transition-transform">
                <Coins className="w-5 h-5" />
              </div>
              <p className="text-xs font-semibold text-emerald-400/80 uppercase tracking-wider">Estimated Savings</p>
              <h3 className="text-3xl font-extrabold text-white mt-2">${estimated_savings_usd.toFixed(4)}</h3>
              <p className="text-xs text-zinc-500 mt-2">Compared to always querying remote</p>
            </div>

            {/* Total Saved Tokens */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-lg relative overflow-hidden group">
              <div className="absolute right-4 top-4 bg-zinc-800 text-zinc-400 p-2 rounded-lg border border-zinc-700 group-hover:scale-110 transition-transform">
                <TrendingUp className="w-5 h-5" />
              </div>
              <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Saved Remote Tokens</p>
              <h3 className="text-3xl font-extrabold text-white mt-2">{tokens_saved_local.toLocaleString()}</h3>
              <p className="text-xs text-zinc-500 mt-2">Zero-cost local & cache resolutions</p>
            </div>

            {/* Token Cost */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-lg relative overflow-hidden group">
              <div className="absolute right-4 top-4 bg-zinc-800 text-zinc-400 p-2 rounded-lg border border-zinc-700 group-hover:scale-110 transition-transform">
                <Cpu className="w-5 h-5" />
              </div>
              <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Estimated Cost</p>
              <h3 className="text-3xl font-extrabold text-white mt-2">${estimated_cost_usd.toFixed(4)}</h3>
              <p className="text-xs text-zinc-500 mt-2">Spent on Fireworks/Remote API</p>
            </div>

            {/* Cache Hits */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-lg relative overflow-hidden group">
              <div className="absolute right-4 top-4 bg-zinc-800 text-zinc-400 p-2 rounded-lg border border-zinc-700 group-hover:scale-110 transition-transform">
                <Database className="w-5 h-5" />
              </div>
              <p className="text-xs font-semibold text-zinc-400 uppercase tracking-wider">Cache Hit Rate</p>
              <h3 className="text-3xl font-extrabold text-white mt-2">{cache_hit_rate.toFixed(1)}%</h3>
              <p className="text-xs text-zinc-500 mt-2">Prompt answers loaded instantly</p>
            </div>
          </div>

          {/* Secondary KPI Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div className="bg-zinc-900/50 border border-zinc-800/80 p-4 rounded-xl flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-zinc-500">Total Requests</p>
                <h4 className="text-xl font-bold text-white mt-1">{total_requests}</h4>
              </div>
              <div className="text-xs bg-zinc-800 text-zinc-300 px-3 py-1.5 rounded-lg border border-zinc-700">
                Local: {local_requests} | Remote: {remote_requests}
              </div>
            </div>

            <div className="bg-zinc-900/50 border border-zinc-800/80 p-4 rounded-xl flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-zinc-500">Escalations</p>
                <h4 className="text-xl font-bold text-white mt-1">{escalated_requests}</h4>
              </div>
              <div className="text-[10px] text-amber-500 bg-amber-950/20 border border-amber-800/30 px-2 py-1 rounded-md">
                Verify-Draft triggered
              </div>
            </div>

            <div className="bg-zinc-900/50 border border-zinc-800/80 p-4 rounded-xl flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-zinc-500">Average Latency</p>
                <h4 className="text-xl font-bold text-white mt-1">{average_latency_ms.toFixed(0)} ms</h4>
              </div>
              <div className="text-zinc-500 flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                <span className="text-xs">End-to-end</span>
              </div>
            </div>
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Time Series Area Chart */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-lg lg:col-span-2 space-y-4">
              <div>
                <h3 className="text-lg font-bold text-white">Daily Routing Volume & Cost</h3>
                <p className="text-xs text-zinc-400 mt-0.5">Historical daily activity logs</p>
              </div>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={daily_stats}>
                    <defs>
                      <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2}/>
                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                    <XAxis dataKey="date" stroke="#71717a" fontSize={11} />
                    <YAxis stroke="#71717a" fontSize={11} />
                    <Tooltip contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a" }} />
                    <Area type="monotone" dataKey="requests" stroke="#3b82f6" fillOpacity={1} fill="url(#colorRequests)" name="Total Requests" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Routing Split Pie Chart */}
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 shadow-lg flex flex-col space-y-4">
              <div>
                <h3 className="text-lg font-bold text-white">Routing Strategy Split</h3>
                <p className="text-xs text-zinc-400 mt-0.5">Breakdown of target paths taken</p>
              </div>
              {pieData.length === 0 ? (
                <div className="flex-1 flex items-center justify-center text-zinc-500 text-xs">
                  Insufficient data to render split chart
                </div>
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center relative">
                  <div className="h-44 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={pieData}
                          cx="50%"
                          cy="50%"
                          innerRadius={45}
                          outerRadius={65}
                          paddingAngle={3}
                          dataKey="value"
                        >
                          {pieData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip contentStyle={{ backgroundColor: "#18181b", borderColor: "#27272a" }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="flex gap-4 mt-2 justify-center flex-wrap">
                    {pieData.map((item, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-xs">
                        <span className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                        <span className="text-zinc-300 font-semibold">{item.name} ({item.value})</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
