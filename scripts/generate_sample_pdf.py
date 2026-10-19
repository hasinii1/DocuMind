import fitz  # PyMuPDF
from pathlib import Path

def create_sample_pdf(output_path: str = "sample_corporate_report.pdf"):
    doc = fitz.open()

    # Page 1: Executive Summary
    page1 = doc.new_page()
    page1.insert_text(
        (50, 70),
        "DOCUMIND ENTERPRISE REPORT: Q3 OPERATIONAL REVIEW",
        fontsize=16,
        fontname="helv",
        fontfile=None,
    )
    page1.insert_text(
        (50, 110),
        "1. Executive Summary\n\n"
        "Project DocuMind represents a modern multimodal document intelligence platform designed\n"
        "to deliver strict factual grounding across complex corporate documents. Unlike traditional\n"
        "unconstrained chatbots, DocuMind enforces page-level citation verification, Reciprocal Rank\n"
        "Fusion (RRF) between lexical and vector indices, and cross-encoder reranking.\n\n"
        "Key Deliverables for Q3:\n"
        "- Ingestion of layout-aware document elements including prose, headings, and tables.\n"
        "- Automated abstention when the underlying source corpus lacks sufficient supporting facts.\n"
        "- Deterministic semantic diffing between versioned agreements and financial reports.\n",
        fontsize=11,
    )

    # Page 2: Milestones & Delivery
    page2 = doc.new_page()
    page2.insert_text((50, 70), "2. Technical Milestones & Architecture", fontsize=14)
    page2.insert_text(
        (50, 110),
        "Milestone 4 delivery in Q4 directly incorporates the revised SOC2 Type II compliance criteria\n"
        "and quarterly penetration testing requirements. System authorization enforces workspace-level\n"
        "isolation, ensuring that no tenant or unauthorized user can query or retrieve document chunks\n"
        "belonging to another workspace.\n\n"
        "Indirect prompt injection defenses sanitize all untrusted text fragments before presentation\n"
        "to the answer generation models.",
        fontsize=11,
    )

    # Page 3: Operating Costs Breakdown
    page3 = doc.new_page()
    page3.insert_text((50, 70), "3. Operating Costs & Financial Variance", fontsize=14)
    page3.insert_text(
        (50, 110),
        "During the recent fiscal period, total operating costs experienced an increase of 28% year-over-year.\n\n"
        "The three main causes of the reported increase in operating costs were:\n"
        "1. Cloud infrastructure expansion across distributed vector databases and GPU clusters.\n"
        "2. Third-party software licensing fees associated with enterprise OCR models.\n"
        "3. Specialized engineering headcount growth in AI systems engineering and data security.\n\n"
        "Evidence indicates that cloud infrastructure alone contributed $230,000 to the net quarterly variance.",
        fontsize=11,
    )

    # Page 4: Financial Summary Table
    page4 = doc.new_page()
    page4.insert_text((50, 70), "4. Financial Summary Table", fontsize=14)
    table_text = (
        "| Quarter | Total Revenue | Operating Costs | Cloud Spend | Net Income |\n"
        "| Q1 2026 | $1,200,000    | $450,000        | $120,000    | $750,000   |\n"
        "| Q2 2026 | $1,350,000    | $520,000        | $160,000    | $830,000   |\n"
        "| Q3 2026 | $1,450,000    | $680,000        | $230,000    | $770,000   |\n"
    )
    page4.insert_text((50, 110), table_text, fontsize=10)

    # Save to disk
    out_p = Path(output_path)
    doc.save(str(out_p))
    doc.close()
    print(f"Sample PDF created successfully at: {out_p.resolve()}")

if __name__ == "__main__":
    create_sample_pdf()
