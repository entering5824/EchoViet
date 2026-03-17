"""
Analytics: transcript viewer, export, statistics, keywords, summary, search, visualizations.
"""
import os
import sys
import json
import streamlit as st
import pandas as pd
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.components.layout import apply_custom_css, render_page_header
from app.components.footer import render_footer
from services.export_service import export_txt, export_docx, export_pdf, export_srt, export_vtt, export_json
from utils.metrics import compute_wer, compute_bleu
from core.nlp import keyword_extraction
from core import summarizer
from core.nlp.meeting_analysis import extract_action_items_rule_based, generate_meeting_summary_gemini

apply_custom_css()
st.set_page_config(page_title="Export & Analytics - Vietnamese Speech to Text", page_icon="📊", layout="wide")

for k, v in [
    ("transcript_text", ""),
    ("audio_info", None),
    ("transcript_segments", []),
    ("transcript_result", None),
]:
    st.session_state.setdefault(k, v)

render_page_header("Export & Analytics", "Xuất transcript, thống kê, keywords, tóm tắt và phân tích", "📊")

transcript = st.session_state.get("transcript_text") or ""
segments = st.session_state.get("transcript_segments") or []
audio_info = st.session_state.get("audio_info") or {}
duration = audio_info.get("duration") or 0

# Tab structure
tabs = ["📄 Transcript", "📤 Export", "📈 Thống kê", "🔑 Keywords", "📝 Tóm tắt", "🔍 Tìm kiếm", "📐 WER/BLEU", "ℹ️ Hệ thống"]
tab_transcript, tab_export, tab_stats, tab_keywords, tab_summary, tab_search, tab_metrics, tab_info = st.tabs(tabs)

# ---------- 1. Transcript Viewer với timestamp ----------
with tab_transcript:
    st.subheader("Transcript timeline")
    if transcript.strip() or segments:
        if segments:
            sub_mode = st.radio("Hiển thị", ["source", "translation", "dual"], horizontal=True, key="trans_timeline_mode")
            has_trans = any(s.get("translated_text") for s in segments)
            has_conf = any(s.get("confidence_asr") is not None for s in segments)
            for seg in segments:
                start = seg.get("start", 0)
                end = seg.get("end", 0)
                text = (seg.get("text") or "").strip()
                trans = (seg.get("translated_text") or "").strip()
                speaker = seg.get("speaker", "")
                conf = seg.get("confidence_asr")
                time_str = f"[{start:.2f}s - {end:.2f}s]"
                if speaker:
                    time_str += f" Speaker {speaker}"
                line = f"{time_str} {text}"
                if sub_mode == "translation" and trans:
                    line = f"{time_str} {trans}"
                elif sub_mode == "dual" and trans:
                    line = f"{time_str} {text}\n  → {trans}"
                if has_conf and conf is not None:
                    line += f" (conf: {conf:.2f})"
                st.text(line)
        else:
            st.text(transcript)
    else:
        st.info("Chưa có transcript. Chạy Transcription trước.")

