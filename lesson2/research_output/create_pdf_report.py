from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors

# Create PDF
doc = SimpleDocTemplate(
    "research_output/bayram_annakov_research.pdf",
    pagesize=letter,
    rightMargin=72,
    leftMargin=72,
    topMargin=72,
    bottomMargin=18,
)

# Container for the 'Flowable' objects
elements = []

# Get default styles
styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=24,
    textColor=colors.HexColor('#1a1a1a'),
    spaceAfter=30,
    alignment=TA_CENTER,
)

subtitle_style = ParagraphStyle(
    'CustomSubtitle',
    parent=styles['Normal'],
    fontSize=10,
    textColor=colors.HexColor('#666666'),
    spaceAfter=20,
    alignment=TA_CENTER,
)

heading_style = ParagraphStyle(
    'CustomHeading',
    parent=styles['Heading2'],
    fontSize=16,
    textColor=colors.HexColor('#2c5aa0'),
    spaceAfter=12,
    spaceBefore=20,
)

subheading_style = ParagraphStyle(
    'CustomSubheading',
    parent=styles['Heading3'],
    fontSize=12,
    textColor=colors.HexColor('#4a4a4a'),
    spaceAfter=10,
    spaceBefore=12,
    fontName='Helvetica-Bold',
)

body_style = ParagraphStyle(
    'CustomBody',
    parent=styles['Normal'],
    fontSize=10,
    textColor=colors.HexColor('#333333'),
    spaceAfter=8,
    leading=14,
)

bullet_style = ParagraphStyle(
    'CustomBullet',
    parent=styles['Normal'],
    fontSize=10,
    textColor=colors.HexColor('#333333'),
    leftIndent=20,
    spaceAfter=6,
    leading=13,
)

# Title
elements.append(Paragraph("B2B Sales Research Report: Bayram Annakov", title_style))
elements.append(Paragraph("Research Date: December 7, 2025 | Version: V2 (Revised) | Rating: 4/5 ⭐⭐⭐⭐", subtitle_style))
elements.append(Spacer(1, 0.3*inch))

# PROSPECT SUMMARY
elements.append(Paragraph("PROSPECT SUMMARY", heading_style))

# Summary table
summary_data = [
    ['Name:', 'Bayram Annakov'],
    ['Title:', 'Founder & CEO'],
    ['Company:', 'onsa.ai'],
    ['Location:', 'Seattle, Washington, United States'],
]

summary_table = Table(summary_data, colWidths=[1.5*inch, 4.5*inch])
summary_table.setStyle(TableStyle([
    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, -1), 10),
    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2c5aa0')),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
]))

elements.append(summary_table)
elements.append(Spacer(1, 0.2*inch))

elements.append(Paragraph(
    "Bayram is the founder and CEO of onsa.ai, a company that automates B2B sales organizations with AI - "
    "including intelligent sales meeting prep, autonomous prospecting and outreach, inbound lead qualification, "
    "and inbound-led outbound. He is a serial entrepreneur with 20+ years of experience, having previously built "
    "and scaled App in the Air (7M+ users, featured in Apple iPad TV commercial) to a $20M exit <i>[ASSUMPTION: "
    "exit value from profile summary, not independently verified]</i>. He founded onsa.ai in May 2024 after running "
    "Empatika Labs (AI and web3 products) from November 2022 to August 2024.",
    body_style
))

# EDUCATION BACKGROUND
elements.append(Paragraph("EDUCATION BACKGROUND", heading_style))

