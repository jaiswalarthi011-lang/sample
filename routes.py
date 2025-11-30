import logging
import requests
from datetime import datetime
from flask import render_template, request, jsonify
from app import app, get_db
from services.research import ResearchService
from services.tts import TTSService

import os

def get_api_keys():
    db = get_db()
    if db is not None:
        keys = db.api_keys.find_one({"_id": "default"})
        if keys:
            return {
                "serper": keys.get("serper", ""),
                "openrouter": keys.get("openrouter", ""),
                "cartesia": keys.get("cartesia", ""),
                "deepgram": keys.get("deepgram", ""),
                "firecrawl": keys.get("firecrawl", ""),
                "sonar": keys.get("sonar", "")
            }
    return {
        "serper": os.environ.get("SERPER_API_KEY", ""),
        "openrouter": os.environ.get("OPENROUTER_API_KEY", ""),
        "cartesia": os.environ.get("CARTESIA_API_KEY", ""),
        "deepgram": os.environ.get("DEEPGRAM_API_KEY", ""),
        "firecrawl": os.environ.get("FIRECRAWL_API_KEY", ""),
        "sonar": os.environ.get("SONAR_API_KEY", "")
    }

@app.route('/')
def index():
    db = get_db()
    search_history = []
    if db is not None:
        history = db.search_history.find().sort("timestamp", -1).limit(10)
        search_history = list(history)
    return render_template('index.html', search_history=search_history)

@app.route('/api/search', methods=['POST'])
def search_company():
    data = request.get_json()
    company_name = data.get('company_name', '').strip()
    
    if not company_name:
        return jsonify({"error": "Company name is required"}), 400
    
    api_keys = get_api_keys()
    research_service = ResearchService(api_keys)
    
    research_data = research_service.get_company_research(company_name)
    
    analysis = research_service.analyze_with_grok(company_name, research_data)
    research_data["ai_analysis"] = analysis
    
    db = get_db()
    if db is not None:
        db.search_history.insert_one({
            "company_name": company_name,
            "timestamp": datetime.utcnow(),
            "categories": list(research_data.get("categories", {}).keys())
        })
        
        db.research_cache.update_one(
            {"company_name": company_name},
            {"$set": {
                "data": research_data,
                "updated_at": datetime.utcnow()
            }},
            upsert=True
        )
    
    return jsonify(research_data)

@app.route('/api/insight/<category>', methods=['POST'])
def get_category_insight(category):
    data = request.get_json()
    insights = data.get('insights', [])
    company_name = data.get('company_name', '')

    api_keys = get_api_keys()
    research_service = ResearchService(api_keys)

    full_insight = research_service.generate_category_insight(category, insights, company_name)
    condensed_insight = research_service.condense_for_tts(full_insight, company_name, category)

    return jsonify({"insight": condensed_insight, "category": category})

