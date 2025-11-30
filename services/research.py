import requests
import logging
from typing import Dict, Any, List

class ResearchService:
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        self.search_config = {
            "max_results": 10,
            "time_filter": "qdr:m"
        }
    
    def search_google(self, query: str, search_type: str = "search") -> Dict[str, Any]:
        url = f"https://google.serper.dev/{search_type}"
        headers = {
            "X-API-KEY": self.api_keys.get('serper', ''),
            "Content-Type": "application/json"
        }
        
        payload = {"q": query, "num": self.search_config['max_results']}
        
        if search_type == "news":
            payload["tbs"] = self.search_config['time_filter']
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                return response.json()
            else:
                logging.error(f"Serper API error: {response.status_code}")
                return {}
        except Exception as e:
            logging.error(f"Search error: {e}")
            return {}
    
    def get_company_research(self, company_name: str) -> Dict[str, Any]:
        search_categories = {
            "overview": f'"{company_name}"',
            "news": f'"{company_name}" news',
            "financials": f'"{company_name}" financial results earnings revenue',
            "hiring": f'"{company_name}" hiring jobs careers',
            "technology": f'"{company_name}" technology cloud AI digital transformation',
            "acquisitions": f'"{company_name}" acquisitions mergers partnerships',
            "competitors": f'"{company_name}" competitors rivals market position',
            "challenges": f'"{company_name}" challenges problems issues'
        }
        
        research_data = {
            "company_name": company_name,
            "categories": {}
        }
        
        for category, query in search_categories.items():
            results = self.search_google(query, "search")
            insights = []
            
            if results.get('organic'):
                for result in results['organic'][:3]:
                    title = result.get('title', 'N/A')
                    snippet = result.get('snippet', 'N/A')
                    link = result.get('link', '')
                    insights.append({
                        "title": title,
                        "snippet": snippet[:200] + "..." if len(snippet) > 200 else snippet,
                        "link": link
                    })
            
            research_data["categories"][category] = {
                "query": query,
                "insights": insights
            }
        
        news_results = self.search_google(company_name, "news")
        news_items = []
        if news_results.get('news'):
            for article in news_results['news'][:5]:
                news_items.append({
                    "title": article.get('title', 'N/A'),
                    "snippet": article.get('snippet', 'N/A')[:200] + "...",
                    "source": article.get('source', 'Unknown'),
                    "date": article.get('date', 'N/A'),
                    "link": article.get('link', '')
                })
        research_data["latest_news"] = news_items
        
        return research_data
    
    def analyze_with_grok(self, company_name: str, research_data: Dict[str, Any]) -> str:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_keys.get('openrouter', '')}",
            "Content-Type": "application/json",
        }
        
        research_text = f"Company: {company_name}\n\n"
        for category, data in research_data.get("categories", {}).items():
            research_text += f"\n{category.upper()}:\n"
            for insight in data.get("insights", []):
                research_text += f"- {insight['title']}: {insight['snippet']}\n"
        
        if research_data.get("latest_news"):
            research_text += "\nLATEST NEWS:\n"
            for news in research_data["latest_news"]:
                research_text += f"- {news['title']} ({news['source']})\n"
        
        prompt = f"""Analyze this company research data and provide a concise, insightful summary. 
Focus on key business opportunities, challenges, and strategic insights.
Keep your response under 300 words and make it engaging.

{research_text[:8000]}

Provide your analysis:"""
        
        payload = {
            "model": "x-ai/grok-3-mini-beta",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                result = response.json()
                if result.get('choices') and len(result['choices']) > 0:
                    return result['choices'][0]['message'].get('content', '')
            logging.error(f"Grok API error: {response.status_code} - {response.text}")
            return "Analysis unavailable. Please check API key configuration."
        except Exception as e:
            logging.error(f"Grok analysis error: {e}")
            return "Analysis unavailable due to connection error."
    
    def generate_category_insight(self, category: str, insights: List[Dict], company_name: str) -> str:
        if not insights:
            return f"No data available for {category}."

        insight_text = ""
        for insight in insights[:3]:
            insight_text += f"{insight['title']}: {insight['snippet']} "

        # Comprehensive LTIMindtree catalog
        ltim_catalog = """
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
- Fosfor Decision Cloud: Data-to-decisions product suite including Spectra (DataOps), Optic (Data Fabric/Discovery), Refract (MLOps), Aspect (Unstructured Data Processing), Lumin (Augmented Analytics with NLP Q&A)
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
            "Authorization": f"Bearer {self.api_keys.get('openrouter', '')}",
            "Content-Type": "application/json",
        }

        prompt = f"""You are Venu, CEO of LTIMindtree. Analyze this SPECIFIC {category} research data about {company_name} and provide a comprehensive sales recommendation using our FULL service portfolio:

CRITICAL REQUIREMENTS:
1. **DOMAIN CONSULTING FIRST**: Start with specific consulting expertise for {company_name}'s industry and the exact {category} challenge
2. **MULTIPLE DIGITAL SERVICES**: Recommend 3-5 different digital services from our complete catalog that directly address the problem
3. **VARIED PLATFORMS**: Include 2-3 different platforms/products from our proprietary offerings
4. **BALANCED APPROACH**: Don't just recommend Fosfor/Canvas.ai/Insight NxT - use the full spectrum of our services

AVAILABLE LTIMINDTREE SERVICES (USE THESE EQUALLY):
{ltim_catalog}

From the research data, identify the PRECISE problem, then provide a structured recommendation:

**Structure your response:**
- Start with domain consulting in the relevant industry
- List 3-5 specific digital services that solve the problem
- End with 2-3 relevant platforms/products
- Explain business value for each recommendation

Example for CPG company with digital integration issues:
"LTIMindtree can provide CPG industry consulting for global digital transformation, digital services including Cloud Migration & Modernization, Data Engineering, Customer 360, and ERP Transformation, plus platforms like Infinity Platform 2.0, Mosaic Platform Suite, and SAP BTP Innovation Studio."

Be specific to {company_name}'s industry and the exact problem from the data.

COMPANY DATA ({category}):
{insight_text[:1500]}

Your comprehensive recommendation:"""

        payload = {
            "model": "x-ai/grok-3-mini-beta",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.6,
            "max_tokens": 200
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=45)
            if response.status_code == 200:
                result = response.json()
                if result.get('choices') and len(result['choices']) > 0:
                    content = result['choices'][0]['message'].get('content', '').strip()
                    return content
            return f"For {company_name}, our {category} analysis shows opportunities where LTIMindtree's expertise can drive transformation."
        except Exception as e:
            logging.error(f"Insight generation error: {e}")
            return f"Based on {company_name}'s {category} data, LTIMindtree can provide strategic solutions to accelerate their digital transformation."

    def condense_for_tts(self, full_insight: str, company_name: str, category: str) -> str:
        """Create CEO guidance for sales team based on client's business strategy"""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_keys.get('openrouter', '')}",
            "Content-Type": "application/json",
        }

        if category.lower() == "hiring":
            # Special handling for hiring category
            prompt = f"""As LTIMindtree CEO, analyze this hiring data and create guidance for sales team:

{full_insight}

Identify the tech roles they're hiring for (AI, data science, cloud, infrastructure, etc.) and explain how LTIMindtree can provide those specialized tech resources.

Format: "Company is expanding tech workforce with roles in X, Y, Z—I urge sales team to position LTIMindtree as strategic partner providing these specialized tech resources."
Keep under 30 words. Be specific about the roles."""

            payload = {
                "model": "x-ai/grok-3-mini-beta",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": 60
            }
        else:
            # Concise CEO guidance using specific formats
            import random
            formats = [
                "Team, {company} is struggling with [problem]—here's my play: [solutions]. Let's land this deal!",
                "Listen up, their challenge is [problem]—I'm pitching [solutions]. Time to make it happen!",
                "This client needs [problem]—my recommendation: [solutions]. Let's close strong!"
            ]
            selected_format = random.choice(formats)

            prompt = f"""As LTIMindtree CEO, create concise guidance using this exact format:

{selected_format}

Fill in the brackets with:
- [problem]: Specific issue from the research data
- [solutions]: 1-2 specific LTIM services/platforms

Keep it under 25 words total. Be direct and to the point.

Research data: {full_insight}"""

            payload = {
                "model": "x-ai/grok-3-mini-beta",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 50
            }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                if result.get('choices') and len(result['choices']) > 0:
                    content = result['choices'][0]['message'].get('content', '').strip()
                    # Don't truncate - let TTS speak complete text
                    return content
            return f"{company_name} focuses on growth—I would urge sales team to position LTIMindtree strategically."
        except Exception as e:
            logging.error(f"TTS guidance error: {e}")
            return f"{company_name} seeks transformation—I urge sales team to engage LTIMindtree solutions."
