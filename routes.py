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

    # LTIM product catalog (same as before)
    ltim_products = """
LTIMindtree offers: Canvas.ai (GenAI platform), Fosfor (data intelligence), BlueVerse AI (intelligent agents),
Insight NxT (IoT/operations), Platform Operations, Digital Platforms, and industry solutions for BFSI, manufacturing, retail/CPG, and hi-tech.
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

    api_keys = get_api_keys()
    research_service = ResearchService(api_keys)

    tts_text = research_service.condense_for_tts(insight, company_name, category)
    return jsonify({"tts_text": tts_text})

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
