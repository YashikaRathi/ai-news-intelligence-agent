import React, { useState } from 'react';
import {
  VerificationResult,
  StoryVerificationSummary,
} from '../types';
import { VerificationBadge, CredibilityBadge } from './StatusBadge';
import { formatISTDateTime, formatRelativeTime } from '../utils/time';
import {
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  AlertCircle,
  HelpCircle,
  Clock,
  Layers,
  Scale,
} from 'lucide-react';

interface VerificationPanelProps {
  result?: VerificationResult | null;
  summary?: StoryVerificationSummary | null;
  title?: string;
  className?: string;
  compact?: boolean;
}

export const VerificationPanel: React.FC<VerificationPanelProps> = ({
  result,
  summary,
  title = 'Credibility & Verification Analysis',
  className = '',
  compact = false,
}) => {
  const [expanded, setExpanded] = useState<boolean>(!compact);
  const [showMethodology, setShowMethodology] = useState<boolean>(false);

  const overallStatus =
    summary?.overall_status ||
    result?.overall_status ||
    summary?.discrepancy_status ||
    'Not checked';

  const statusReason =
    summary?.status_reason ||
    result?.status_reason ||
    'Verification pipeline evaluated cross-source reporting and external fact-checking databases.';

  const factChecks = summary?.fact_checks || result?.fact_checks || [];
  const findings = summary?.cross_source_findings || result?.cross_source_findings || {};
  const limitations = summary?.limitations || result?.limitations || [];
  const lastChecked = summary?.last_checked_at || result?.last_checked_at;

  const publisherRating = result?.source_rating;
  const publisherDomain = result?.publisher_domain;

  const agreements: string[] = findings.agreements || [];
  const differences: string[] = findings.differences || [];
  const singleSourceClaims: string[] = findings.single_source_claims || [];
  const independentSources: string[] = findings.independent_sources || [];
  const syndicatedSources: string[] = findings.syndicated_sources || [];
  const citations = findings.citations || [];

  return (
    <section className={`bg-white border border-[#E2E8F0] rounded-xl p-5 space-y-4 shadow-sm ${className}`}>
      {/* Panel Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E2E8F0] pb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-[#EFF6FF] border border-[#60A5FA]/30 flex items-center justify-center text-[#2563EB]">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-base font-extrabold text-[#0F172A] tracking-tight">{title}</h3>
            <p className="text-[11px] text-[#64748B] font-medium">
              Multi-source evidence, third-party fact-checks, and publisher governance
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <VerificationBadge status={overallStatus} size="md" />
          {compact && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="p-1 rounded hover:bg-slate-100 text-[#64748B] transition-colors"
              aria-label="Toggle details"
            >
              {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          )}
        </div>
      </div>

      {/* Main Status Callout */}
      <div className="p-3.5 rounded-lg bg-[#F7FAFF] border border-[#E2E8F0] flex items-start gap-3">
        <div className="p-1.5 rounded-md bg-white border border-[#E2E8F0] text-[#2563EB] shrink-0 mt-0.5">
          <Scale className="w-4 h-4" />
        </div>
        <div className="space-y-1 text-xs">
          <span className="font-bold text-[#0F172A] block">
            Status Verdict: <span className="text-[#2563EB]">{overallStatus}</span>
          </span>
          <p className="text-[#475569] leading-relaxed font-normal">{statusReason}</p>
        </div>
      </div>

      {expanded && (
        <div className="space-y-5 pt-1">
          {/* Two-Column Grid: Publisher Credibility + Fact-Check Results */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            {/* 1. Publisher Credibility Card */}
            <div className="bg-[#F8FAFC] p-4 rounded-xl border border-[#E2E8F0] space-y-3 flex flex-col justify-between">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#0F172A] uppercase tracking-wider text-[11px]">
                    Publisher Credibility
                  </span>
                  {publisherDomain && (
                    <span className="font-mono text-[10px] text-[#64748B] bg-white px-2 py-0.5 rounded border border-[#E2E8F0]">
                      {publisherDomain}
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <CredibilityBadge
                    status={publisherRating?.rating}
                    assessmentStatus={publisherRating?.assessment_status || result?.publisher_credibility_status}
                  />
                  <span className="text-[11px] font-semibold text-[#64748B]">
                    {publisherRating?.assessment_status === 'rated' ? 'Audited Domain' : 'Unassessed'}
                  </span>
                </div>

                <p className="text-[11px] text-[#475569] leading-relaxed">
                  {publisherRating?.explanation ||
                    'Publisher domain is evaluated against public editorial transparency records and correction notices.'}
                </p>
              </div>

              <div className="pt-2 border-t border-[#E2E8F0] text-[10px] text-[#64748B] space-y-1">
                <div>
                  <span className="font-semibold text-[#334155]">Registry Basis: </span>
                  {publisherRating?.provenance || 'Editorial Policy Audit Registry'}
                </div>
                <div className="text-amber-800 bg-amber-50/70 p-1.5 rounded border border-amber-200/50">
                  Note: Publisher reputation reflects organization policy, not proof of individual claim veracity.
                </div>
              </div>
            </div>

            {/* 2. External Fact-Check Matching */}
            <div className="bg-[#F8FAFC] p-4 rounded-xl border border-[#E2E8F0] space-y-3 flex flex-col justify-between">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-[#0F172A] uppercase tracking-wider text-[11px]">
                    External Fact-Check Results
                  </span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-white border border-[#E2E8F0] text-[#64748B]">
                    {factChecks.length} found
                  </span>
                </div>

                {factChecks.length > 0 ? (
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {factChecks.map((fc, i) => (
                      <div key={i} className="p-2.5 rounded-lg bg-white border border-[#E2E8F0] space-y-1 text-[11px]">
                        <div className="flex items-start justify-between gap-2">
                          <span className="font-semibold text-[#0F172A] line-clamp-2">
                            "{fc.claim}"
                          </span>
                          <a
                            href={fc.fact_check_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[#2563EB] hover:text-[#1D4ED8] shrink-0"
                            title="Open original fact-check"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        </div>
                        <div className="flex flex-wrap items-center gap-1.5 text-[10px] text-[#64748B]">
                          <span className="font-medium text-[#2563EB]">{fc.fact_check_publisher}</span>
                          <span>&bull;</span>
                          <span>Verdict: <strong className="text-[#0F172A]">{fc.original_rating}</strong></span>
                          {fc.review_date && (
                            <>
                              <span>&bull;</span>
                              <span>{formatISTDateTime(fc.review_date)}</span>
                            </>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="py-6 text-center space-y-1">
                    <HelpCircle className="w-6 h-6 text-slate-400 mx-auto" />
                    <p className="text-[#64748B] text-[11px] font-medium">
                      No matching third-party fact-check review found in public registry databases.
                    </p>
                    <span className="text-[10px] text-slate-400 block">
                      Absence of a fact-check record does not confirm or refute this reporting.
                    </span>
                  </div>
                )}
              </div>

              <div className="pt-2 border-t border-[#E2E8F0] text-[10px] text-[#64748B]">
                Powered by accredited third-party fact-checkers & ClaimReview metadata.
              </div>
            </div>
          </div>

          {/* 3. Cross-Source Coverage & Discrepancies */}
          {(agreements.length > 0 || differences.length > 0 || singleSourceClaims.length > 0) && (
            <div className="bg-[#F8FAFC] p-4 rounded-xl border border-[#E2E8F0] space-y-3 text-xs">
              <div className="flex items-center justify-between">
                <span className="font-bold text-[#0F172A] uppercase tracking-wider text-[11px] flex items-center gap-1.5">
                  <Layers className="w-3.5 h-3.5 text-[#2563EB]" />
                  Cross-Source Verification & Discrepancy Analysis
                </span>
                <div className="flex items-center gap-2 text-[10px] text-[#64748B]">
                  {independentSources.length > 0 && (
                    <span className="font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                      {independentSources.length} Independent Outlets
                    </span>
                  )}
                  {syndicatedSources.length > 0 && (
                    <span className="font-semibold text-slate-600 bg-slate-100 px-2 py-0.5 rounded border border-slate-200">
                      {syndicatedSources.length} Syndicated/Duplicates
                    </span>
                  )}
                </div>
              </div>

              {findings.summary && (
                <p className="text-[#334155] text-[11px] bg-white p-2.5 rounded-lg border border-[#E2E8F0]">
                  {findings.summary}
                </p>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px]">
                {/* Agreed Claims */}
                {agreements.length > 0 && (
                  <div className="space-y-1">
                    <span className="font-bold text-emerald-800 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      Claims Supported by Multiple Outlets
                    </span>
                    <ul className="space-y-1 text-[#475569] list-disc list-inside bg-white p-2.5 rounded-lg border border-[#E2E8F0]">
                      {agreements.map((a, i) => (
                        <li key={i}>{a}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Differences / Contradictions */}
                {differences.length > 0 && (
                  <div className="space-y-1">
                    <span className="font-bold text-amber-800 flex items-center gap-1">
                      <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                      Variations & Timeline Updates
                    </span>
                    <ul className="space-y-1 text-[#475569] list-disc list-inside bg-white p-2.5 rounded-lg border border-[#E2E8F0]">
                      {differences.map((d, i) => (
                        <li key={i}>{d}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Single Source Claims Notice */}
              {singleSourceClaims.length > 0 && (
                <div className="bg-amber-50/60 p-2.5 rounded-lg border border-amber-200/50 text-[11px] text-amber-900 space-y-1">
                  <span className="font-bold block">Single-Source Reporting Note:</span>
                  <p>
                    Claims reported by only one outlet are highlighted above. Note that single-source reporting is NOT automatically classified as false; further coverage is monitored.
                  </p>
                </div>
              )}

              {/* Clickable Citations */}
              {citations.length > 0 && (
                <div className="pt-2 space-y-1.5">
                  <span className="font-bold text-[#0F172A] text-[11px] block">
                    Verified Citations & Original Articles ({citations.length}):
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                    {citations.map((c: any, i: number) => (
                      <a
                        key={i}
                        href={c.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="p-2 rounded-lg bg-white hover:bg-[#EFF6FF] border border-[#E2E8F0] hover:border-[#60A5FA] flex items-center justify-between gap-2 group transition-all text-[11px]"
                      >
                        <div className="truncate space-y-0.5">
                          <span className="font-semibold text-[#0F172A] group-hover:text-[#2563EB] block truncate">
                            {c.title || c.source_name}
                          </span>
                          <span className="text-[10px] text-[#64748B]">
                            {c.source_name} &bull; {c.published_at ? formatRelativeTime(c.published_at) : 'Time unavailable'}
                          </span>
                        </div>
                        <ExternalLink className="w-3.5 h-3.5 text-[#64748B] group-hover:text-[#2563EB] shrink-0" />
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Footer Metadata: Last Checked + Methodology Collapsible */}
          <div className="pt-2 border-t border-[#E2E8F0] flex flex-wrap items-center justify-between gap-2 text-xs text-[#64748B]">
            <div className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-[#2563EB]" />
              <span>
                Last Verified:{' '}
                <strong className="text-[#0F172A]">
                  {lastChecked ? formatISTDateTime(lastChecked) : 'Recently checked'}
                </strong>
              </span>
            </div>

            <button
              onClick={() => setShowMethodology(!showMethodology)}
              className="text-[#2563EB] hover:underline font-semibold text-[11px]"
            >
              {showMethodology ? 'Hide Methodology & Limitations' : 'View Methodology & Limitations'}
            </button>
          </div>

          {/* Expandable Methodology & Limitations */}
          {showMethodology && (
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-[11px] text-[#475569] space-y-2">
              <span className="font-bold text-[#0F172A] block">
                Verification Methodology & System Limitations:
              </span>
              <ul className="space-y-1 list-disc list-inside">
                {limitations.map((lim, idx) => (
                  <li key={idx}>{lim}</li>
                ))}
              </ul>
              <p className="text-[10px] text-slate-500 pt-1">
                The AI News Intelligence Agent does not force coverage into binary True/False labels. It synthesizes verifiable registry data, publisher audit governance, third-party claim reviews, and cross-source agreement.
              </p>
            </div>
          )}
        </div>
      )}
    </section>
  );
};