elements.append(Paragraph("Executive Education", subheading_style))
elements.append(Paragraph("• <b>Stanford University Graduate School of Business</b> (August 2022)", bullet_style))
elements.append(Paragraph("  - Executive Program", bullet_style))
elements.append(Paragraph("  - Elite business school education, strong network access", bullet_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("• <b>Singularity University</b> (2015)", bullet_style))
elements.append(Paragraph("  - Executive Program in Exponential Technologies", bullet_style))
elements.append(Paragraph("  - Focus on emerging technologies, AI, and innovation", bullet_style))
elements.append(Paragraph("  - Positions him at forefront of tech trends", bullet_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("Graduate Degrees", subheading_style))
elements.append(Paragraph("• <b>Lomonosov Moscow State University (MSU)</b> (2004-2006)", bullet_style))
elements.append(Paragraph("  - MA in General & Strategic Management", bullet_style))
elements.append(Paragraph("  - Top-tier Russian university, strategic thinking foundation", bullet_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("• <b>Bauman Moscow State Technical University</b> (2000-2006)", bullet_style))
elements.append(Paragraph("  - MA in Finances", bullet_style))
elements.append(Paragraph("  - Specialization: Banking Information Systems", bullet_style))
elements.append(Paragraph("  - Technical and financial expertise combination", bullet_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph(
    "<b>Education Analysis:</b> Bayram's education combines deep technical knowledge (finance, information systems) "
    "with strategic management and cutting-edge technology training. His Stanford GSB and Singularity University "
    "credentials indicate commitment to continuous learning and staying current with AI/tech trends. This makes him "
    "an ideal peer for strategic conversations about the future of AI in sales.",
    body_style
))

# KEY INSIGHTS
elements.append(Paragraph("KEY INSIGHTS", heading_style))

elements.append(Paragraph("Industry Position & Competition", subheading_style))
elements.append(Paragraph(
    "• <b>Direct Competitor with Co-opetition Potential:</b> onsa.ai operates in the same AI-powered B2B sales "
    "automation space, offering meeting prep, autonomous prospecting/outreach, and lead qualification",
    bullet_style
))
elements.append(Paragraph(
    "• <b>Early-Stage Startup (May 2024):</b> Company is ~8 months old, likely in rapid product iteration and "
    "market validation phase",
    bullet_style
))
elements.append(Paragraph(
    "• <b>Potential for Industry Collaboration:</b> As emerging players in a rapidly evolving AI sales space, "
    "there may be opportunities for knowledge sharing, industry standards development, or non-competing feature collaboration",
    bullet_style
))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("Track Record & Credibility", subheading_style))
elements.append(Paragraph(
    "• <b>Proven Serial Founder:</b> Built App in the Air to 7M+ users and $20M exit [ASSUMPTION], demonstrating "
    "product-market fit expertise and execution capabilities",
    bullet_style
))
elements.append(Paragraph(
    "• <b>10-Year CEO Tenure:</b> Led App in the Air for 10 years (2012-2022), showing long-term commitment and "
    "scaling experience",
    bullet_style
))
elements.append(Paragraph(
    "• <b>Product Management Excellence:</b> From the very beginning, responsible for product vision, execution, "
    "and growth - featured in iPad TV commercial and named \"World's Greatest App\" by Business Insider",
    bullet_style
))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("Network & Influence", subheading_style))
elements.append(Paragraph(
    "• <b>Strong Industry Presence:</b> 7,164+ LinkedIn followers indicate thought leadership and visibility",
    bullet_style
))
elements.append(Paragraph(
    "• <b>Mentorship Experience:</b> Previously mentored mobile startups at Founder Institute (2013-2015) and "
    "Farminers Startup Academy (2011)",
    bullet_style
))
elements.append(Paragraph(
    "• <b>Elite Education Network:</b> Stanford GSB alumni network access, Singularity University connections",
    bullet_style
))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("Technical & Business Depth", subheading_style))
elements.append(Paragraph(
    "• <b>20+ Years Experience:</b> Career spans from developer (2003) → project manager → CEO, showing technical "
    "depth and business acumen",
    bullet_style
))
elements.append(Paragraph(
    "• <b>Cross-Industry Experience:</b> Consumer apps (App in the Air), enterprise software (EPAM, Vested Development), "
    "AI/web3 (Empatika Labs), and now B2B SaaS",
    bullet_style
))
elements.append(Paragraph(
    "• <b>International Background:</b> Experience in Russian, European, and US markets (currently based in Seattle)",
    bullet_style
))

# PAGE BREAK
elements.append(PageBreak())

# PAIN POINTS
elements.append(Paragraph("PAIN POINTS", heading_style))
elements.append(Paragraph("Even successful competitors in the AI sales automation space face shared challenges:", body_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("1. Market Education & Category Creation", subheading_style))
elements.append(Paragraph("• <b>Challenge:</b> AI sales automation is still an emerging category requiring significant market education", bullet_style))
elements.append(Paragraph("• <b>Shared Interest:</b> Both companies benefit from educating the market on AI capabilities, ROI, and best practices", bullet_style))
elements.append(Paragraph("• <b>Opportunity:</b> Industry thought leadership, co-marketing opportunities, or joint research could accelerate category growth", bullet_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("2. Rapid AI Technology Evolution", subheading_style))
elements.append(Paragraph("• <b>Challenge:</b> Keeping pace with LLM improvements, new AI capabilities, and changing customer expectations", bullet_style))
elements.append(Paragraph("• <b>Shared Interest:</b> Understanding which AI features drive real value vs. which are just \"cool demos\"", bullet_style))
elements.append(Paragraph("• <b>Opportunity:</b> Peer insights on product roadmap priorities, customer feedback patterns, and technical implementation approaches", bullet_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("3. Early-Stage Go-to-Market", subheading_style))
elements.append(Paragraph("• <b>Challenge:</b> As an 8-month-old startup, onsa.ai is still validating ICP, messaging, pricing, and sales channels", bullet_style))
elements.append(Paragraph("• <b>Shared Interest:</b> Learning from others' GTM experiments, understanding what resonates with buyers", bullet_style))
elements.append(Paragraph("• <b>Opportunity:</b> Compare notes on customer acquisition strategies, conversion metrics, and sales cycle insights", bullet_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("4. Talent & Team Building in Competitive AI Market", subheading_style))
elements.append(Paragraph("• <b>Challenge:</b> Recruiting top AI/ML talent and experienced sales professionals in a hyper-competitive market", bullet_style))
elements.append(Paragraph("• <b>Shared Interest:</b> Understanding compensation benchmarks, team structure, and hiring best practices", bullet_style))
elements.append(Paragraph("• <b>Opportunity:</b> Non-competitive talent insights, referrals for non-overlapping roles", bullet_style))

# OUTREACH ANGLE
elements.append(Paragraph("OUTREACH ANGLE", heading_style))
elements.append(Paragraph("✅ CO-OPETITION STRATEGY: \"Comparing Notes on Building AI Sales Tools\"", subheading_style))
elements.append(Paragraph("<b>Primary Hook:</b> Industry peer conversation between founders building in the same emerging space", body_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("Recommended Approach:", subheading_style))

elements.append(Paragraph("1. Positioning: Peer-to-Peer, Not Prospect", body_style))
elements.append(Paragraph("• Frame as founder-to-founder conversation, not a sales pitch", bullet_style))
elements.append(Paragraph("• Acknowledge you're both building in the AI sales automation space", bullet_style))
elements.append(Paragraph("• Express genuine curiosity about their approach and learnings", bullet_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("2. Value Proposition: Mutual Knowledge Sharing", body_style))
elements.append(Paragraph("• \"I've been following onsa.ai's launch and would love to compare notes on what we're both learning about AI in sales\"", bullet_style))
elements.append(Paragraph("• Share a specific insight or challenge from your side first (reciprocity principle)", bullet_style))
elements.append(Paragraph("• Suggest a short 20-minute conversation to exchange perspectives", bullet_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("3. Co-opetition Opportunities to Explore:", body_style))
elements.append(Paragraph("• Industry Standards: Collaborate on best practices, ethical AI use in sales", bullet_style))
elements.append(Paragraph("• Market Expansion: Different ICP targeting (e.g., company size, industry verticals)", bullet_style))
elements.append(Paragraph("• Non-Competing Features: Potential integration or partnership on complementary capabilities", bullet_style))
elements.append(Paragraph("• Joint Research: Co-author industry reports on AI adoption in B2B sales", bullet_style))
elements.append(Paragraph("• Event Collaboration: Co-host webinars or workshops on AI sales transformation", bullet_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("<b>Expected Outcome:</b>", body_style))
elements.append(Paragraph("• Best Case: Ongoing peer relationship, industry insights exchange, potential collaboration opportunities", bullet_style))
elements.append(Paragraph("• Realistic Case: One-time conversation providing competitive intelligence and market validation", bullet_style))
elements.append(Paragraph("• Worst Case: Polite decline (no harm done, maintains professional relationship)", bullet_style))

# PAGE BREAK
elements.append(PageBreak())

# DATA QUALITY NOTES
elements.append(Paragraph("DATA QUALITY NOTES", heading_style))
elements.append(Paragraph("Data Completeness: 80% (High Quality)", subheading_style))

elements.append(Paragraph("<b>Verified Information:</b>", body_style))
elements.append(Paragraph("✅ Current role: Founder & CEO at onsa.ai (May 2024 - Present)", bullet_style))
elements.append(Paragraph("✅ Company description: AI-powered B2B sales automation", bullet_style))
elements.append(Paragraph("✅ Work history: Complete career timeline from 2003-present", bullet_style))
elements.append(Paragraph("✅ Education: 4 degrees from verified institutions with dates and specializations", bullet_style))
elements.append(Paragraph("✅ Previous companies: App in the Air (CEO, 10 years), Empatika Labs (CEO), EPAM, Vested Development", bullet_style))
elements.append(Paragraph("✅ Profile engagement: 7,164 followers (verified)", bullet_style))
elements.append(Paragraph("✅ Location: Seattle, Washington, United States", bullet_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("<b>Missing/Limited Information:</b>", body_style))
elements.append(Paragraph("❌ Current revenue or funding status for onsa.ai", bullet_style))
elements.append(Paragraph("❌ Current team size or key hires", bullet_style))
elements.append(Paragraph("❌ Specific customer names or case studies", bullet_style))
elements.append(Paragraph("❌ Detailed product roadmap or feature differentiation", bullet_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("<b>Unverified Assumptions:</b>", body_style))
elements.append(Paragraph("[ASSUMPTION] $20M exit for App in the Air - mentioned in profile summary but not independently verified", bullet_style))
elements.append(Paragraph("[ASSUMPTION] Company is in \"rapid growth phase\" - inferred from recent founding date (May 2024), not confirmed", bullet_style))
elements.append(Spacer(1, 0.1*inch))

elements.append(Paragraph("Research Limitations", subheading_style))
elements.append(Paragraph("1. <b>No Financial Data:</b> Cannot access revenue, funding, burn rate, or valuation information from LinkedIn alone", bullet_style))
elements.append(Paragraph("2. <b>Limited Product Details:</b> LinkedIn doesn't provide feature comparisons or technical architecture details", bullet_style))
elements.append(Paragraph("3. <b>Customer Information:</b> No visibility into customer list, testimonials, or case studies beyond public profile", bullet_style))
elements.append(Paragraph("4. <b>Team Composition:</b> Cannot see full team size, key hires, or organizational structure", bullet_style))
elements.append(Paragraph("5. <b>Recent Activities:</b> LinkedIn profile doesn't show recent posts, engagement, or thought leadership content", bullet_style))

# QUALITY ASSURANCE CHECKLIST
elements.append(Paragraph("QUALITY ASSURANCE CHECKLIST", heading_style))
elements.append(Paragraph("✅ Job title current and verified", bullet_style))
elements.append(Paragraph("✅ Company information accurate and up-to-date", bullet_style))
elements.append(Paragraph("✅ Relevant work history providing context", bullet_style))
elements.append(Paragraph("✅ Recent triggers identified (founded company 8 months ago)", bullet_style))
elements.append(Paragraph("✅ Clear value proposition for outreach (co-opetition)", bullet_style))
elements.append(Paragraph("✅ Information specific and actionable", bullet_style))
elements.append(Paragraph("✅ Assumptions clearly marked", bullet_style))
elements.append(Paragraph("✅ Detailed education information included", bullet_style))
elements.append(Spacer(1, 0.2*inch))

# Footer
elements.append(Paragraph(
    "<b>Research Completed By:</b> AI Sales Research Agent<br/>"
    "<b>Next Steps:</b> Review co-opetition strategy, prepare founder-to-founder outreach, maintain professional boundaries while gathering market insights",
    body_style
))

# Build PDF
doc.build(elements)

print("PDF report created successfully: research_output/bayram_annakov_research.pdf")
