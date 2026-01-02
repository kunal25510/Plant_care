from flask import Flask, render_template, request, jsonify, session
import google.generativeai as genai
from PIL import Image
import io
import json
from datetime import datetime
import os
import base64

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'

# 🔑 PUT YOUR API KEY HERE
GEMINI_API_KEY = "AIzaSyCjGH__YdkJk-hOSEIOBuSzCbQACNlRUXc"

genai.configure(api_key=GEMINI_API_KEY)

# File to store history (in production, use a database)
HISTORY_FILE = 'analysis_history.json'
UPLOAD_FOLDER = 'static/uploads'

# Create upload folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def format_response_enhanced(text):
    """Format AI response with proper HTML markup and structured styling"""
    if not text:
        return text
    
    # Clean up markdown formatting
 AIzaSyCjGH__YdkJk-hOSEIOBuSzCbQACNlRUXcAIzaSyCjGH__YdkJk-hOSEIOBuSzCbQACNlRUXcAIzaSyCjGH__YdkJk-hOSEIOBuSzCbQACNlRUXc   text = text.replace('**', '')
    lines = text.split('\n')
    formatted_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        
        if line == '':
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append('<div class="response-spacer"></div>')
            continue
        
        # Detect main headers (ALL CAPS or ends with colon and short)
        if (line.isupper() and len(line) < 60) or (line.endswith(':') and len(line) < 60 and line.count(':') == 1):
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            
            # Add icon based on header content
            icon = ''
            if 'IDENTIFICATION' in line or 'PLANT' in line:
                icon = '🌿'
            elif 'HEALTH' in line or 'STATUS' in line:
                icon = '💚'
            elif 'DISEASE' in line or 'PROBLEM' in line:
                icon = '🦠'
            elif 'SEVERITY' in line:
                icon = '⚠️'
            elif 'SYMPTOMS' in line:
                icon = '🔍'
            elif 'CAUSES' in line:
                icon = '🎯'
            elif 'TREATMENT' in line or 'RECOMMENDATIONS' in line:
                icon = '💊'
            elif 'PREVENTION' in line:
                icon = '🛡️'
            elif 'PROGNOSIS' in line:
                icon = '📊'
            elif 'NOTES' in line or 'ADDITIONAL' in line:
                icon = '📝'
            elif 'CARE' in line:
                icon = '🌱'
            elif 'CLASSIFICATION' in line:
                icon = '📋'
            elif 'CHARACTERISTICS' in line:
                icon = '✨'
            elif 'TOXICITY' in line:
                icon = '⚠️'
            elif 'PROPAGATION' in line:
                icon = '🌱'
            
            formatted_lines.append(f'<div class="response-header"><span class="header-icon">{icon}</span> {line}</div>')
        
        # Sub-headers (contains : in middle)
        elif ':' in line and not line.endswith(':'):
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            parts = line.split(':', 1)
            formatted_lines.append(f'<div class="response-subheader"><span class="label">{parts[0]}:</span> <span class="value">{parts[1]}</span></div>')
        
        # Bullet points
        elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
            content = line[1:].strip()
            if not in_list:
                formatted_lines.append('<ul class="response-list">')
                in_list = True
            formatted_lines.append(f'<li class="response-bullet">{content}</li>')
        
        # Numbered lists
        elif len(line) > 2 and line[0].isdigit() and line[1] in '.):':
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append(f'<div class="response-numbered">{line}</div>')
        
        # Regular content
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append(f'<div class="response-content">{line}</div>')
    
    if in_list:
        formatted_lines.append('</ul>')
    
    return '\n'.join(formatted_lines)

def save_image(file, analysis_id):
    """Save uploaded image and return path"""
    try:
        filename = f"analysis_{analysis_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Convert to RGB if necessary and save
        image = Image.open(file)
        if image.mode in ('RGBA', 'LA', 'P'):
            image = image.convert('RGB')
        image.save(filepath, 'JPEG', quality=85)
        
        return f"/static/uploads/{filename}"
    except Exception as e:
        print(f"Error saving image: {str(e)}")
        return None

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/diagnosis')
def diagnosis():
    return render_template('diagnosis.html')

@app.route('/care-guide')
def care_guide():
    return render_template('care_guide.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/plant-identifier')
