"use client";

import { useEffect, useState } from "react";
import { API_BASE_URL } from "@/lib/api";
import { 
  Settings, 
  RefreshCw, 
  Save, 
  Key, 
  Sliders, 
  Database,
  CheckCircle,
  HelpCircle,
  ShieldCheck
} from "lucide-react";

interface SettingsData {
  active_local_model: string;
  active_remote_model: string;
  default_threshold: number;
  enable_cache: boolean;
  enable_prompt_compression: boolean;
  fireworks_api_key?: string;
  openai_api_key?: string;
  anthropic_api_key?: string;
}

export default function SettingsPage() {
  const [formData, setFormData] = useState<SettingsData>({
    active_local_model: "qwen2.5:3b-instruct",
    active_remote_model: "accounts/fireworks/models/llama-v3p1-8b-instruct",
    default_threshold: 0.8,
    enable_cache: true,
    enable_prompt_compression: false,
    fireworks_api_key: "",
    openai_api_key: "",
    anthropic_api_key: ""
  });

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchSettings = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/settings`);
      if (!res.ok) throw new Error("Failed to fetch settings from API.");
      const json = await res.json();
      setFormData(json);
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to contact backend API.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg(null);
    setErrorMsg(null);
    try {
      const res = await fetch(`${API_BASE_URL}/api/settings`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      });
      if (!res.ok) throw new Error("Failed to save settings changes.");
      setSuccessMsg("System configuration updated successfully.");
      setTimeout(() => setSuccessMsg(null), 3000);
    } catch (err: any) {
      setErrorMsg(err.message || "Error saving configuration changes.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-screen text-zinc-400">
        <RefreshCw className="w-8 h-8 animate-spin text-amber-500 mb-3" />
        <p className="text-sm font-semibold tracking-wide">Retrieving system configurations...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center border-b border-zinc-800 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">System Settings</h1>
          <p className="text-zinc-400 text-sm mt-1">Configure pluggable API credentials, active routing models, and thresholds</p>
        </div>
      </div>

      <form onSubmit={handleSave} className="space-y-6">
        {/* API Credentials */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-lg space-y-4">
          <h3 className="font-bold text-sm text-white uppercase tracking-wider flex items-center gap-2 border-b border-zinc-800 pb-3">
            <Key className="w-4 h-4 text-amber-500" />
            API Key Credentials
          </h3>
          
          <div className="space-y-4 text-xs">
            <div>
              <label className="block font-semibold text-zinc-400 mb-1.5 uppercase">Fireworks AI API Key</label>
              <input 
                type="password" 
                value={formData.fireworks_api_key || ""} 
                onChange={(e) => setFormData({ ...formData, fireworks_api_key: e.target.value })}
                placeholder="Paste your fireworks key here (starts with fw_)..."
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-white placeholder-zinc-600 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block font-semibold text-zinc-400 mb-1.5 uppercase">OpenAI API Key (Optional)</label>
              <input 
                type="password" 
                value={formData.openai_api_key || ""} 
                onChange={(e) => setFormData({ ...formData, openai_api_key: e.target.value })}
                placeholder="Paste your openai key here (starts with sk-)..."
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-white placeholder-zinc-600 focus:outline-none focus:border-amber-500"
              />
            </div>

            <div>
              <label className="block font-semibold text-zinc-400 mb-1.5 uppercase">Anthropic API Key (Optional)</label>
              <input 
                type="password" 
                value={formData.anthropic_api_key || ""} 
                onChange={(e) => setFormData({ ...formData, anthropic_api_key: e.target.value })}
                placeholder="Paste your anthropic key here (starts with sk-ant-)..."
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-white placeholder-zinc-600 focus:outline-none focus:border-amber-500"
              />
            </div>
          </div>
        </div>

        {/* Model Configurations */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-lg space-y-4">
          <h3 className="font-bold text-sm text-white uppercase tracking-wider flex items-center gap-2 border-b border-zinc-800 pb-3">
            <Sliders className="w-4 h-4 text-amber-500" />
            Model & Routing Policies
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="block font-semibold text-zinc-400 mb-1.5 uppercase">Active Local Model</label>
              <select 
                value={formData.active_local_model} 
                onChange={(e) => setFormData({ ...formData, active_local_model: e.target.value })}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-white"
              >
                <option value="qwen2.5:3b-instruct">Qwen 2.5 3B (Instruct)</option>
                <option value="gemma2:2b">Gemma 2 2B</option>
                <option value="phi3:3.8b">Phi-3 3.8B</option>
                <option value="tinyllama:1.1b">TinyLlama 1.1B</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-zinc-400 mb-1.5 uppercase">Active Remote Model</label>
              <select 
                value={formData.active_remote_model} 
                onChange={(e) => setFormData({ ...formData, active_remote_model: e.target.value })}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-white"
              >
                <option value="accounts/fireworks/models/llama-v3p1-8b-instruct">Llama 3.1 8B (Fireworks)</option>
                <option value="accounts/fireworks/models/llama-v3p1-70b-instruct">Llama 3.1 70B (Fireworks)</option>
                <option value="gpt-4o-mini">GPT-4o Mini (OpenAI)</option>
                <option value="claude-3-5-sonnet-20240620">Claude 3.5 Sonnet (Anthropic)</option>
              </select>
            </div>

            <div>
              <label className="block font-semibold text-zinc-400 mb-1.5 uppercase">Consistency Agreement Threshold</label>
              <input 
                type="number" 
                min="0.1" 
                max="1.0" 
                step="0.05"
                value={formData.default_threshold} 
                onChange={(e) => setFormData({ ...formData, default_threshold: parseFloat(e.target.value) })}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2.5 text-white mt-1.5"
              />
            </div>
          </div>
        </div>

        {/* Cache & Optimization */}
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-6 shadow-lg space-y-4">
          <h3 className="font-bold text-sm text-white uppercase tracking-wider flex items-center gap-2 border-b border-zinc-800 pb-3">
            <Database className="w-4 h-4 text-amber-500" />
            Optimizations
          </h3>
          
          <div className="space-y-4 text-xs">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="font-bold text-white text-sm">Smart Query Caching</h4>
                <p className="text-zinc-500 text-xs mt-0.5">Enable direct SQLite retrieval of previous prompt answers</p>
              </div>
              <input 
                type="checkbox" 
                checked={formData.enable_cache} 
                onChange={(e) => setFormData({ ...formData, enable_cache: e.target.checked })}
                className="w-4 h-4 text-amber-500 bg-zinc-950 border-zinc-800 rounded accent-amber-500"
              />
            </div>

            <div className="flex items-center justify-between border-t border-zinc-850/60 pt-4">
              <div>
                <h4 className="font-bold text-white text-sm">Prompt Compression</h4>
                <p className="text-zinc-500 text-xs mt-0.5">Summarize lengthy contexts using local models before remote calls to save remote tokens</p>
              </div>
              <input 
                type="checkbox" 
                checked={formData.enable_prompt_compression} 
                onChange={(e) => setFormData({ ...formData, enable_prompt_compression: e.target.checked })}
                className="w-4 h-4 text-amber-500 bg-zinc-950 border-zinc-800 rounded accent-amber-500"
              />
            </div>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-4 items-center">
          <button
            type="submit"
            disabled={saving}
            className="bg-gradient-to-r from-amber-500 to-red-500 hover:from-amber-600 hover:to-red-600 disabled:from-zinc-850 disabled:to-zinc-850 text-white font-semibold text-xs px-6 py-3 rounded-lg flex items-center gap-2 shadow-lg shadow-amber-500/10 active:scale-95 transition"
          >
            {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            <span>Save System Changes</span>
          </button>
          
          {successMsg && (
            <div className="text-emerald-400 text-xs font-semibold flex items-center gap-1.5 animate-fade-in">
              <CheckCircle className="w-4 h-4" />
              {successMsg}
            </div>
          )}

          {errorMsg && (
            <p className="text-red-400 text-xs">
              {errorMsg}
            </p>
          )}
        </div>
      </form>
    </div>
  );
}
