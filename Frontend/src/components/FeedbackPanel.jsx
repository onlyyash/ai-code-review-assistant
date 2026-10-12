import { Sparkles, Copy } from "lucide-react";
import { useState } from "react"; // ensure this is imported

export default function FeedbackPanel({ feedback }) {
  const {
    pass_status,
    readability_score,
    efficiency_score,
    suggestions,
    errors,
    corrected_code,
    similarity_score,
    is_similar_to_sample,
    similarity_details,
  } = feedback;

  return (
    <div className="relative">
      <div className="absolute inset-0 bg-gradient-to-r from-purple-500/10 to-blue-500/10 rounded-xl blur opacity-75"></div>
      <div className="relative border border-gray-600 rounded-xl p-5 bg-slate-900/90 backdrop-blur-sm text-white shadow-xl h-full overflow-y-auto space-y-4">
        {/* Header */}
        <div className="flex items-center gap-3 mb-2">
          <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-cyan-500 rounded-xl flex items-center justify-center">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-xl font-bold text-white">AI Feedback Summary</h2>
        </div>

        {/* Pass Status */}
        <div className="bg-gray-800/50 rounded-lg p-3 text-sm">
          <p className="flex items-center gap-2">
            <strong className="text-white">Status:</strong>
            {pass_status ? (
              <span className="text-green-400 bg-green-500/20 px-2 py-1 rounded-full text-xs">
                ✅ Pass
              </span>
            ) : (
              <span className="text-red-400 bg-red-500/20 px-2 py-1 rounded-full text-xs">
                ❌ Fail
              </span>
            )}
          </p>
        </div>

        {/* Top: Chart Scores */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          {/* Readability */}
          <div className="bg-gray-800/50 rounded-lg p-3">
            <p className="text-white font-medium">Readability</p>
            <div className="flex items-center gap-2 mt-1">
              <div className="flex-1 bg-gray-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full"
                  style={{ width: `${(readability_score / 10) * 100}%` }}
                ></div>
              </div>
              <span className="text-white font-bold">
                {readability_score}/10
              </span>
            </div>
          </div>

          {/* Efficiency */}
          <div className="bg-gray-800/50 rounded-lg p-3">
            <p className="text-white font-medium">Efficiency</p>
            <div className="flex items-center gap-2 mt-1">
              <div className="flex-1 bg-gray-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-purple-500 to-cyan-500 h-2 rounded-full"
                  style={{ width: `${(efficiency_score / 10) * 100}%` }}
                ></div>
              </div>
              <span className="text-white font-bold">
                {efficiency_score}/10
              </span>
            </div>
          </div>

          {/* Similarity */}
          {similarity_score !== null && (
            <div className="bg-gray-800/50 rounded-lg p-3">
              <p className="text-white font-medium mb-2">
                Similarity to Sample
              </p>
              <div className="flex items-center gap-2 mb-2">
                <div className="flex-1 bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${
                      is_similar_to_sample
                        ? "bg-gradient-to-r from-green-400 to-green-600"
                        : "bg-gradient-to-r from-red-500 to-red-700"
                    }`}
                    style={{ width: `${similarity_score}%` }}
                  ></div>
                </div>
                <span className="text-white font-bold">
                  {similarity_score}%
                </span>
              </div>
              <span
                className={`text-xs px-2 py-1 rounded-full ${
                  is_similar_to_sample
                    ? "text-green-400 bg-green-500/20"
                    : "text-red-400 bg-red-500/20"
                }`}
              >
                {is_similar_to_sample ? "Similar" : "Not Similar"}
              </span>
              {similarity_details && (
                <p className="text-xs text-gray-400 mt-2">
                  Structure match {similarity_details.token_similarity}% ·
                  Fingerprint match {similarity_details.fingerprint_similarity}%
                  <span className="block text-gray-500">
                    Ignores renamed variables, comments, formatting and
                    reordered functions.
                  </span>
                </p>
              )}
            </div>
          )}
        </div>

        {/* Bottom: 2-Column Layout */}
        <div className="grid md:grid-cols-2 gap-4 text-sm">
          {/* Left: Errors & Suggestions */}
          <div className="space-y-4">
            {/* Errors */}
            {errors?.length > 0 && (
              <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
                <h3 className="font-semibold text-red-400 mb-2 flex items-center gap-2">
                  🚫 Detected Errors
                </h3>
                <ul className="space-y-1">
                  {errors.map((e, i) => (
                    <li key={i} className="text-red-300 flex items-start gap-2">
                      <span className="text-red-500 mt-1">•</span>
                      <span>{e}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Suggestions */}
            {suggestions?.length > 0 && (
              <div className="bg-blue-900/20 border border-blue-500/30 rounded-lg p-4">
                <h3 className="font-semibold text-blue-400 mb-2 flex items-center gap-2">
                  💡 Suggestions
                </h3>
                <ul className="space-y-1">
                  {suggestions.map((s, i) => (
                    <li
                      key={i}
                      className="text-blue-200 flex items-start gap-2"
                    >
                      <span className="text-blue-500 mt-1">•</span>
                      <span>{s}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Right: Corrected Code */}
          {corrected_code && (
            <div className="bg-green-900/20 border border-green-500/30 rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-green-400 flex items-center gap-2">
                  ✅ Suggested Correction
                </h3>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(corrected_code);
                  }}
                  className="text-green-300 hover:text-white transition-colors"
                  title="Copy to clipboard"
                >
                  <Copy className="w-5 h-5" />
                </button>
              </div>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-3 overflow-hidden">
                <pre className="text-green-100 text-xs overflow-x-auto whitespace-pre-wrap font-mono">
                  <code>{corrected_code}</code>
                </pre>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