def plant_identifier():
    return render_template('plant_identifier.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_plant():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No image selected'}), 400
        
        # Read image
        file.seek(0)
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Save image for history
        file.seek(0)
        analysis_id = len(load_history()) + 1
        image_path = save_image(file, analysis_id)
        
        prompt = """You are an expert plant pathologist. Analyze this plant image and provide a detailed, well-structured report:

PLANT IDENTIFICATION:
[Identify the plant species if possible]

HEALTH STATUS:
[Overall health: Healthy/Diseased/Stressed/Critical]

DISEASE/PROBLEM IDENTIFIED:
[Specific disease or issue name, or "None detected" if healthy]

SEVERITY LEVEL:
[Mild/Moderate/Severe/Critical/None]

SYMPTOMS OBSERVED:
• [List each visible symptom clearly]
• [Include colors, patterns, locations]
• [Note any abnormalities]

POSSIBLE CAUSES:
• [Primary cause]
• [Secondary causes]
• [Environmental factors]

TREATMENT RECOMMENDATIONS:
1. Immediate actions (within 24 hours)
2. Short-term treatment (1-2 weeks)
3. Long-term care adjustments
4. Products or solutions to use

PREVENTION TIPS:
• [How to prevent recurrence]
• [Environmental management]
• [Care routine adjustments]

PROGNOSIS:
[Expected recovery time and success rate]

ADDITIONAL NOTES:
[Any other relevant information or warnings]

Be specific, practical, and use clear formatting. If the image is unclear or not a plant, politely explain why you cannot provide an analysis."""
        
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([prompt, image])
        
        # Format the response
        formatted_analysis = format_response_enhanced(response.text)
        
        # Save to history
        history = load_history()
        history_entry = {
            'id': analysis_id,
            'timestamp': datetime.now().isoformat(),
            'analysis': response.text,
            'formatted_analysis': formatted_analysis,
            'type': 'diagnosis',
            'image_path': image_path
        }
        history.append(history_entry)
        save_history(history)
        
        return jsonify({
            'success': True,
            'analysis': response.text,
            'formatted_analysis': formatted_analysis
        })
    
    except Exception as e:
        print(f"Error in analyze_plant: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/identify', methods=['POST'])
def identify_plant():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image uploaded'}), 400
        
        file = request.files['image']
        
        if file.filename == '':
            return jsonify({'error': 'No image selected'}), 400
        
        # Read image
        file.seek(0)
        image_bytes = file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Save image for history
        file.seek(0)
        analysis_id = len(load_history()) + 1
        image_path = save_image(file, analysis_id)
        
        prompt = """You are an expert botanist. Identify this plant and provide comprehensive information in a well-structured format:

PLANT IDENTIFICATION:
Common Name: [Primary common name]
Scientific Name: [Genus species]
Other Names: [Alternative common names]

CLASSIFICATION:
Family: [Plant family]
Origin: [Native region/habitat]
Type: [Annual/Perennial/Shrub/Tree/etc.]

PHYSICAL CHARACTERISTICS:
• Leaves: [Shape, size, color, arrangement]
• Flowers: [If visible - color, size, season]
• Growth Habit: [Height, spread, growth rate]
• Special Features: [Unique identifying traits]

CARE REQUIREMENTS:
Light: [Full sun/Partial shade/Shade with specifics]
Water: [Frequency and amount]
Soil: [Type, pH, drainage needs]
Temperature: [Ideal range, hardiness zones]
Humidity: [Preferences]
Fertilizer: [Type and frequency]

CARE DIFFICULTY:
[Easy/Moderate/Challenging with explanation]

TOXICITY INFORMATION:
Pets: [Safe/Toxic with details]
Humans: [Safe/Toxic with details]
Handling: [Any precautions needed]

PROPAGATION:
• [Methods: seeds, cuttings, division, etc.]
• [Best time and success tips]

COMMON ISSUES:
• [Typical pests or diseases]
• [Prevention strategies]

INTERESTING FACTS:
• [Cultural significance, uses, or unique properties]
• [Growing tips or fun information]

COMPANION PLANTS:
[Plants that grow well together]

Be accurate and comprehensive. If you cannot identify the plant with certainty, explain what category it might belong to and what additional photos would help."""
        
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content([prompt, image])
        
        # Format the response
        formatted_analysis = format_response_enhanced(response.text)
        
        # Save to history
        history = load_history()
        history_entry = {
            'id': analysis_id,
            'timestamp': datetime.now().isoformat(),
            'analysis': response.text,
            'formatted_analysis': formatted_analysis,
            'type': 'identification',
            'image_path': image_path
        }
        history.append(history_entry)
        save_history(history)
        
        return jsonify({
            'success': True,
            'analysis': response.text,
            'formatted_analysis': formatted_analysis
        })
    
    except Exception as e:
        print(f"Error in identify_plant: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/ask', methods=['POST'])
def ask_question():
    try:
        data = request.json
        question = data.get('question', '')
        context = data.get('analysis', '')
        
        if not question:
            return jsonify({'error': 'Question is required'}), 400
        
        prompt = f"""Based on this plant analysis:

{context}

User's question: {question}

Provide a clear, helpful answer. Structure your response with proper formatting."""
        
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(prompt)
        
        formatted_answer = format_response_enhanced(response.text)
        
        return jsonify({
            'success': True,
            'answer': response.text,
            'formatted_answer': formatted_answer
        })
    
    except Exception as e:
        print(f"Error in ask_question: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    history = load_history()
    # Format each history entry
    for item in history:
        if 'formatted_analysis' not in item:
            item['formatted_analysis'] = format_response_enhanced(item['analysis'])
    return jsonify(history)

@app.route('/api/history/<int:history_id>', methods=['DELETE'])
def delete_history(history_id):
    history = load_history()
    
    # Find and delete associated image
    item_to_delete = next((item for item in history if item['id'] == history_id), None)
    if item_to_delete and 'image_path' in item_to_delete:
        image_path = item_to_delete['image_path'].replace('/static/', 'static/')
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                print(f"Error deleting image: {str(e)}")
    
    history = [item for item in history if item['id'] != history_id]
    save_history(history)
    return jsonify({'success': True})

@app.route('/api/history/clear', methods=['DELETE'])
def clear_history():
    history = load_history()
    
    # Delete all associated images
    for item in history:
        if 'image_path' in item:
            image_path = item['image_path'].replace('/static/', 'static/')
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except Exception as e:
                    print(f"Error deleting image: {str(e)}")
    
    save_history([])
    return jsonify({'success': True})

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🌿 PlantCare Pro - Enhanced Version Starting...")
    print("="*60)
    print(f"✓ API Key: {GEMINI_API_KEY[:15]}...{GEMINI_API_KEY[-4:]}")
    print(f"✓ Server: http://localhost:5000")
    print(f"✓ Upload Folder: {UPLOAD_FOLDER}")
    print(f"✓ Press Ctrl+C to stop")
    print("="*60 + "\n")

    app.run(debug=True, port=5000)