# ---------- 2–4. Export (incl. JSON) ----------
with tab_export:
    if transcript.strip():
        st.subheader("Xuất file")
        meta = {
            "duration": duration,
            "word_count": len(transcript.split()),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            data, fname = export_txt(transcript, "transcript.txt")
            st.download_button("Tải TXT", data, file_name=fname, mime="text/plain")
        with col2:
            data, fname = export_docx(transcript, meta, "transcript.docx")
            st.download_button("Tải DOCX", data, file_name=fname, mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with col3:
            data, fname = export_pdf(transcript, meta, "transcript.pdf")
            st.download_button("Tải PDF", data, file_name=fname, mime="application/pdf")
        with col4:
            meta["segments_count"] = len(segments)
            data, fname = export_json(segments, transcript, meta, "transcript.json")
            st.download_button("Tải JSON", data, file_name=fname, mime="application/json", key="dl_json")
        if segments:
            st.subheader("Subtitle")
            dual = bool(segments and segments[0].get("translated_text"))
            c1, c2 = st.columns(2)
            with c1:
                srt_data, srt_name = export_srt(segments, "subtitles.srt", dual=dual)
                st.download_button("Tải SRT", srt_data, file_name=srt_name, mime="text/plain", key="dl_srt")
            with c2:
                vtt_data, vtt_name = export_vtt(segments, "subtitles.vtt", dual=dual)
                st.download_button("Tải VTT", vtt_data, file_name=vtt_name, mime="text/vtt", key="dl_vtt")
    else:
        st.info("Chưa có transcript. Chạy Transcription trước.")

# ---------- 3–4. Thống kê (words, sentences, duration, WPM, segment stats) ----------
with tab_stats:
    if transcript.strip():
        words = len(transcript.split())
        sents = max(1, transcript.count(".") + transcript.count("!") + transcript.count("?"))
        wpm = (words / (duration / 60.0)) if duration > 0 else 0
        st.metric("Số từ", words)
        st.metric("Số câu (ước lượng)", sents)
        st.metric("Thời lượng (s)", f"{duration:.1f}")
        st.metric("Từ/phút", f"{wpm:.1f}")

        seg_durations = []
        if segments:
            st.subheader("Segment statistics")
            seg_count = len(segments)
            words_per_seg = words / seg_count if seg_count > 0 else 0
            seg_durations = [(s.get("end", 0) - s.get("start", 0)) for s in segments if "start" in s and "end" in s]
            avg_seg_dur = sum(seg_durations) / len(seg_durations) if seg_durations else 0
            longest_seg = max(seg_durations) if seg_durations else 0
            st.metric("Số segment", seg_count)
            st.metric("Trung bình từ/segment", f"{words_per_seg:.1f}")
            st.metric("Segment dài nhất (s)", f"{longest_seg:.1f}")

        # Confidence statistics (nếu có)
        if segments:
            confs = [s.get("confidence_asr") for s in segments if s.get("confidence_asr") is not None]
            if confs:
                st.subheader("Confidence statistics")
                avg_conf = sum(confs) / len(confs)
                min_conf = min(confs)
                worst_idx = confs.index(min_conf)
                st.metric("Trung bình confidence", f"{avg_conf:.2f}")
                st.metric("Segment có confidence thấp nhất", f"{min_conf:.2f}")
                if worst_idx < len(segments):
                    st.caption(f"Segment: {segments[worst_idx].get('text', '')[:80]}...")

        # Segment duration histogram
        if segments and seg_durations:
            st.subheader("Độ dài segment (giây)")
            df_dur = pd.DataFrame({"Segment": range(1, len(seg_durations) + 1), "Giây": seg_durations})
            st.bar_chart(df_dur.set_index("Segment"))

        # Speaking rate distribution (WPM per segment)
        if segments and seg_durations:
            st.subheader("Speaking rate per segment (từ/phút)")
            seg_wpms = []
            for s in segments:
                start, end = s.get("start", 0), s.get("end", 0)
                dur = end - start
                txt = (s.get("text") or "").strip()
                w = len(txt.split())
                wp = (w / (dur / 60.0)) if dur > 0 else 0
                seg_wpms.append(wp)
            if seg_wpms:
                df = pd.DataFrame({"Segment": range(1, len(seg_wpms) + 1), "WPM": seg_wpms})
                st.bar_chart(df.set_index("Segment"))

        # Word frequency chart
        st.subheader("Tần suất từ")
        try:
            kw_with_count = keyword_extraction.extract_keywords(transcript, top_k=15, return_with_counts=True)
            if kw_with_count:
                df_w = pd.DataFrame(kw_with_count, columns=["Từ", "Số lần"])
                st.bar_chart(df_w.set_index("Từ"))
        except Exception:
            pass
    else:
        st.info("Chưa có transcript.")

# ---------- 5. Keywords ----------
with tab_keywords:
    if transcript.strip():
        st.subheader("Top keywords")
        method = st.radio("Phương pháp", ["Word frequency", "TF-IDF"], horizontal=True, key="kw_method")
        top_k = st.slider("Số keywords", 5, 30, 10, key="kw_topk")
        if method == "TF-IDF":
            try:
                kws = keyword_extraction.extract_keywords_tfidf(transcript, top_k=top_k)
                for w, score in kws:
                    st.write(f"- **{w}** ({score:.2f})")
            except Exception:
                kws = keyword_extraction.extract_keywords(transcript, top_k=top_k)
                for w in kws:
                    st.write(f"- {w}")
        else:
            kws = keyword_extraction.extract_keywords(transcript, top_k=top_k)
            for w in kws:
                st.write(f"- {w}")
    else:
        st.info("Chưa có transcript.")

# ---------- 6. Summary ----------
with tab_summary:
    if transcript.strip():
        st.subheader("Meeting Summary")
        use_gemini = st.checkbox("Dùng Gemini AI (cần API key)", value=False, key="use_gemini_sum")
        if use_gemini:
            if st.button("Tạo tóm tắt", key="btn_summary"):
                with st.spinner("Đang tóm tắt..."):
                    summary = generate_meeting_summary_gemini(transcript)
                    if summary:
                        st.markdown(summary)
                    else:
                        st.warning("Không thể tạo tóm tắt (kiểm tra GEMINI_API_KEY).")
        else:
            summary = summarizer.simple_summarize(transcript, max_sentences=5)
            st.markdown(summary)

        st.subheader("Action items")
        actions = extract_action_items_rule_based(transcript)
        if actions:
            for a in actions:
                st.write(f"- {a}")
        else:
            st.caption("Không tìm thấy action item (rule-based). Thử bật Gemini để có kết quả tốt hơn.")
    else:
        st.info("Chưa có transcript.")

# ---------- 7. Search transcript ----------
with tab_search:
    if transcript.strip() or segments:
        kw = st.text_input("Tìm kiếm trong transcript", key="search_kw")
        if kw and kw.strip():
            kw_lower = kw.strip().lower()
            found = []
            if segments:
                for i, seg in enumerate(segments):
                    txt = (seg.get("text") or "").strip()
                    if kw_lower in txt.lower():
                        found.append((seg.get("start", 0), seg.get("end", 0), txt))
            if found:
                for start, end, txt in found:
                    st.write(f"**[{start:.2f}s - {end:.2f}s]** {txt}")
            elif transcript and kw_lower in transcript.lower():
                # Fallback: hiển thị đoạn chứa từ khóa
                parts = transcript.replace("\n", " ").split()
                for j, p in enumerate(parts):
                    if kw_lower in p.lower():
                        ctx = " ".join(parts[max(0, j - 3) : j + 4])
                        st.write(ctx)
                        break
                else:
                    st.write(transcript)
            else:
                st.info(f"Không tìm thấy '{kw}'.")
        else:
            st.caption("Nhập từ khóa để tìm kiếm.")
    else:
        st.info("Chưa có transcript.")

# ---------- 8. WER/BLEU ----------
with tab_metrics:
    st.subheader("WER & BLEU")
    st.caption("So sánh reference (bản chuẩn) với hypothesis (output ASR hoặc dịch).")
    ref = st.text_area("Reference (bản chuẩn)", height=100, key="ref_metric")
    hyp = st.text_area("Hypothesis (output cần đánh giá)", height=100, key="hyp_metric")
    if st.button("Tính WER & BLEU", key="btn_metric"):
        if ref.strip() and hyp.strip():
            wer = compute_wer(ref, hyp)
            bleu = compute_bleu(ref, hyp)
            st.metric("WER (Word Error Rate)", f"{wer:.4f}")
            st.metric("BLEU", f"{bleu:.2f}")
        else:
            st.warning("Nhập cả reference và hypothesis.")

# ---------- 9. Info ----------
with tab_info:
    st.caption("Model: Whisper, Distil-Whisper, Parakeet, Moonshine. Dịch: NLLB, SeamlessM4T, M2M100.")
    try:
        from services.audio_service import get_ffmpeg_info
        ok, msg = get_ffmpeg_info()
        st.write("FFmpeg:", msg)
    except Exception:
        st.write("FFmpeg: N/A")

render_footer()
