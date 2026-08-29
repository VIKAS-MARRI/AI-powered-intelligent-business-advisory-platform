"""
Seed script for Phase 6 Government Scheme Intelligence.

Seeds the database with curated Indian government scheme records.

DATA INTEGRITY POLICY:
  - data_status = "verified"  → sourced from official government publications
  - data_status = "demo"      → illustrative / representative data

All verified records include official_url pointing to official government portals.
Scheme details (loan amounts, subsidies, eligibility) are subject to change;
users MUST verify current requirements through official sources before applying.

Run with:
    python -m app.seed_schemes
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.db import AsyncSessionLocal, engine, Base
from app.models.scheme import Scheme


# ── Scheme seed data ──────────────────────────────────────────────────────────
# Each entry maps directly to Scheme model fields.
# JSON-list fields (eligibility_requirements, required_documents, application_steps)
# are stored as JSON strings.

SCHEMES: list[dict] = [
    # ─────────────────────────────────────────────────────────────────────────
    # 1. PMEGP — Prime Minister's Employment Generation Programme
    # Source: https://www.kviconline.gov.in/pmegpeportal/
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name": "Prime Minister's Employment Generation Programme (PMEGP)",
        "slug": "pmegp",
        "short_description": (
            "A credit-linked subsidy programme administered by KVIC to generate "
            "self-employment through setting up micro-enterprises in non-farm sectors."
        ),
        "full_description": (
            "PMEGP is a central sector scheme for generation of employment opportunities "
            "through establishment of micro enterprises in rural and urban areas. "
            "Projects with maximum cost of ₹50 lakh in manufacturing and ₹20 lakh in "
            "service sector are eligible. The subsidy is 15–35% of the project cost "
            "depending on location and beneficiary category."
        ),
        "category": "Mixed",
        "sector": "General",
        "target_beneficiaries": "Individuals above 18 years, Self Help Groups, Institutions, Co-operative Societies, Charitable Trusts",
        "location_scope": "National",
        "states": "All",
        "business_categories": (
            "tailoring,clothing,dairy,food processing,bakery,kirana,grocery,retail,"
            "agriculture,handicraft,pottery,beauty,electronics,hardware,manufacturing,"
            "services,tea,snacks,medical,education,coaching"
        ),
        "business_tags": "shop,craft,amenity,office",
        "minimum_age": 18,
        "maximum_age": None,
        "minimum_investment": 10000,
        "maximum_investment": 5000000,
        "maximum_loan_amount": 5000000,
        "maximum_subsidy_amount": 1750000,
        "subsidy_percentage": 35,
        "key_benefit": "Subsidy of 15–35% of project cost (up to ₹50L for manufacturing, ₹20L for services)",
        "eligibility_requirements": json.dumps([
            "Age: 18 years or above",
            "Educational qualification: 8th pass for projects above ₹10 lakh",
            "No income ceiling for assistance under PMEGP",
            "Existing units and units that have availed government subsidy are not eligible",
            "Beneficiary must contribute 5–10% of the project cost as margin money",
            "One beneficiary per family is eligible",
        ]),
        "required_documents": json.dumps([
            "Aadhaar card",
            "PAN card",
            "Educational qualification certificates",
            "Project report / business plan",
            "Proof of special category (SC/ST/OBC/women/ex-serviceman etc.) if applicable",
            "Photograph",
            "Bank account details",
        ]),
        "application_steps": json.dumps([
            "Visit the PMEGP e-Portal: kviconline.gov.in/pmegpeportal",
            "Register and fill the online application form",
            "Upload required documents",
            "Application is forwarded to District Industries Centre (DIC) or KVIC/KVIB",
            "Interview and selection by Task Force Committee",
            "Bank sanction of loan",
            "Training (EDP) completion",
            "Subsidy disbursement by bank",
        ]),
        "is_women_specific": False,
        "is_sc_st_specific": False,
        "is_rural_specific": False,
        "is_youth_specific": False,
        "official_source": "Khadi and Village Industries Commission (KVIC), Ministry of MSME",
        "official_url": "https://www.kviconline.gov.in/pmegpeportal/",
        "data_status": "verified",
        "last_reviewed": "2024-08",
        "sort_order": 1,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 2. MUDRA — Micro Units Development and Refinance Agency
    # Source: https://www.mudra.org.in/
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name": "MUDRA Loan — Pradhan Mantri MUDRA Yojana (PMMY)",
        "slug": "mudra-pmmy",
        "short_description": (
            "Provides loans up to ₹20 lakh to non-corporate, non-farm small/micro "
            "enterprises through banks, MFIs, and NBFCs under three tiers: "
            "Shishu, Kishore, and Tarun."
        ),
        "full_description": (
            "PMMY provides financial support to non-corporate, non-farm small/micro "
            "enterprises. Three loan categories: Shishu (up to ₹50,000), "
            "Kishore (₹50,001–₹5 lakh), Tarun (₹5 lakh–₹10 lakh). "
            "Tarun Plus (up to ₹20 lakh) is for eligible borrowers. "
            "No collateral required. Interest rates as per lending institution guidelines."
        ),
        "category": "Loan",
        "sector": "General",
        "target_beneficiaries": "Non-corporate, non-farm micro and small enterprises, individuals, proprietorships, partnerships",
        "location_scope": "National",
        "states": "All",
        "business_categories": (
            "tailoring,clothing,dairy,food processing,bakery,kirana,grocery,retail,"
            "agriculture,handicraft,beauty,electronics,hardware,manufacturing,services,"
            "tea,snacks,transport,poultry,fishery,vegetable,fruit"
        ),
        "business_tags": "shop,craft,amenity,office",
        "minimum_age": 18,
        "maximum_age": None,
        "minimum_investment": 1000,
        "maximum_investment": 2000000,
        "maximum_loan_amount": 2000000,
        "maximum_subsidy_amount": None,
        "subsidy_percentage": None,
        "key_benefit": "Collateral-free business loans from ₹10K to ₹20 lakh under Shishu/Kishore/Tarun/Tarun Plus",
        "eligibility_requirements": json.dumps([
            "Non-corporate, non-farm micro/small enterprise or individual entrepreneur",
            "Viable business plan or existing income-generating activity",
            "Good credit history with the lending institution",
            "No upper income limit specified",
            "Loan available for manufacturing, trading, and service sector activities",
        ]),
        "required_documents": json.dumps([
            "Aadhaar card / Voter ID / Passport / Driving Licence",
            "PAN card",
            "Proof of residence",
            "Business proof / registration documents (if applicable)",
            "Quotation for machinery/equipment (if applicable)",
            "Passport-size photographs",
            "Bank statement (last 6 months, for Kishore and Tarun)",
        ]),
        "application_steps": json.dumps([
            "Approach any MUDRA-linked bank, NBFC, or MFI",
            "Fill the loan application form",
            "Submit required documents",
            "Bank evaluates the application",
            "Loan is sanctioned and disbursed",
            "A MUDRA Card (RuPay debit card) may be issued for working capital",
        ]),
        "is_women_specific": False,
        "is_sc_st_specific": False,
        "is_rural_specific": False,
        "is_youth_specific": False,
        "official_source": "MUDRA (Micro Units Development & Refinance Agency Ltd.), Ministry of Finance",
        "official_url": "https://www.mudra.org.in/",
        "data_status": "verified",
        "last_reviewed": "2024-08",
        "sort_order": 2,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Stand-Up India
    # Source: https://www.standupmitra.in/
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name": "Stand-Up India Scheme",
        "slug": "stand-up-india",
        "short_description": (
            "Bank loans between ₹10 lakh and ₹1 crore to at least one SC/ST borrower "
            "and one woman borrower per bank branch for setting up a greenfield enterprise."
        ),
        "full_description": (
            "Stand-Up India facilitates bank loans between ₹10 lakh and ₹1 crore to "
            "SC/ST and women entrepreneurs for setting up greenfield enterprises in "
            "manufacturing, services, agri-allied, or trading sectors. "
            "Loan tenor up to 7 years; working capital facilities also available."
        ),
        "category": "Loan",
        "sector": "General",
        "target_beneficiaries": "SC/ST entrepreneurs, Women entrepreneurs (18 years and above)",
        "location_scope": "National",
        "states": "All",
        "business_categories": (
            "tailoring,clothing,dairy,food processing,bakery,kirana,grocery,retail,"
            "agriculture,handicraft,beauty,manufacturing,services,transport"
        ),
        "business_tags": "shop,craft,amenity,office",
        "minimum_age": 18,
        "maximum_age": None,
        "minimum_investment": 1000000,
        "maximum_investment": 10000000,
        "maximum_loan_amount": 10000000,
        "maximum_subsidy_amount": None,
        "subsidy_percentage": None,
        "key_benefit": "Loans ₹10L–₹1Cr for greenfield enterprises; at least 51% ownership by SC/ST or woman",
        "eligibility_requirements": json.dumps([
            "SC/ST or woman entrepreneur",
            "Age: 18 years or above",
            "Enterprise should be a greenfield project (first-time venture in manufacturing, services, agri-allied, or trading)",
            "At least 51% shareholding by SC/ST or woman borrower",
            "Borrower should not be in default to any bank or financial institution",
            "Loan amount: ₹10 lakh to ₹1 crore",
        ]),
        "required_documents": json.dumps([
            "Aadhaar card",
            "PAN card",
            "Proof of SC/ST/Women category",
            "Business plan / Project report",
            "Proof of identity and residence",
            "Passport-size photographs",
            "Rent agreement / ownership documents for business premises",
        ]),
        "application_steps": json.dumps([
            "Apply online at standupmitra.in or approach any Scheduled Commercial Bank branch",
            "Fill loan application and submit required documents",
            "Bank assesses the application",
            "Training support available through Stand-Up Connect Centres",
            "Loan sanction and disbursement",
        ]),
        "is_women_specific": True,
        "is_sc_st_specific": True,
        "is_rural_specific": False,
        "is_youth_specific": False,
        "official_source": "Department of Financial Services, Ministry of Finance",
        "official_url": "https://www.standupmitra.in/",
        "data_status": "verified",
        "last_reviewed": "2024-08",
        "sort_order": 3,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 4. PMFME — PM Formalisation of Micro Food Processing Enterprises
    # Source: https://pmfme.mofpi.gov.in/
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name": "PM Formalisation of Micro Food Processing Enterprises (PMFME)",
        "slug": "pmfme",
        "short_description": (
            "Credit-linked subsidy of 35% (up to ₹10 lakh) for upgrading existing "
            "micro food processing enterprises. Targets informal food processing units."
        ),
        "full_description": (
            "PMFME scheme provides financial, technical, and business support for "
            "existing micro food processing enterprises. Individual units receive 35% "
            "credit-linked capital subsidy up to ₹10 lakh. SHGs receive seed capital "
            "of ₹40,000 per member. FPOs/SHGs/Co-operatives receive grant for common "
            "infrastructure. Implemented by Ministry of Food Processing Industries."
        ),
        "category": "Subsidy",
        "sector": "Food Processing",
        "target_beneficiaries": "Existing micro food processing enterprises, SHGs, FPOs, Co-operatives",
        "location_scope": "National",
        "states": "All",
        "business_categories": (
            "food processing,bakery,dairy,pickle,papad,snacks,jaggery,oil mill,"
            "flour mill,spices,jam,juice,fruit processing,vegetable processing,"
            "rice mill,dhal mill,poultry,fishery"
        ),
        "business_tags": "shop,craft",
        "minimum_age": 18,
        "maximum_age": None,
        "minimum_investment": None,
        "maximum_investment": None,
        "maximum_loan_amount": None,
        "maximum_subsidy_amount": 1000000,
        "subsidy_percentage": 35,
        "key_benefit": "35% credit-linked subsidy up to ₹10 lakh for micro food processing enterprise upgradation",
        "eligibility_requirements": json.dumps([
            "Existing micro food processing enterprise (informal/formal)",
            "Individual entrepreneurs, SHGs, FPOs, Cooperatives",
            "Unit must be engaged in food processing activity",
            "Preferably using One District One Product (ODOP) crops/products",
            "Must be willing to formalise (FSSAI registration, Udyam registration etc.)",
            "Age: 18 years or above for individual applicants",
        ]),
        "required_documents": json.dumps([
            "Aadhaar card / identity proof",
            "Proof of existing enterprise / business activity",
            "Project report for proposed upgradation",
            "Bank account details",
            "FSSAI registration (existing or to be applied for)",
            "Udyam registration or proof of micro enterprise",
            "SC/ST/Women certificate if applicable",
        ]),
        "application_steps": json.dumps([
            "Visit PMFME portal: pmfme.mofpi.gov.in",
            "Register and submit online application",
            "Application reviewed by State Nodal Agency",
            "Project report assessment and approval",
            "Credit linked loan from bank",
            "Subsidy released by government to bank",
            "Training and hand-holding support provided",
        ]),
        "is_women_specific": False,
        "is_sc_st_specific": False,
        "is_rural_specific": False,
        "is_youth_specific": False,
        "official_source": "Ministry of Food Processing Industries, Government of India",
        "official_url": "https://pmfme.mofpi.gov.in/",
        "data_status": "verified",
        "last_reviewed": "2024-08",
        "sort_order": 4,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 5. DAY-NRLM — Deendayal Antyodaya Yojana – National Rural Livelihoods Mission
    # Source: https://aajeevika.gov.in/
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name": "DAY-NRLM — Deendayal Antyodaya Yojana (Rural Livelihoods Mission)",
        "slug": "day-nrlm",
        "short_description": (
            "Promotes self-employment and organisation of rural poor into Self Help "
            "Groups (SHGs) with access to credit, subsidies, and skill training "
            "for livelihoods development."
        ),
        "full_description": (
            "DAY-NRLM facilitates formation of SHGs and their federations among rural "
            "poor, provides interest subvention on SHG bank loans (7% p.a.), revolving "
            "fund of ₹10,000–₹15,000 per SHG, community investment fund, and enterprise "
            "promotion support. Women-led micro-enterprises are a key focus."
        ),
        "category": "Enterprise Support",
        "sector": "General",
        "target_beneficiaries": "Rural poor women (BPL and near-BPL), Self Help Groups (SHGs)",
        "location_scope": "National",
        "states": "All",
        "business_categories": (
            "tailoring,clothing,dairy,food processing,bakery,kirana,grocery,retail,"
            "agriculture,handicraft,beauty,livestock,poultry,fishery,weaving"
        ),
        "business_tags": "shop,craft",
        "minimum_age": 18,
        "maximum_age": None,
        "minimum_investment": None,
        "maximum_investment": None,
        "maximum_loan_amount": None,
        "maximum_subsidy_amount": None,
        "subsidy_percentage": None,
        "key_benefit": "Interest subvention on SHG loans (up to 7% p.a.), revolving fund ₹10K–₹15K, enterprise support",
        "eligibility_requirements": json.dumps([
            "Rural poor women (BPL/near-BPL)",
            "Must be part of or willing to form a Self Help Group (SHG)",
            "SHG must be registered under DAY-NRLM in the state",
            "Primary focus on women entrepreneurs in rural areas",
            "Enterprise must be livelihood-generating activity",
        ]),
        "required_documents": json.dumps([
            "Aadhaar card",
            "Ration card / BPL certificate",
            "SHG membership proof",
            "Bank account (individual/SHG)",
            "Photograph",
        ]),
        "application_steps": json.dumps([
            "Join or form an SHG through the local DAY-NRLM/SRLM (State Rural Livelihoods Mission)",
            "Attend SHG meetings and maintain savings for 3–6 months",
            "Apply for revolving fund through the SHG",
            "Access credit from bank under interest subvention",
            "Participate in skill training and enterprise promotion activities",
            "Contact State Rural Livelihoods Mission (SRLM) in your state for enrollment",
        ]),
        "is_women_specific": True,
        "is_sc_st_specific": False,
        "is_rural_specific": True,
        "is_youth_specific": False,
        "official_source": "Ministry of Rural Development, Government of India",
        "official_url": "https://aajeevika.gov.in/",
        "data_status": "verified",
        "last_reviewed": "2024-08",
        "sort_order": 5,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 6. NABARD — Agricultural / Rural Entrepreneurship Support
    # Source: https://www.nabard.org/
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name": "NABARD — Rural Enterprise Development & Agricultural Finance",
        "slug": "nabard-rural-enterprise",
        "short_description": (
            "NABARD provides refinance and development support for agricultural, "
            "allied, and rural non-farm enterprises through cooperatives, RRBs, "
            "and commercial banks."
        ),
        "full_description": (
            "NABARD (National Bank for Agriculture and Rural Development) refinances "
            "short-term and long-term credit to rural entrepreneurs, farmers, and SHGs "
            "through cooperative banks, RRBs, and commercial banks. "
            "Key programs include RIDF (Rural Infrastructure Development Fund), "
            "NABARD SHG-Bank Linkage Programme, and credit support for agri-allied activities."
        ),
        "category": "Loan",
        "sector": "Agriculture",
        "target_beneficiaries": "Farmers, agricultural entrepreneurs, rural artisans, SHGs, FPOs, rural micro-enterprises",
        "location_scope": "National",
        "states": "All",
        "business_categories": (
            "agriculture,dairy,poultry,fishery,horticulture,livestock,food processing,"
            "agri-allied,rural non-farm,handicraft,weaving,sericulture"
        ),
        "business_tags": "shop,craft",
        "minimum_age": 18,
        "maximum_age": None,
        "minimum_investment": None,
        "maximum_investment": None,
        "maximum_loan_amount": None,
        "maximum_subsidy_amount": None,
        "subsidy_percentage": None,
        "key_benefit": "Refinance for agricultural and rural enterprise loans through banks; SHG-Bank Linkage support",
        "eligibility_requirements": json.dumps([
            "Rural entrepreneur, farmer, or artisan",
            "SHG, FPO, or cooperative may also be eligible",
            "Activity must be agricultural, agri-allied, or rural non-farm enterprise",
            "Must apply through a NABARD-linked bank (cooperative bank, RRB, or commercial bank)",
        ]),
        "required_documents": json.dumps([
            "Aadhaar card / identity proof",
            "Land records (for agriculture-based activities)",
            "Business/project proposal",
            "Bank account details",
            "Photographs",
        ]),
        "application_steps": json.dumps([
            "Approach a NABARD-linked bank (cooperative, RRB, or commercial bank) in your area",
            "Discuss agricultural or rural enterprise loan requirement",
            "Submit project proposal and required documents",
            "Bank applies for NABARD refinance",
            "Loan sanctioned and disbursed",
            "Visit nabard.org or nearest NABARD Regional Office for specific scheme details",
        ]),
        "is_women_specific": False,
        "is_sc_st_specific": False,
        "is_rural_specific": True,
        "is_youth_specific": False,
        "official_source": "National Bank for Agriculture and Rural Development (NABARD)",
        "official_url": "https://www.nabard.org/",
        "data_status": "verified",
        "last_reviewed": "2024-08",
        "sort_order": 6,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 7. PMKVY — PM Kaushal Vikas Yojana (Skill Training + Certification)
    # Source: https://www.pmkvyofficial.org/
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name": "PM Kaushal Vikas Yojana (PMKVY) — Skill Development",
        "slug": "pmkvy",
        "short_description": (
            "Free skill training and certification for youth under the National Skills "
            "Qualification Framework (NSQF). Monetary reward on successful certification."
        ),
        "full_description": (
            "PMKVY provides short-term skill training to youth for free, with monetary "
            "reward on successful certification. Covers 300+ job roles across sectors "
            "including agriculture, retail, beauty, construction, electronics, food "
            "processing, healthcare, and textiles. Training is delivered through "
            "PMKVY-affiliated Training Partners and Training Centres."
        ),
        "category": "Training",
        "sector": "General",
        "target_beneficiaries": "Youth (18–45 years), school/college dropouts, unemployed, underemployed",
        "location_scope": "National",
        "states": "All",
        "business_categories": (
            "tailoring,clothing,food processing,bakery,beauty,electronics,agriculture,"
            "retail,healthcare,construction,manufacturing,services"
        ),
        "business_tags": "shop,craft,amenity",
        "minimum_age": 15,
        "maximum_age": 45,
        "minimum_investment": None,
        "maximum_investment": None,
        "maximum_loan_amount": None,
        "maximum_subsidy_amount": None,
        "subsidy_percentage": None,
        "key_benefit": "Free skill training + government certification + monetary award (₹500–₹1,500)",
        "eligibility_requirements": json.dumps([
            "Indian citizen",
            "Age: 15–45 years (varies by job role)",
            "School/college dropout, unemployed, or underemployed youth",
            "Must have Aadhaar card",
            "Prior Learning Recognition (RPL) available for those with existing skills",
        ]),
        "required_documents": json.dumps([
            "Aadhaar card",
            "Bank account linked to Aadhaar",
            "Educational qualification certificate (if any)",
            "Photograph",
        ]),
        "application_steps": json.dumps([
            "Visit pmkvyofficial.org or Skill India Portal (skillindiadigital.gov.in)",
            "Find a PMKVY Training Centre near you",
            "Enrol for a relevant job role / trade",
            "Complete the training programme (typically 150–300 hours)",
            "Appear for assessment by an SSC-empanelled assessment body",
            "Receive NSQF certificate and monetary reward on passing",
        ]),
        "is_women_specific": False,
        "is_sc_st_specific": False,
        "is_rural_specific": False,
        "is_youth_specific": True,
        "official_source": "Ministry of Skill Development and Entrepreneurship, Government of India",
        "official_url": "https://www.pmkvyofficial.org/",
        "data_status": "verified",
        "last_reviewed": "2024-08",
        "sort_order": 7,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 8. Startup India (Seed Fund + Registration Benefits)
    # Source: https://www.startupindia.gov.in/
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name": "Startup India — DPIIT Recognition & Support",
        "slug": "startup-india-dpiit",
        "short_description": (
            "DPIIT-recognised startups get tax exemptions, self-certification for "
            "labour and environment laws, fast-track patent examination, and access "
            "to Startup India Seed Fund Scheme (up to ₹20 lakh for early-stage startups)."
        ),
        "full_description": (
            "Startup India provides DPIIT recognition for eligible startups: "
            "income tax exemption for 3 consecutive years, 80% rebate on patent fees, "
            "self-certification under 6 labour and 3 environmental laws, and access to "
            "Startup India Seed Fund Scheme (SISFS) which provides ₹5–20 lakh for "
            "proof of concept, prototype, product trials and market entry."
        ),
        "category": "Enterprise Support",
        "sector": "General",
        "target_beneficiaries": "Innovative startups up to 10 years old with annual turnover below ₹100 crore",
        "location_scope": "National",
        "states": "All",
        "business_categories": (
            "technology,agri-tech,food-tech,retail-tech,health-tech,edu-tech,"
            "manufacturing,services,software,mobile,electronics"
        ),
        "business_tags": "office",
        "minimum_age": 18,
        "maximum_age": None,
        "minimum_investment": None,
        "maximum_investment": None,
        "maximum_loan_amount": None,
        "maximum_subsidy_amount": 2000000,
        "subsidy_percentage": None,
        "key_benefit": "DPIIT recognition, tax benefits, seed fund up to ₹20 lakh, patent fee rebate 80%",
        "eligibility_requirements": json.dumps([
            "Entity incorporated as Private Ltd., LLP, or Registered Partnership",
            "Business must be innovative with potential to scale",
            "Up to 10 years since incorporation",
            "Annual turnover not exceeding ₹100 crore in any preceding financial year",
            "Not formed by splitting or restructuring an existing business",
            "Must have DPIIT recognition for most benefits",
        ]),
        "required_documents": json.dumps([
            "Certificate of Incorporation",
            "PAN card of the company",
            "Brief pitch deck / description of innovative product/service",
            "Patent/trademark applications if any",
            "Aadhaar of founders",
        ]),
        "application_steps": json.dumps([
            "Register on Startup India Hub: startupindia.gov.in",
            "Apply for DPIIT Recognition through the portal",
            "Receive DPIIT Recognition Certificate",
            "Access benefits: tax exemption, self-certification, patent fee rebate",
            "Apply separately to Startup India Seed Fund Scheme (SISFS) if eligible",
        ]),
        "is_women_specific": False,
        "is_sc_st_specific": False,
        "is_rural_specific": False,
        "is_youth_specific": False,
        "official_source": "Department for Promotion of Industry and Internal Trade (DPIIT), Ministry of Commerce",
        "official_url": "https://www.startupindia.gov.in/",
        "data_status": "verified",
        "last_reviewed": "2024-08",
        "sort_order": 8,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 9. Mahila Udyam Nidhi (Women Entrepreneurs — Small Industries Dev Bank)
    # Source: SIDBI — sidbi.in
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name": "Mahila Udyam Nidhi Scheme (Women Entrepreneur Loan — SIDBI)",
        "slug": "mahila-udyam-nidhi-sidbi",
        "short_description": (
            "SIDBI scheme providing soft loans up to ₹10 lakh to women entrepreneurs "
            "for setting up new small-scale industrial units or upgrading existing ones."
        ),
        "full_description": (
            "Mahila Udyam Nidhi provides financial assistance to women entrepreneurs "
            "for small-scale industrial units. Soft loan up to ₹10 lakh with 10 years "
            "repayment period (including 5-year moratorium). Operates through SIDBI "
            "and channelised through State Financial Corporations/Banks. "
            "Targets manufacturing and allied activities."
        ),
        "category": "Loan",
        "sector": "MSME",
        "target_beneficiaries": "Women entrepreneurs setting up or upgrading small-scale industrial/manufacturing enterprises",
        "location_scope": "National",
        "states": "All",
        "business_categories": (
            "tailoring,clothing,food processing,bakery,dairy,handicraft,beauty,"
            "manufacturing,textiles,weaving,pottery,electronics assembly"
        ),
        "business_tags": "shop,craft",
        "minimum_age": 18,
        "maximum_age": None,
        "minimum_investment": 50000,
        "maximum_investment": 1000000,
        "maximum_loan_amount": 1000000,
        "maximum_subsidy_amount": None,
        "subsidy_percentage": None,
        "key_benefit": "Soft loan up to ₹10 lakh for women entrepreneurs in SSI/manufacturing sector",
        "eligibility_requirements": json.dumps([
            "Woman entrepreneur (sole proprietor or majority women-owned firm)",
            "Engaged in small-scale industry (manufacturing/processing)",
            "New unit setup or existing unit expansion/modernisation",
            "Must approach through SIDBI or channelising State Financial Corporation",
            "Project must be technically and financially viable",
        ]),
        "required_documents": json.dumps([
            "Proof of identity (Aadhaar, PAN)",
            "Proof of residence",
            "Project report",
            "Proof of women ownership/control of enterprise",
            "Bank statements",
            "Quotations for machinery/equipment",
        ]),
        "application_steps": json.dumps([
            "Contact nearest SIDBI branch or State Financial Corporation",
            "Submit loan application with project report",
            "Due diligence and assessment",
            "Loan sanctioned through lending institution",
            "Visit sidbi.in for latest scheme details and branch locator",
        ]),
        "is_women_specific": True,
        "is_sc_st_specific": False,
        "is_rural_specific": False,
        "is_youth_specific": False,
        "official_source": "Small Industries Development Bank of India (SIDBI)",
        "official_url": "https://www.sidbi.in/",
        "data_status": "verified",
        "last_reviewed": "2024-08",
        "sort_order": 9,
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 10. Udyogini — Women Micro-Enterprise Loan
    # Source: Women Development Corporation / State governments
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name": "Udyogini Scheme — Women Micro-Enterprise Support",
        "slug": "udyogini",
        "short_description": (
            "State-level scheme providing loans up to ₹3 lakh to women entrepreneurs "
            "in BPL families, with subsidy for SC/ST and special category women."
        ),
        "full_description": (
            "Udyogini provides financial assistance to women from BPL families for "
            "self-employment in micro-enterprises. Loans up to ₹3 lakh for 88 types "
            "of businesses. SC/ST women and widows/disabled women receive 30% subsidy. "
            "Implemented by Women Development Corporations at state level. "
            "Availability varies by state."
        ),
        "category": "Mixed",
        "sector": "General",
        "target_beneficiaries": "BPL women aged 18–55, SC/ST women, widows, disabled women",
        "location_scope": "National",
        "states": "All",
        "business_categories": (
            "tailoring,clothing,food processing,bakery,dairy,kirana,beauty,retail,"
            "agriculture,handicraft,pottery,incense,candle,agarbatti"
        ),
        "business_tags": "shop,craft",
        "minimum_age": 18,
        "maximum_age": 55,
        "minimum_investment": 5000,
        "maximum_investment": 300000,
        "maximum_loan_amount": 300000,
        "maximum_subsidy_amount": 90000,
        "subsidy_percentage": 30,
        "key_benefit": "Loans up to ₹3 lakh for BPL women; 30% subsidy for SC/ST/widow/disabled women",
        "eligibility_requirements": json.dumps([
            "Woman entrepreneur from BPL family",
            "Age: 18–55 years",
            "Annual family income below state-specified threshold (varies by state)",
            "SC/ST women, widows, and physically disabled women receive higher subsidy",
            "Must be resident of the implementing state",
        ]),
        "required_documents": json.dumps([
            "Aadhaar card",
            "BPL/income certificate",
            "Caste certificate (for SC/ST)",
            "Proof of residence",
            "Bank account details",
            "Photograph",
        ]),
        "application_steps": json.dumps([
            "Contact State Women Development Corporation or District Industries Centre",
            "Obtain and fill application form",
            "Submit required documents",
            "Interview and assessment",
            "Loan sanctioned through linked bank",
            "Subsidy credit to loan account",
        ]),
        "is_women_specific": True,
        "is_sc_st_specific": False,
        "is_rural_specific": False,
        "is_youth_specific": False,
        "official_source": "Women Development Corporations (State Governments) / Ministry of WCD",
        "official_url": "https://wcd.nic.in/",
        "data_status": "verified",
        "last_reviewed": "2024-08",
        "sort_order": 10,
    },
]


# ── Seed function ──────────────────────────────────────────────────────────────

async def seed_schemes(db: AsyncSession) -> int:
    """
    Insert schemes that do not already exist (idempotent by slug).
    Returns number of schemes newly inserted.
    """
    inserted = 0
    for data in SCHEMES:
        existing = await db.execute(select(Scheme).where(Scheme.slug == data["slug"]))
        if existing.scalar_one_or_none() is not None:
            continue

        scheme = Scheme(
            id=str(uuid.uuid4()),
            **{k: v for k, v in data.items()},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(scheme)
        inserted += 1

    await db.commit()
    return inserted


async def main() -> None:
    """Entry point for standalone seeding: python -m app.seed_schemes"""
    import app.models.scheme  # noqa: ensure table is known
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        n = await seed_schemes(db)
        print(f"✅ Seeded {n} new scheme(s) ({len(SCHEMES)} total in dataset)")


if __name__ == "__main__":
    asyncio.run(main())
