import React, { useEffect, useState } from 'react';
import { ReviewSummary, ReviewItem } from '../types';
import {
  getReviewsSummary,
  submitReview,
  updateReview,
  deleteReview,
  getOrCreateReaderId,
} from '../services/api';
import { formatISTDateTime, formatRelativeTime } from '../utils/time';
import {
  Star,
  MessageSquare,
  Trash2,
  Edit2,
  Send,
  User,
  Info,
  CheckCircle,
} from 'lucide-react';

interface ReaderReviewsProps {
  targetType: 'article' | 'story';
  targetId: string;
  targetTitle?: string;
  className?: string;
}

export const ReaderReviews: React.FC<ReaderReviewsProps> = ({
  targetType,
  targetId,
  targetTitle,
  className = '',
}) => {
  const [summary, setSummary] = useState<ReviewSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form State
  const [rating, setRating] = useState<number>(5);
  const [hoverRating, setHoverRating] = useState<number>(0);
  const [reviewText, setReviewText] = useState<string>('');
  const [readerName, setReaderName] = useState<string>('');
  const [editingReviewId, setEditingReviewId] = useState<string | null>(null);

  const currentReaderId = getOrCreateReaderId();

  const loadReviews = async () => {
    try {
      setLoading(true);
      const data = await getReviewsSummary(targetType, targetId);
      setSummary(data);

      // Prepopulate form if user already has a review
      if (data.user_review) {
        setRating(data.user_review.rating);
        setReviewText(data.user_review.review_text || '');
        setReaderName(data.user_review.reader_name || '');
      }
    } catch (err: any) {
      console.warn('Unable to load reviews:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReviews();
  }, [targetType, targetId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (rating < 1 || rating > 5) return;

    setSubmitting(true);
    setError(null);
    setSuccessMsg(null);

    try {
      if (editingReviewId) {
        await updateReview(editingReviewId, {
          rating,
          review_text: reviewText.trim() || undefined,
          reader_name: readerName.trim() || 'Reader',
        });
        setSuccessMsg('Your review was successfully updated.');
        setEditingReviewId(null);
      } else {
        await submitReview(targetType, targetId, {
          rating,
          review_text: reviewText.trim() || undefined,
          reader_name: readerName.trim() || 'Reader',
        });
        setSuccessMsg('Thank you! Your feedback has been recorded.');
      }
      await loadReviews();
    } catch (err: any) {
      setError(err?.response?.data?.detail || 'Failed to submit rating. Please try again.');
    } finally {
      setSubmitting(false);
      setTimeout(() => setSuccessMsg(null), 4000);
    }
  };

  const handleDelete = async (reviewId: string) => {
    if (!window.confirm('Are you sure you want to delete your review?')) return;
    try {
      await deleteReview(reviewId);
      setEditingReviewId(null);
      setReviewText('');
      setRating(5);
      await loadReviews();
    } catch (err: any) {
      alert('Unable to delete review: ' + (err?.response?.data?.detail || err.message));
    }
  };

  const handleStartEdit = (item: ReviewItem) => {
    setEditingReviewId(item.id);
    setRating(item.rating);
    setReviewText(item.review_text || '');
    setReaderName(item.reader_name);
  };

  const totalRatings = summary?.total_ratings || 0;
  const avgRating = summary?.average_rating || 0;
  const distribution = summary?.rating_distribution || { '5': 0, '4': 0, '3': 0, '2': 0, '1': 0 };

  return (
    <section className={`bg-white border border-[#E2E8F0] rounded-xl p-6 space-y-6 shadow-sm ${className}`}>
      {/* Header with clear disclaimer */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#E2E8F0] pb-4">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-[#2563EB]" />
            <h3 className="text-xl font-extrabold text-[#0F172A] tracking-tight">
              Reader Reviews & Community Ratings
            </h3>
          </div>
          <p className="text-xs text-[#64748B] font-medium">
            Reader feedback on article usefulness, clarity, and reading experience.
          </p>
        </div>

        {/* Prominent Truthfulness Disclaimer Badge */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-amber-50 border border-amber-200/70 text-amber-900 text-[11px] font-medium max-w-md">
          <Info className="w-4 h-4 text-amber-600 shrink-0" />
          <span>
            <strong>Reader Rating:</strong> Reflects reader perspective & clarity. This is <em>NOT</em> a truthfulness verdict and does not affect fact-checking.
          </span>
        </div>
      </div>

      {/* Aggregate Score & Distribution Grid */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center bg-[#F8FAFC] p-5 rounded-xl border border-[#E2E8F0]">
        {/* Left Column: Big Average Star Score */}
        <div className="md:col-span-4 flex flex-col items-center justify-center text-center space-y-2 border-b md:border-b-0 md:border-r border-[#E2E8F0] pb-4 md:pb-0 md:pr-4">
          <span className="text-5xl font-black text-[#0F172A] tracking-tight">
            {avgRating > 0 ? avgRating.toFixed(1) : '—'}
          </span>
          <div className="flex items-center gap-1 text-amber-400">
            {[1, 2, 3, 4, 5].map((s) => (
              <Star
                key={s}
                className={`w-5 h-5 ${
                  s <= Math.round(avgRating) ? 'fill-amber-400 text-amber-400' : 'text-slate-300'
                }`}
              />
            ))}
          </div>
          <span className="text-xs font-semibold text-[#64748B]">
            Based on {totalRatings} {totalRatings === 1 ? 'reader rating' : 'reader ratings'}
          </span>
        </div>

        {/* Right Column: 5-to-1 Star Distribution Bars */}
        <div className="md:col-span-8 space-y-2 text-xs">
          {[5, 4, 3, 2, 1].map((stars) => {
            const count = distribution[stars.toString()] || 0;
            const percentage = totalRatings > 0 ? Math.round((count / totalRatings) * 100) : 0;
            return (
              <div key={stars} className="flex items-center gap-3">
                <span className="w-12 font-semibold text-[#475569] flex items-center gap-1 text-right justify-end">
                  {stars} <Star className="w-3 h-3 fill-amber-400 text-amber-400 inline" />
                </span>
                <div className="flex-1 h-2.5 rounded-full bg-slate-200 overflow-hidden">
                  <div
                    className="h-full bg-[#2563EB] rounded-full transition-all duration-500"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
                <span className="w-10 text-[11px] font-medium text-[#64748B] text-right">
                  {count}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Rating & Review Submission Form */}
      <form onSubmit={handleSubmit} className="bg-white border border-[#E2E8F0] p-5 rounded-xl space-y-4 shadow-sm">
        <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3">
          <span className="font-extrabold text-sm text-[#0F172A]">
            {editingReviewId
              ? 'Edit Your Review'
              : summary?.user_review
              ? 'Update Your Rating & Review'
              : targetTitle
              ? `Rate & Review "${targetTitle}"`
              : 'Rate this Article & Leave a Review'}
          </span>
          {editingReviewId && (
            <button
              type="button"
              onClick={() => setEditingReviewId(null)}
              className="text-xs font-semibold text-[#64748B] hover:text-[#0F172A]"
            >
              Cancel Edit
            </button>
          )}
        </div>

        {/* Interactive Star Picker */}
        <div className="space-y-1">
          <label className="block text-xs font-bold text-[#475569]">
            Your Rating (1 to 5 Stars):
          </label>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 cursor-pointer">
              {[1, 2, 3, 4, 5].map((s) => (
                <button
                  type="button"
                  key={s}
                  onClick={() => setRating(s)}
                  onMouseEnter={() => setHoverRating(s)}
                  onMouseLeave={() => setHoverRating(0)}
                  className="p-1 focus:outline-none focus:ring-2 focus:ring-[#2563EB] rounded"
                  title={`${s} Star${s > 1 ? 's' : ''}`}
                >
                  <Star
                    className={`w-6 h-6 transition-colors ${
                      (hoverRating || rating) >= s
                        ? 'fill-amber-400 text-amber-400 scale-110'
                        : 'text-slate-300'
                    }`}
                  />
                </button>
              ))}
            </div>
            <span className="text-xs font-bold text-[#2563EB] ml-2">
              {rating === 5 && '5/5 — Highly clear & useful'}
              {rating === 4 && '4/5 — Good reading experience'}
              {rating === 3 && '3/5 — Average clarity'}
              {rating === 2 && '2/5 — Needs more context'}
              {rating === 1 && '1/5 — Hard to follow'}
            </span>
          </div>
        </div>

        {/* Name and Text Fields */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="sm:col-span-1 space-y-1">
            <label className="block text-xs font-bold text-[#475569]">
              Your Display Name (Optional):
            </label>
            <input
              type="text"
              value={readerName}
              onChange={(e) => setReaderName(e.target.value)}
              placeholder="e.g. Reader Alex"
              maxLength={50}
              className="w-full px-3 py-2 text-xs rounded-lg border border-[#CBD5E1] focus:outline-none focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]"
            />
          </div>

          <div className="sm:col-span-2 space-y-1">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-bold text-[#475569]">
                Written Review (Optional):
              </label>
              <span className="text-[10px] text-[#64748B]">{reviewText.length}/1000</span>
            </div>
            <textarea
              value={reviewText}
              onChange={(e) => setReviewText(e.target.value)}
              rows={2}
              maxLength={1000}
              placeholder="Share what made this article informative, clear, or what background details were missing..."
              className="w-full px-3 py-2 text-xs rounded-lg border border-[#CBD5E1] focus:outline-none focus:border-[#2563EB] focus:ring-1 focus:ring-[#2563EB]"
            />
          </div>
        </div>

        {error && <p className="text-xs text-red-600 font-semibold">{error}</p>}
        {successMsg && (
          <p className="text-xs text-emerald-700 font-semibold flex items-center gap-1">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            {successMsg}
          </p>
        )}

        <div className="flex items-center justify-end gap-2 pt-2 border-t border-[#E2E8F0]">
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#2563EB] hover:bg-[#1D4ED8] disabled:bg-slate-300 text-white text-xs font-bold rounded-lg transition-colors shadow-sm"
          >
            <Send className="w-3.5 h-3.5" />
            <span>{submitting ? 'Submitting...' : editingReviewId ? 'Update Review' : summary?.user_review ? 'Update Feedback' : 'Submit Feedback'}</span>
          </button>
        </div>
      </form>

      {/* Reader Reviews List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-2">
          <h4 className="text-sm font-extrabold text-[#0F172A] tracking-tight">
            Community Comments ({summary?.reviews.length || 0})
          </h4>
          <span className="text-xs text-[#64748B]">Sorted by latest</span>
        </div>

        {loading ? (
          <div className="py-8 text-center text-xs text-[#64748B]">Loading reviews...</div>
        ) : !summary || summary.reviews.length === 0 ? (
          <div className="py-8 text-center rounded-xl bg-[#F8FAFC] border border-[#E2E8F0] space-y-1">
            <MessageSquare className="w-7 h-7 text-slate-400 mx-auto" />
            <p className="text-xs font-semibold text-[#0F172A]">No written reviews yet.</p>
            <p className="text-[11px] text-[#64748B]">Be the first reader to share your feedback above!</p>
          </div>
        ) : (
          <div className="space-y-3">
            {summary.reviews.map((rev) => {
              const isOwner = rev.reader_id === currentReaderId;
              return (
                <div
                  key={rev.id}
                  className={`p-4 rounded-xl border transition-all space-y-2 ${
                    isOwner
                      ? 'bg-[#EFF6FF]/40 border-[#60A5FA]/40'
                      : 'bg-white border-[#E2E8F0]'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-full bg-slate-200 text-[#475569] flex items-center justify-center font-bold text-xs">
                        <User className="w-3.5 h-3.5" />
                      </div>
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="text-xs font-bold text-[#0F172A]">{rev.reader_name}</span>
                          {isOwner && (
                            <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.2 bg-[#2563EB] text-white rounded">
                              You
                            </span>
                          )}
                        </div>
                        <span className="text-[10px] text-[#64748B] block" title={formatISTDateTime(rev.created_at)}>
                          {formatRelativeTime(rev.created_at)}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Star Rating Display */}
                      <div className="flex items-center gap-0.5 text-amber-400 bg-amber-50 px-2 py-0.5 rounded border border-amber-200/50">
                        <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                        <span className="text-xs font-bold text-amber-900">{rev.rating}/5</span>
                      </div>

                      {/* Author Edit/Delete Controls */}
                      {isOwner && (
                        <div className="flex items-center gap-1 ml-2">
                          <button
                            onClick={() => handleStartEdit(rev)}
                            className="p-1 rounded hover:bg-blue-100 text-[#2563EB] transition-colors"
                            title="Edit your review"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDelete(rev.id)}
                            className="p-1 rounded hover:bg-rose-100 text-rose-600 transition-colors"
                            title="Delete your review"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  {rev.review_text && (
                    <p className="text-xs text-[#334155] leading-relaxed pt-1 pl-9">
                      {rev.review_text}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
};