@app.route('/api/panel-insight/<category>', methods=['POST'])
def get_panel_insight(category):
    data = request.get_json()
    insights = data.get('insights', [])
    company_name = data.get('company_name', '')

    if not insights:
        return jsonify({"insight": f"No data available for {category} analysis."})

    api_keys = get_api_keys()
    research_service = ResearchService(api_keys)

    # Generate a panel-friendly insight using Grok
    insight_text = ""
    for insight in insights[:3]:
        insight_text += f"{insight['title']}: {insight['snippet']} "

    # Comprehensive LTIMindtree catalog (matching research.py)
    ltim_products = """
INDUSTRY VERTICALS (DOMAINS):
Banking & Financial Services, Insurance, Capital Markets & Payments, Retail, Consumer Packaged Goods (CPG), Travel, Transportation & Hospitality, Manufacturing (Industrial, Automotive, Aerospace, EPC, Process Manufacturing), Energy, Utilities, Oil & Gas, Hi-Tech & Services, Communications, Media & Entertainment, Telecom, Healthcare, Life Sciences & Pharma, Public Services & Government, Real Estate, Logistics

CORE SERVICES (HORIZONTAL):
Cloud & Infrastructure Services: Cloud Migration & Modernization, Hybrid Cloud Management, Multi-Cloud Governance, DevOps & CI/CD Automation, Containerization (Kubernetes, Docker), Platform Operations, AIOps, Intelligent IT Operations, Near Zero Touch Operations
Consulting Services: Digital Strategy Consulting, Business Transformation, AI & Automation Consulting, Process Consulting, Data Strategy Consulting
Data & Analytics: Data Engineering, Data Warehousing, Data Lakes, Data Mesh, Business Intelligence (BI), Big Data Platforms, Advanced Analytics, Predictive Modeling, Machine Learning, AI/ML Engineering, Decision Intelligence, Augmented Analytics
Digital Engineering: Application Development, Mobile App Development, Web Application Development, Cloud-Native Development, Microservices Architecture, API Development & Management, Product Engineering, Platform Engineering, Device Engineering, Embedded Systems
Enterprise Application Services: SAP (S/4HANA, RISE with SAP, SAP BTP, SAP SuccessFactors, SAP Fiori), Oracle (Oracle Cloud, OCI, Oracle ERP, Oracle HCM), Microsoft Dynamics 365 (Finance & Operations, CRM, Business Central), Salesforce (Sales Cloud, Service Cloud, Marketing Cloud, Commerce Cloud), ServiceNow (ITSM, HRSD, SPM, CSM), Workday, Temenos
ERP Transformation: ERP Implementation, ERP Migration, ERP Upgrade, ERP Managed Services, ERP Optimization

Legacy Modernization: Application Modernization, Mainframe Modernization, Re-hosting, Re-platforming, Re-architecting, Database Migration, Data Warehouse Migration, Cloud Re-engineering

Customer Success & Experience: CRM Transformation, Customer 360, Omnichannel Experience, Digital Commerce, Personalization, Customer Analytics, Marketing Automation

Cyber Security: Cloud Security, Identity & Access Management (IAM), Security Operations Center (SOC), Threat Detection & Response, Data Privacy, Compliance & GRC, Zero Trust Security

Quality Engineering & Testing: Test Automation, Performance Engineering, Continuous Testing, AI-Driven Testing, Product Quality Engineering, Digital Testing, Data Testing, Enterprise Apps Testing, Cloud Assurance

Intelligent Automation: Robotic Process Automation (RPA), Hyper-Automation, Process Mining, Workflow Automation, Document Processing, Chatbots & Conversational AI, Low-Code/No-Code Development

Product Engineering Services: IoT Platform Development, Connected Products, Embedded Software, Firmware Development, Hardware-Software Integration

INDUSTRY-SPECIFIC SERVICES:
BFSI: Core Banking Transformation, Payments Modernization, Wealth Management, Trade Finance, Loan Management, Anti-Money Laundering (AML), Fraud Detection, RegTech, InsurTech, Policy Administration, Claims Management, Underwriting Automation

Insurance Platforms: Guidewire (PolicyCenter, BillingCenter, ClaimCenter), Duck Creek (Policy, Billing, Claims, Distribution), Majesco, Insurity

Healthcare & Life Sciences: Clinical Trials, Drug Supply Chain, Pharma Manufacturing, Healthcare Analytics, Patient Engagement, Care Management, Population Health, Interoperability (HL7, FHIR), Provider Solutions, Payer Solutions

Manufacturing & Industry 4.0: Smart Factory, Predictive Maintenance, Asset Performance Management, Connected Worker, Digital Twin, MES Integration, Supply Chain Visibility, Quality Management, Shop Floor Automation

Retail & CPG: Demand Sensing, Trade Promotion Optimization, Merchandise Planning, Connected Store, E-Commerce, Omnichannel Retail, Supply Chain Analytics, Revenue Growth Management

Energy & Utilities: Grid Intelligence, Smart Metering (AMI), Customer Care & Billing, Network Management, Asset Management, Demand Response, Renewable Energy Management, Carbon Management

Telecom & Media: BSS/OSS Transformation, 5G Solutions, Network Operations, Content Management, OTT Platforms, Ad-Tech, Subscriber Analytics

Travel & Transportation: Airline Systems, Hotel Property Management, Booking Platforms, Loyalty Programs, Fleet Management, Cargo Tracking, Logistics Optimization

PROPRIETARY PLATFORMS & PRODUCTS:
AI & Data Platforms:
- Canvas.ai: Enterprise GenAI platform for building, managing and consuming generative AI solutions with responsible AI principles
- BlueVerse AI: AI-native ecosystem with intelligent agents, agentic AI, modular architecture for autonomous IT operations and enterprise processes
- DecisionsCX Platform: Customer 360 and hyper-personalization platform using first-party data and AI

Cloud & Infrastructure Platforms:
- Infinity Platform 2.0: Unified cloud transformation platform with industry blueprints, GenAI-driven cloud strategy, migration factory, multi-cloud governance, FinOps, sustainability tracking
- Infinity Insights: Cloud assessment toolkit with pre-defined rules for fast-tracking cloud adoption
- Enclose: Cloud migration and modernization accelerator
- Cloud Boost: OCI migration and optimization framework powered by Infinity
- Novigo: Oracle Cloud adoption accelerator

IoT & Industry 4.0 Platforms:
- iNXT (Insight NxT): Enterprise IoT platform connecting workers, machines, locations and processes; includes Asset NxT (asset intelligence), Worker NxT (connected worker), Material NxT (track-and-trace), Geospatial NxT (location intelligence), BI NxT (self-configurable analytics)

Analytics & AI Platforms:
- Mosaic Platform Suite: Integrated platform for analytics, AI, IoT and automation; includes Mosaic Decisions (analytics), Mosaic AI (ML models), Mosaic Automation (RPA/IT Ops), Leni (NLP-based virtual analytics assistant)

Enterprise & Domain Platforms:
- Reimagination Studio: SAP S/4HANA transformation accelerator with industry-specific blueprints
- Canvas Profiler: Digital transformation impact assessment tool
- SPEED Framework: Service Process Enablement Engineering and Deployment for ServiceNow implementations

Automation & Operations Platforms:
- iDigitalization (iDz): Low-code business process automation solution powered by IBM Cloud Pak
- iBOC (Integrated Bot Operations Center): Shared bot support services for RPA at scale
- AIM Modernization Center: Microsoft Dynamics legacy-to-cloud migration framework
- NZTM (Near Zero Touch Migration): Platform re-platforming tool (e.g., Salesforce to ServiceNow)
- Agentic Central: Enterprise AI solution for ServiceNow with intelligent agents

Industry-Specific Accelerators:
- Smart Underwriting Platform: GenAI-powered underwriting for insurance
- Duck Creek Migration Framework: SaaS migration accelerators for P&C insurers
- Guidewire Productivity Accelerators: Implementation and QA accelerators for Guidewire suite
- SAP BTP Innovation Studio: Ready-to-deploy digital apps, microservices for SAP BTP
- Oracle Industry Solutions: Pre-built solutions for banking, oil & gas, utilities, retail, life sciences, E&C, media
"""

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_keys.get('openrouter', '')}",
        "Content-Type": "application/json",
    }

    prompt = f"""Based on this {category} data about {company_name}, create a concise, insightful summary (2-3 sentences) that:

1. Identifies the key opportunity or challenge from the data
2. Explains why it matters for {company_name}
3. Suggests how LTIMindtree can help with relevant products/services

Focus on actionable business insights, not just raw data. Be specific and valuable.

LTIM PRODUCTS: {ltim_products}

DATA ({category}):
{insight_text[:1500]}

Business insight:"""

    payload = {
        "model": "x-ai/grok-3-mini-beta",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 150
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if result.get('choices') and len(result['choices']) > 0:
                content = result['choices'][0]['message'].get('content', '').strip()
                return jsonify({"insight": content})
        return jsonify({"insight": f"Analysis shows {company_name} has opportunities in {category} that align with LTIMindtree's expertise."})
    except Exception as e:
        logging.error(f"Panel insight generation error: {e}")
        return jsonify({"insight": f"Key {category} insights for {company_name} reveal strategic opportunities for digital transformation."})

@app.route('/api/ultra-short-tts', methods=['POST'])
def get_ultra_short_tts():
    data = request.get_json()
    insight = data.get('insight', '')
    company_name = data.get('company_name', '')
    category = data.get('category', '')

    if not insight:
        return jsonify({"tts_text": f"{company_name} benefits from LTIMindtree solutions."})

    # Compress the insight using Grok AI to 1/5th length
    compressed_text = compress_insight_with_grok(insight, company_name, category)
    return jsonify({"tts_text": compressed_text})

def compress_insight_with_grok(insight, company_name, category):
    """Compress the insight text to 1/5th length using Grok AI"""
    try:
        api_keys = get_api_keys()
        if not api_keys.get('openrouter'):
            return f"{company_name} benefits from LTIMindtree solutions."

        prompt = f"""As LTIMindtree CEO Venu, create ultra-short guidance (under 25 words) for your sales team on how to sell to {company_name}.

Based on this insight: {insight}

Format as CEO speaking to sales team: "Team, [company_name] needs [problem]—pitch [LTIMindtree solution] to [benefit]."

Make it sound like direct CEO guidance to sales reps. Keep under 25 words total.

Provide ONLY the guidance sentence."""

        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Authorization': f"Bearer {api_keys['openrouter']}",
                'Content-Type': 'application/json',
                'HTTP-Referer': 'https://sales-mind.vercel.app',
                'X-Title': 'Sales Mind Platform'
            },
            json={
                'model': 'meta-llama/llama-3.2-3b-instruct:free',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 100,
                'temperature': 0.3
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            compressed = result['choices'][0]['message']['content'].strip()
            # Clean up the response (remove quotes if present)
            compressed = compressed.strip('"').strip("'")
            return compressed if compressed else f"{company_name} benefits from LTIMindtree solutions."
        else:
            logging.error(f"Grok compression failed: {response.status_code} - {response.text}")
            return f"{company_name} benefits from LTIMindtree solutions."

    except Exception as e:
        logging.error(f"Grok compression error: {e}")
        return f"{company_name} benefits from LTIMindtree solutions."

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({"error": "Text is required"}), 400

    api_keys = get_api_keys()
    tts_service = TTSService(api_keys.get('cartesia', ''))

    audio_base64 = tts_service.text_to_speech(text)

    if audio_base64 == "CREDITS_EXHAUSTED":
        # Update MongoDB to mark TTS as unavailable
        db = get_db()
        if db is not None:
            db.system_status.update_one(
                {"_id": "tts_status"},
                {"$set": {
                    "tts_available": False,
                    "last_checked": datetime.utcnow(),
                    "error": "Credits exhausted"
                }},
                upsert=True
            )
        return jsonify({"error": "TTS credits exhausted"}), 402
    elif audio_base64:
        # Update MongoDB to mark TTS as available
        db = get_db()
        if db is not None:
            db.system_status.update_one(
                {"_id": "tts_status"},
                {"$set": {
                    "tts_available": True,
                    "last_checked": datetime.utcnow()
                }},
                upsert=True
            )
        return jsonify({"audio": audio_base64})
    else:
        return jsonify({"error": "TTS conversion failed"}), 500

@app.route('/api/keys', methods=['GET'])
def get_keys():
    api_keys = get_api_keys()
    masked_keys = {}
    for key, value in api_keys.items():
        if value:
            masked_keys[key] = value[:8] + "..." + value[-4:] if len(value) > 12 else "****"
        else:
            masked_keys[key] = ""
    return jsonify(masked_keys)

@app.route('/api/keys', methods=['POST'])
def update_keys():
    data = request.get_json()
    
    db = get_db()
    if db is not None:
        update_data = {}
        for key in ['serper', 'openrouter', 'cartesia', 'deepgram', 'firecrawl', 'sonar']:
            if key in data and data[key]:
                update_data[key] = data[key]
        
        if update_data:
            db.api_keys.update_one(
                {"_id": "default"},
                {"$set": update_data},
                upsert=True
            )
            return jsonify({"success": True, "message": "API keys updated successfully"})
    
    return jsonify({"error": "Failed to update keys"}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    db = get_db()
    if db is not None:
        history = db.search_history.find().sort("timestamp", -1).limit(20)
        result = []
        for item in history:
            result.append({
                "company_name": item.get("company_name"),
                "timestamp": item.get("timestamp").isoformat() if item.get("timestamp") else None
            })
        return jsonify(result)
    return jsonify([])

@app.route('/api/history/<company_name>', methods=['DELETE'])
def delete_history_item(company_name):
    db = get_db()
    if db is not None:
        db.search_history.delete_many({"company_name": company_name})
        return jsonify({"success": True})
    return jsonify({"error": "Failed to delete"}), 500

@app.route('/api/status', methods=['GET'])
def get_status():
    db = get_db()
    tts_status = {"available": False, "error": "Not configured"}

    if db is not None:
        # Check TTS status from MongoDB
        tts_record = db.system_status.find_one({"_id": "tts_status"})
        if tts_record:
            tts_status = {
                "available": tts_record.get("tts_available", False),
                "last_checked": tts_record.get("last_checked").isoformat() if tts_record.get("last_checked") else None,
                "error": tts_record.get("error", None)
            }
        else:
            # Check if TTS key is configured
            api_keys = get_api_keys()
            if api_keys.get('cartesia'):
                tts_status = {"available": True, "error": None}

    return jsonify({
        "mongodb": db is not None,
        "tts": tts_status,
        "timestamp": datetime.utcnow().isoformat()
    })
