import React from 'react';
import { VerificationResponse } from '../types';
import { ShieldCheck, CheckCircle2, AlertCircle, Building2, FileCheck2, Award } from 'lucide-react';

interface VerificationPanelProps {
  verification: VerificationResponse;
}

export const VerificationPanel: React.FC<VerificationPanelProps> = ({ verification }) => {
  const { trust_score, publisher_credibility, claim_checks, summary, total_sources, total_articles } = verification;

  return (
    <div className="bg-white rounded-2xl border border-[#E2E8F0] p-6 shadow-sm space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#E2E8F0] pb-4">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-xl bg-[#EFF6FF] border border-[#60A5FA]/30 text-[#2563EB]">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-lg font-black text-[#0F172A] tracking-tight">
                NewsTrust AI Authenticity & Evidence Layer
              </h3>
              <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-[#2563EB] text-white">
                Live Verification
              </span>
            </div>
            <p className="text-xs font-semibold text-[#64748B] mt-0.5">
              {summary}
            </p>
          </div>
        </div>

        {/* Big Trust Score Metric Ring/Badge */}
        <div className="flex items-center gap-3 bg-[#F7FAFF] border border-[#E2E8F0] rounded-xl px-4 py-2.5">
          <div className="text-right">
            <div className="text-[10px] font-black uppercase text-[#64748B] tracking-wider">
              Trust Score
            </div>
            <div className="text-xs font-bold text-[#0F172A]">
              {trust_score.label}
            </div>
          </div>
          <div className="w-12 h-12 rounded-xl bg-[#2563EB] text-white flex items-center justify-center text-lg font-black shadow-inner">
            {trust_score.score}
          </div>
        </div>
      </div>

      {/* Metrics Breakdown Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 rounded-xl bg-[#F7FAFF] border border-[#E2E8F0]">
          <div className="flex items-center justify-between text-xs text-[#64748B] font-semibold mb-1">
            <span className="flex items-center gap-1.5">
              <Award className="w-4 h-4 text-[#2563EB]" /> Corroboration Index
            </span>
            <span className="font-bold text-[#0F172A]">{trust_score.corroboration_score}/100</span>
          </div>
          <div className="w-full bg-[#E2E8F0] h-2 rounded-full overflow-hidden mt-2">
            <div
              className="bg-[#2563EB] h-full rounded-full transition-all"
              style={{ width: `${trust_score.corroboration_score}%` }}
            />
          </div>
          <div className="text-[11px] text-[#64748B] mt-2 font-medium">
            Based on {total_sources} outlet(s) & {total_articles} article dispatch(es)
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#F7FAFF] border border-[#E2E8F0]">
          <div className="flex items-center justify-between text-xs text-[#64748B] font-semibold mb-1">
            <span className="flex items-center gap-1.5">
              <Building2 className="w-4 h-4 text-[#2563EB]" /> Publisher Authority
            </span>
            <span className="font-bold text-[#0F172A]">{trust_score.publisher_credibility_score}/100</span>
          </div>
          <div className="w-full bg-[#E2E8F0] h-2 rounded-full overflow-hidden mt-2">
            <div
              className="bg-[#2563EB] h-full rounded-full transition-all"
              style={{ width: `${trust_score.publisher_credibility_score}%` }}
            />
          </div>
          <div className="text-[11px] text-[#64748B] mt-2 font-medium">
            Verified tier evaluation across source domains
          </div>
        </div>

        <div className="p-4 rounded-xl bg-[#F7FAFF] border border-[#E2E8F0]">
          <div className="flex items-center justify-between text-xs text-[#64748B] font-semibold mb-1">
            <span className="flex items-center gap-1.5">
              <FileCheck2 className="w-4 h-4 text-[#2563EB]" /> Confidence Level
            </span>
            <span className="font-bold text-[#2563EB]">{trust_score.confidence_level}</span>
          </div>
          <div className="w-full bg-[#E2E8F0] h-2 rounded-full overflow-hidden mt-2">
            <div
              className="bg-[#2563EB] h-full rounded-full transition-all"
              style={{ width: trust_score.confidence_level === 'High' ? '95%' : '75%' }}
            />
          </div>
          <div className="text-[11px] text-[#64748B] mt-2 font-medium">
            Empirical evidence check status
          </div>
        </div>
      </div>

      {/* Claim & Evidence Audits Table */}
      {claim_checks && claim_checks.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-extrabold text-[#0F172A] uppercase tracking-wider flex items-center gap-1.5">
              <FileCheck2 className="w-4 h-4 text-[#2563EB]" /> Fact & Claim Verification Checks
            </h4>
            <span className="text-xs font-semibold text-[#64748B]">
              {claim_checks.length} Claims Audited
            </span>
          </div>

          <div className="space-y-2.5">
            {claim_checks.map((claim, idx) => {
              const isCorroborated = claim.status === 'Corroborated';
              return (
                <div
                  key={idx}
                  className="p-3.5 rounded-xl border border-[#E2E8F0] bg-[#F7FAFF] flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                >
                  <div className="space-y-1">
                    <div className="font-bold text-[#0F172A] flex items-center gap-2">
                      {isCorroborated ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                      ) : (
                        <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0" />
                      )}
                      <span>{claim.claim_text}</span>
                    </div>
                    <p className="text-[#64748B] pl-6">{claim.details}</p>
                  </div>

                  <div className="flex items-center gap-2 pl-6 sm:pl-0 flex-shrink-0">
                    <span
                      className={`px-2.5 py-1 rounded-full text-[11px] font-bold border ${
                        isCorroborated
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-amber-50 text-amber-700 border-amber-200'
                      }`}
                    >
                      {claim.status}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Publisher Credibility Breakdown */}
      {publisher_credibility && publisher_credibility.length > 0 && (
        <div className="space-y-3 border-t border-[#E2E8F0] pt-4">
          <h4 className="text-sm font-extrabold text-[#0F172A] uppercase tracking-wider flex items-center gap-1.5">
            <Building2 className="w-4 h-4 text-[#2563EB]" /> Publisher Credibility Tiers
          </h4>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {publisher_credibility.map((pub, idx) => (
              <div
                key={idx}
                className="p-3 rounded-xl border border-[#E2E8F0] bg-[#F7FAFF] flex items-center justify-between"
              >
                <div>
                  <div className="font-bold text-[#0F172A] text-xs">{pub.source_name}</div>
                  <div className="text-[10px] font-semibold text-[#64748B]">
                    {pub.credibility_tier}
                  </div>
                </div>
                <div className="text-right">
                  <span className="px-2 py-0.5 rounded text-[10px] font-extrabold bg-[#EFF6FF] text-[#2563EB] border border-[#60A5FA]/30">
                    {pub.domain_authority_score}/100
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
