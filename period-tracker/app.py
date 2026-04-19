from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta

# AI/ML Imports for Emerging Tech
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

app = Flask(__name__)
app.secret_key = 'flowgreen_secret_key'

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flowgreen_new.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Models ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    periods = db.relationship('Period', backref='user', cascade="all, delete-orphan")
    symptoms = db.relationship('SymptomLog', backref='user', cascade="all, delete-orphan") # Added relationship
    weights = db.relationship('WeightLog', backref='user', cascade="all, delete-orphan")
    temperatures = db.relationship('TemperatureLog', backref='user', cascade="all, delete-orphan")

class Period(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class SymptomLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=date.today)
    symptoms = db.Column(db.String(500))  # Stores "Cramps, Headache"
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class WeightLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class TemperatureLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    value = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

with app.app_context():
    db.create_all()

# --- Remedy Dictionary (Evidence-Based) ---
REMEDIES = {
    # Physical Discomfort
    "Cramps": {
        "main": "Apply heat therapy (heating pad) for 15-20 minutes to lower abdomen.",
        "secondary": "Try light stretching, yoga, or walking. Ibuprofen (if safe for you) is also effective.",
        "diet": "Increase magnesium, cal­cium, and omega-3 intake.",
        "severity": "common"
    },
    "Bloating": {
        "main": "Reduce sodium and processed foods. Increase potassium through bananas, sweet potatoes.",
        "secondary": "Peppermint tea, fennel tea, or light exercise can reduce water retention.",
        "diet": "Avoid carbonated drinks and high-fiber foods temporarily if uncomfortable.",
        "severity": "common"
    },
    "Headache": {
        "main": "Stay hydrated with water. Fatigue-related headaches improve with rest and magnesium.",
        "secondary": "Rest in a dark, quiet room. Apply a cold/warm compress to your neck.",
        "diet": "Magnesium-rich foods: almonds, pumpkin seeds, dark leafy greens.",
        "severity": "common"
    },
    "Fatigue": {
        "main": "This is normal! Your body needs 20-30% more energy during your period.",
        "secondary": "Prioritize sleep, take short naps if needed, and do gentle activities.",
        "diet": "Iron-rich foods: spinach, lentils, red meat, beans. Pair with vitamin C for absorption.",
        "severity": "common"
    },
    "Breast Tenderness": {
        "main": "Wear a supportive bra or sports bra. Avoid caffeine which can worsen tenderness.",
        "secondary": "Apply warm compresses if painful. This usually subsides by end of period.",
        "diet": "Vitamin E supplements or foods: almonds, avocado, olive oil.",
        "severity": "common"
    },
    "Nausea": {
        "main": "Eat small, frequent meals to stabilize blood sugar and prevent nausea.",
        "secondary": "Ginger tea, peppermint, or ginger candies are natural remedies.",
        "diet": "Bland, protein-rich foods: crackers, yogurt, toast. Avoid greasy foods.",
        "severity": "moderate"
    },
    "Acne": {
        "main": "Keep skin clean and hydrated. Salicylic acid or benzoyl peroxide cleansers help.",
        "secondary": "Avoid touching your face. Change pillowcases frequently.",
        "diet": "Zinc supplements or foods: oysters, beef, pumpkin seeds. Stay hydrated.",
        "severity": "mild"
    },
    "Backache": {
        "main": "Use gentle stretching and a warm compress on your lower back.",
        "secondary": "Try walking or a warm bath to loosen tight muscles.",
        "diet": "Keep magnesium-rich foods like spinach and nuts in your meals.",
        "severity": "moderate"
    },
    "Insomnia": {
        "main": "Establish a calming bedtime routine and avoid screens before sleep.",
        "secondary": "Drink herbal tea (chamomile or lavender) and keep the room cool.",
        "diet": "Limit caffeine after midday and choose light dinners with protein.",
        "severity": "moderate"
    },
    "Abdominal pain": {
        "main": "Gentle heat and rest can ease abdominal pain during your cycle.",
        "secondary": "Sip ginger or peppermint tea and avoid heavy meals.",
        "diet": "Eat smaller, frequent meals and include anti-inflammatory foods like berries.",
        "severity": "moderate"
    },
    "Vaginal itching": {
        "main": "Keep the area clean and dry. Wear breathable cotton underwear.",
        "secondary": "Avoid scented products and hot baths until irritation clears.",
        "diet": "Yogurt and probiotics may support healthy flora.",
        "severity": "moderate"
    },
    "Vaginal dryness": {
        "main": "Use a gentle, water-based lubricant and stay well-hydrated.",
        "secondary": "Avoid harsh soaps and choose mild, fragrance-free cleansers.",
        "diet": "Healthy fats from avocado, nuts, and olive oil can support lubrication.",
        "severity": "informational"
    },
    "Spotting": {
        "main": "Light spotting can be normal between cycles, especially near your period.",
        "secondary": "Track it for a few cycles and see your doctor if it becomes frequent.",
        "diet": "Keep iron-rich foods like leafy greens and lean meat in your diet.",
        "severity": "informational"
    },
    "Watery": {
        "main": "Watery discharge often happens around ovulation and is usually normal.",
        "secondary": "Use panty liners if needed and note any strong odor or irritation.",
        "diet": "Stay hydrated and eat balanced meals to support your cycle.",
        "severity": "informational"
    },
    "Sticky": {
        "main": "Sticky discharge is common mid-cycle and usually nothing to worry about.",
        "secondary": "Track it alongside other symptoms to understand your fertility pattern.",
        "diet": "Healthy fiber and hydration help keep discharge balanced.",
        "severity": "informational"
    },
    "No discharge": {
        "main": "A lack of discharge can be normal for some people, especially after menstruation.",
        "secondary": "If you experience itching or discomfort, talk to a provider.",
        "diet": "Hydrate well and include healthy fats to support natural moisture.",
        "severity": "informational"
    },
    "High sex drive": {
        "main": "High libido is a normal part of many cycles, particularly around ovulation.",
        "secondary": "Honor your body’s energy with healthy boundaries and communication.",
        "diet": "Maintain stable blood sugar with balanced meals and avoid excess sugar.",
        "severity": "positive"
    },
    "Low sex drive": {
        "main": "Low desire can happen with hormonal changes and stress.",
        "secondary": "Rest, communicate with your partner, and prioritize self-care.",
        "diet": "Stay hydrated and include zinc-rich foods like beans, seeds, and eggs.",
        "severity": "normal"
    },
    "Neutral sex drive": {
        "main": "A neutral libido is perfectly normal. Your body is simply balancing itself.",
        "secondary": "Focus on comfort, rest, and staying present with what feels right.",
        "diet": "Eat a variety of nutrient-rich foods to support your cycle overall.",
        "severity": "informational"
    },
    "Orgasm": {
        "main": "Orgasm may reduce menstrual cramps for some people through natural hormone release.",
        "secondary": "Choose what feels comfortable for your body and prioritize consent.",
        "diet": "Staying hydrated supports healthy circulation and comfort.",
        "severity": "informational"
    },
    
    # Mood & Mind
    "Irritable": {
        "main": "This is PMS - hormonal shifts affect mood. Deep breathing and pausing before reacting helps.",
        "secondary": "Take a 10-15 minute walk outside. Practice the 5-4-3-2-1 grounding technique.",
        "diet": "Avoid excess caffeine and sugar. Complex carbs help stabilize mood.",
        "severity": "common"
    },
    "Anxious": {
        "main": "Hormonal changes can trigger anxiety. Limit caffeine completely for now.",
        "secondary": "Try meditation apps (Calm, Headspace), breathing exercises, or journaling.",
        "diet": "L-theanine, magnesium, and vitamin B6 can help. Avoid energy drinks.",
        "severity": "moderate"
    },
    "Sad": {
        "main": "Mood changes are normal with hormonal fluctuations. Be compassionate with yourself.",
        "secondary": "Call a friend, journal, or engage in activities you enjoy. Sunlight helps.",
        "diet": "Omega-3s (salmon), B vitamins (eggs), and complex carbs support mood.",
        "severity": "moderate"
    },
    "Happy": {
        "main": "Great! This can occur around ovulation or with naturally rising hormones.",
        "secondary": "Channel this energy into creative projects or social activities.",
        "diet": "Maintain stable energy with balanced meals to sustain your mood.",
        "severity": "positive"
    },
    
    # Discharge (Informational)
    "Dry": {
        "main": "Normal during menstruation. Stay hydrated and use water-based lubricant if needed.",
        "secondary": "This typically changes as your cycle progresses post-period.",
        "diet": "Hydration is key: drink 2-3 liters of water daily.",
        "severity": "informational"
    },
    "Egg White": {
        "main": "Clear, stretchy discharge - indicates high fertility (ovulation phase).",
        "secondary": "This is a sign your body is ready to ovulate. Useful for family planning.",
        "diet": "Support hormonal balance with whole grains and lean proteins.",
        "severity": "informational"
    },
    "Creamy": {
        "main": "Creamy discharge occurs before ovulation and after periods normalize.",
        "secondary": "This is normal and part of your natural cycle.",
        "diet": "Continue with balanced nutrition to support your cycle.",
        "severity": "informational"
    },
    
    # Cravings
    "Sweet": {
        "main": "Cravings peak before period due to dropping serotonin. Dark chocolate is ideal!",
        "secondary": "Dark chocolate (70%+) provides magnesium, which your body needs.",
        "diet": "Dark chocolate, fruit with nut butter, or dates satisfy cravings healthily.",
        "severity": "mild"
    },
    "Salty": {
        "main": "Salty cravings may indicate low electrolytes. Don't entirely restrict salt.",
        "secondary": "Choose naturally salty options with nutrients.",
        "diet": "Salted nuts, seeds, hummus with salt, or olives are better than processed snacks.",
        "severity": "mild"
    },
    
    # Additional Physical Symptoms
    "Dizziness": {
        "main": "Dizziness can occur due to hormonal changes or iron deficiency during menstruation.",
        "secondary": "Sit or lie down, drink water, and rest. Get up slowly from sitting or lying positions.",
        "diet": "Iron-rich foods like spinach, lentils, red meat. Pair with vitamin C for better absorption.",
        "severity": "moderate"
    },
    "Joint ache": {
        "main": "Joint pain can be related to hormonal fluctuations affecting inflammation markers.",
        "secondary": "Gentle movement, warm compresses, and anti-inflammatory foods can help.",
        "diet": "Foods rich in omega-3s: salmon, walnuts, flaxseeds. Ginger and turmeric have anti-inflammatory properties.",
        "severity": "moderate"
    },
    "General discomfort": {
        "main": "General body discomfort is common during your period. Listen to your body's needs.",
        "secondary": "Rest, gentle stretching, warm baths, and self-massage can ease tension.",
        "diet": "Magnesium-rich foods support muscle relaxation: almonds, pumpkin seeds, dark chocolate.",
        "severity": "moderate"
    },
    
    # Digestive Issues
    "Constipation": {
        "main": "Hormonal changes slow digestion and increase constipation during your cycle.",
        "secondary": "Increase water intake, eat fiber-rich foods, and try light movement like walking.",
        "diet": "Prunes, pears, whole grains, leafy greens, and chia seeds. Stay hydrated with 2-3 liters daily.",
        "severity": "moderate"
    },
    "Diarrhea": {
        "main": "Loose stools are common due to prostaglandins released during menstruation.",
        "secondary": "Stay hydrated, avoid fatty or spicy foods, and eat bland meals.",
        "diet": "Rice, toast, bananas, applesauce, and crackers. Include electrolyte-rich foods like coconut water.",
        "severity": "moderate"
    },
    "Gas": {
        "main": "Bloating and gas increase during your period due to slower digestion.",
        "secondary": "Peppermint or fennel tea, gentle walking, and avoiding carbonated drinks help.",
        "diet": "Limit cruciferous vegetables temporarily. Eat slowly and chew thoroughly.",
        "severity": "mild"
    },
    "Heartburn": {
        "main": "Heartburn can be triggered by relaxed stomach muscles during hormone fluctuations.",
        "secondary": "Eat smaller meals, avoid triggers like spicy or fatty foods, and stay upright after eating.",
        "diet": "Bland foods, low-acid options: bananas, almonds, oatmeal. Avoid caffeine and chocolate temporarily.",
        "severity": "moderate"
    },
    "Indigestion": {
        "main": "Indigestion happens when digestive processes slow during your cycle.",
        "secondary": "Eat small frequent meals, sip ginger tea, and avoid heavy dining.",
        "diet": "Ginger, fennel, peppermint tea. Light proteins like chicken and fish. Avoid heavy, rich foods.",
        "severity": "moderate"
    },
    
    # Discharge Type
    "Clumpy white": {
        "main": "Thick, clumpy white discharge can indicate yeast overgrowth or normal cycle variation.",
        "secondary": "Maintain hygiene, use cotton underwear, and avoid douching. See a provider if persistent.",
        "diet": "Yogurt and probiotics support healthy vaginal flora. Avoid excess sugar temporarily.",
        "severity": "informational"
    },
    "Gray": {
        "main": "Gray discharge could indicate bacterial vaginosis. Consult a healthcare provider.",
        "secondary": "Seek medical evaluation if accompanied by itching, burning, or strong odor.",
        "diet": "Probiotics and yogurt support healthy bacterial balance.",
        "severity": "moderate"
    },
    "Unusual": {
        "main": "Unusual discharge warrants a check with your healthcare provider for peace of mind.",
        "secondary": "Note color, odor, and consistency changes to discuss with your provider.",
        "diet": "Maintain good nutrition and hydration to support your immune system.",
        "severity": "informational"
    }
}

# --- Helper Function: Get Cycle Phase ---
def get_cycle_phase(user_id):
    """Determines which phase of the cycle user is in based on last period."""
    latest_period = Period.query.filter_by(user_id=user_id).order_by(Period.start_date.desc()).first()
    if not latest_period:
        return "unknown", 0
    
    days_since_start = (datetime.utcnow().date() - latest_period.start_date).days
    
    # Typical 28-day cycle
    if days_since_start < 0:
        return "pre-period", abs(days_since_start)
    elif days_since_start < 5:
        return "menstruation", days_since_start
    elif days_since_start < 12:
        return "follicular", days_since_start - 5
    elif days_since_start < 18:
        return "ovulation", days_since_start - 12
    else:
        return "luteal", days_since_start - 18

# --- Helper Function: Enhanced Analysis ---
def analyze_symptoms(symptoms_str, user_id):
    """Analyze symptoms with cycle phase context."""
    symptoms_list = [s.strip() for s in symptoms_str.split(", ")]
    phase, _ = get_cycle_phase(user_id)
    
    analysis = {
        "phase": phase,
        "remedies": [],
        "pattern_note": "",
        "wellness_tips": []
    }
    
    for symptom in symptoms_list:
        if symptom in REMEDIES:
            remedy = REMEDIES[symptom]
            analysis["remedies"].append({
                "symptom": symptom,
                "advice": remedy.get("main", ""),
                "secondary": remedy.get("secondary", ""),
                "diet": remedy.get("diet", ""),
                "severity": remedy.get("severity", "mild")
            })
    
    # Phase-specific wellness tips
    if phase == "menstruation":
        analysis["wellness_tips"].append("Rest is your priority - your body needs extra energy now.")
        analysis["wellness_tips"].append("Stay hydrated and replenish iron with red meat, beans, or supplements.")
    elif phase == "follicular":
        analysis["wellness_tips"].append("Energy is rising! This is a great time for exercise and new projects.")
    elif phase == "ovulation":
        analysis["wellness_tips"].append("You're at peak energy and confidence - channel this into important tasks!")
    elif phase == "luteal":
        analysis["wellness_tips"].append("Slow down and prioritize self-care - avoid major decisions if possible.")
    
    return analysis


def analyze_daily_wellness(user_id):
    """Analyze today's tracking inputs and build a comprehensive remedy summary."""
    today = date.today()
    symptom_log = SymptomLog.query.filter_by(user_id=user_id, date=today).first()
    weight_log = WeightLog.query.filter_by(user_id=user_id, date=today).first()
    temp_log = TemperatureLog.query.filter_by(user_id=user_id, date=today).first()
    phase, cycle_day = get_cycle_phase(user_id)

    analysis = {
        "phase": phase,
        "cycle_day": cycle_day,
        "symptoms": [],
        "remedies": [],
        "wellness_tips": [],
        "wellness_insights": [],
        "tracker_summary": {}
    }

    if symptom_log and symptom_log.symptoms:
        symptom_list = [s.strip() for s in symptom_log.symptoms.split(", ") if s.strip()]
        analysis["symptoms"] = symptom_list
        for symptom in symptom_list:
            if symptom in REMEDIES:
                remedy = REMEDIES[symptom]
                analysis["remedies"].append({
                    "symptom": symptom,
                    "advice": remedy.get("main", ""),
                    "secondary": remedy.get("secondary", ""),
                    "diet": remedy.get("diet", ""),
                    "severity": remedy.get("severity", "mild")
                })

    if weight_log:
        analysis["tracker_summary"]["weight"] = weight_log.value
        yesterday = today - timedelta(days=1)
        prev_weight = WeightLog.query.filter_by(user_id=user_id, date=yesterday).first()
        if prev_weight:
            delta = weight_log.value - prev_weight.value
            if abs(delta) < 0.5:
                analysis["wellness_insights"].append(f"Weight stable at {weight_log.value:.1f}kg today.")
            elif delta > 0:
                analysis["wellness_insights"].append(f"Slight weight increase (+{delta:.1f}kg). Stay hydrated and balanced.")
            else:
                analysis["wellness_insights"].append(f"Slight weight decrease (-{abs(delta):.1f}kg). Keep nourishing meals on track.")
    
    if temp_log:
        analysis["tracker_summary"]["temperature"] = temp_log.value
        if 36.4 <= temp_log.value <= 37.0:
            analysis["wellness_insights"].append(f"Temperature is normal at {temp_log.value:.1f}°C.")
        elif temp_log.value < 36.4:
            analysis["wellness_insights"].append(f"Temperature is a bit low at {temp_log.value:.1f}°C. Stay warm and rested.")
        else:
            analysis["wellness_insights"].append(f"Temperature is slightly elevated at {temp_log.value:.1f}°C. Rest and hydrate.")

    if phase == "menstruation":
        analysis["wellness_tips"].append("Rest is your priority - your body needs extra energy now.")
        analysis["wellness_tips"].append("Stay hydrated and replenish iron with red meat, beans, or supplements.")
        if not temp_log:
            analysis["wellness_tips"].append("Log your temperature for better cycle insight.")
    elif phase == "follicular":
        analysis["wellness_tips"].append("Energy is rising! This is a great time for exercise and new projects.")
        if weight_log:
            analysis["wellness_tips"].append("Keep meals regular to support rising energy.")
    elif phase == "ovulation":
        analysis["wellness_tips"].append("You're in your fertile window. Stay hydrated and focus on self-care.")
    elif phase == "luteal":
        analysis["wellness_tips"].append("Slow down and prioritize self-care - avoid major decisions if possible.")
        analysis["wellness_tips"].append("Choose magnesium-rich foods and gentle movement.")

    return analysis


def ai_analyze_symptoms(symptoms_text, available_remedies=None):
    """
    AI-powered symptom analysis using TF-IDF similarity matching.
    Returns ranked remedies based on symptom similarity with confidence scores.
    """
    if not AI_AVAILABLE or not symptoms_text:
        return None
    
    try:
        if available_remedies is None:
            available_remedies = list(REMEDIES.keys())
        
        # Create TF-IDF vectorizer
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 3), lowercase=True)
        
        # Combine user symptoms for better matching
        all_texts = [symptoms_text] + available_remedies
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # Calculate similarity between user input and each remedy
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        
        # Rank remedies by similarity and filter by confidence threshold
        ranked_remedies = []
        min_confidence = 0.2  # Only include remedies with at least 20% similarity
        
        for idx, similarity in enumerate(sorted(enumerate(similarities), key=lambda x: x[1], reverse=True)):
            remedy_idx, confidence = similarity
            if confidence < min_confidence:
                continue
            
            remedy_name = available_remedies[remedy_idx]
            ranked_remedies.append({
                "remedy": remedy_name,
                "confidence": round(float(confidence) * 100, 1),
                "details": REMEDIES.get(remedy_name, {})
            })
        
        return ranked_remedies[:10]  # Return top 10 recommendations
    except Exception as e:
        return None


def ai_enhanced_remedies(symptoms_list, user_id, phase):
    """
    Enhanced remedy recommendation combining rule-based and AI analysis.
    Returns both traditional and AI-powered recommendations with analysis.
    """
    # Direct matches (rule-based)
    direct_matches = []
    for symptom in symptoms_list:
        if symptom in REMEDIES:
            direct_matches.append({
                "symptom": symptom,
                "type": "direct",
                "advice": REMEDIES[symptom].get("main", ""),
                "secondary": REMEDIES[symptom].get("secondary", ""),
                "diet": REMEDIES[symptom].get("diet", ""),
                "severity": REMEDIES[symptom].get("severity", "mild")
            })
    
    # AI-powered fuzzy matching for unrecognized symptoms
    ai_matches = []
    if AI_AVAILABLE and symptoms_list:
        symptoms_string = ", ".join(symptoms_list)
        ai_recommendations = ai_analyze_symptoms(symptoms_string)
        
        if ai_recommendations:
            ai_matches = [{
                "symptom": rec["remedy"],
                "type": "ai-recommended",
                "confidence": rec["confidence"],
                "advice": rec["details"].get("main", ""),
                "secondary": rec["details"].get("secondary", ""),
                "diet": rec["details"].get("diet", ""),
                "severity": rec["details"].get("severity", "mild")
            } for rec in ai_recommendations if rec["remedy"] not in [d["symptom"] for d in direct_matches]]
    
    # Phase-specific analysis
    phase_insights = []
    if phase == "menstruation":
        phase_insights.append("Your body is in active menstruation. Prioritize hydration and iron intake.")
    elif phase == "follicular":
        phase_insights.append("Rising hormones bring increasing energy. Perfect time for new activities.")
    elif phase == "ovulation":
        phase_insights.append("Peak hormone levels - embrace your peak energy and confidence.")
    elif phase == "luteal":
        phase_insights.append("Hormones are declining. Slow down and practice self-care.")
    
    return {
        "direct_matches": direct_matches,
        "ai_matches": ai_matches,
        "phase_insights": phase_insights,
        "ai_available": AI_AVAILABLE
    }


def get_cycle_insight(latest_log):
    if not latest_log:
        return "Log your period dates to get personalized daily insights and cycle forecasts."

    today = date.today()
    period_length = ((latest_log.end_date - latest_log.start_date).days + 1) if latest_log.end_date else 5
    cycle_day = (today - latest_log.start_date).days + 1
    if cycle_day <= 0:
        return "Start tracking your upcoming cycle so FlowGreen can predict your next window."

    if cycle_day <= period_length:
        return "Your body is still in menstruation. Focus on hydration, warmth, and gentle movement to ease cramps."
    if cycle_day == 14:
        return "Today is your likely ovulation day. Your energy may be at its peak — embrace confidence and steady nutrition."
    if 11 <= cycle_day <= 16:
        return "You're in your fertile window. Prioritize self-care, hydration, and clear planning for the days ahead."
    if cycle_day <= 28:
        return "Your body is shifting into the luteal phase. Rest when needed and choose calming routines."

    return "Your next period is overdue. Keep tracking symptoms and consult a healthcare provider if the delay continues."


def build_calendar_highlights(logs, latest_log):
    actual_period_days = []
    for log in logs:
        start = log.start_date
        end = log.end_date or (start + timedelta(days=4))
        total_days = (end - start).days
        for i in range(total_days + 1):
            actual_period_days.append((start + timedelta(days=i)).isoformat())

    predicted_period_days = []
    fertile_days = []
    ovulation_day = None

    if latest_log:
        predicted_start = latest_log.start_date + timedelta(days=28)
        for i in range(5):
            predicted_period_days.append((predicted_start + timedelta(days=i)).isoformat())

        ovulation_date = predicted_start - timedelta(days=14)
        ovulation_day = ovulation_date.isoformat()

        fertile_start = predicted_start - timedelta(days=16)
        for i in range(5):
            fertile_days.append((fertile_start + timedelta(days=i)).isoformat())

    return actual_period_days, predicted_period_days, fertile_days, ovulation_day

# --- Advanced AI Functions ---

def get_symptom_patterns(user_id):
    """Analyze symptom patterns and trends over past 3 cycles."""
    symptom_history = SymptomLog.query.filter_by(user_id=user_id).order_by(SymptomLog.date.desc()).limit(90).all()
    
    symptom_frequency = {}
    symptom_dates = {}
    
    for log in symptom_history:
        if log.symptoms:
            symptoms_list = [s.strip() for s in log.symptoms.split(',') if s.strip()]
            for symptom in symptoms_list:
                symptom_frequency[symptom] = symptom_frequency.get(symptom, 0) + 1
                if symptom not in symptom_dates:
                    symptom_dates[symptom] = []
                symptom_dates[symptom].append(log.date)
    
    # Calculate most common symptoms
    sorted_symptoms = sorted(symptom_frequency.items(), key=lambda x: x[1], reverse=True)
    top_symptoms = [{"name": s[0], "frequency": s[1], "percentage": round((s[1] / len(symptom_history)) * 100, 1)} for s in sorted_symptoms[:5]]
    
    return {
        "top_symptoms": top_symptoms,
        "total_tracked_days": len(symptom_history),
        "symptom_patterns": symptom_frequency
    }


def get_symptom_severity_assessment(symptoms_list):
    """Assess overall severity of current symptoms."""
    severity_scores = {"mild": 1, "informational": 0.5, "normal": 1, "positive": 0, "common": 2, "moderate": 3}
    
    total_severity = 0
    max_severity = 0
    critical_symptoms = []
    
    for symptom in symptoms_list:
        if symptom in REMEDIES:
            severity_level = REMEDIES[symptom].get("severity", "mild")
            score = severity_scores.get(severity_level, 1)
            total_severity += score
            max_severity = max(max_severity, score)
            
            if score >= 3:
                critical_symptoms.append(symptom)
    
    avg_severity = total_severity / len(symptoms_list) if symptoms_list else 0
    
    if max_severity >= 3 or len(critical_symptoms) > 2:
        severity_label = "High - Consider medical consultation"
    elif avg_severity >= 2:
        severity_label = "Moderate - Self-care strongly recommended"
    elif avg_severity >= 1:
        severity_label = "Mild - Standard self-care measures"
    else:
        severity_label = "Low - Monitor and maintain wellness"
    
    return {
        "level": severity_label,
        "average_score": round(avg_severity, 2),
        "max_score": max_severity,
        "critical_symptoms": critical_symptoms
    }


def get_personalized_wellness_plan(user_id):
    """Create a personalized daily wellness plan based on current state."""
    today = date.today()
    phase, cycle_day = get_cycle_phase(user_id)
    symptom_log = SymptomLog.query.filter_by(user_id=user_id, date=today).first()
    weight_log = WeightLog.query.filter_by(user_id=user_id, date=today).first()
    temp_log = TemperatureLog.query.filter_by(user_id=user_id, date=today).first()
    
    plan = {
        "morning": [],
        "afternoon": [],
        "evening": [],
        "throughout_day": [],
        "avoid": [],
        "hydration_goal": 2500  # ml
    }
    
    symptoms = []
    if symptom_log and symptom_log.symptoms:
        symptoms = [s.strip() for s in symptom_log.symptoms.split(',') if s.strip()]
    
    # Menstruation phase
    if phase == "menstruation":
        plan["morning"] = [
            "🌅 Warm lemon water or herbal tea to boost energy",
            "🍳 Iron-rich breakfast: eggs, oatmeal, berries",
            "💊 Gentle stretching or yoga (10 minutes)"
        ]
        plan["afternoon"] = [
            "🚶 Light walk for 20-30 minutes",
            "🥗 Iron-rich lunch: spinach, beans, chicken",
            "💧 Hydration check: drink 500ml water"
        ]
        plan["evening"] = [
            "🛀 Warm bath with Epsom salt (if cramps present)",
            "🍲 Nourishing dinner: leafy greens, protein",
            "😴 Aim for 8+ hours sleep"
        ]
        plan["throughout_day"] = ["Heat therapy for cramps", "Rest when needed", "Avoid heavy lifting"]
        plan["avoid"] = ["Caffeine (if sensitive)", "High-intensity exercise", "Cold foods"]
        plan["hydration_goal"] = 3000
    
    # Follicular phase
    elif phase == "follicular":
        plan["morning"] = [
            "🌅 Energizing smoothie with fruits",
            "🏃 Medium-intensity workout (20-30 min)",
            "☀️ Get sunlight exposure"
        ]
        plan["afternoon"] = [
            "💪 Strength training or yoga",
            "🥙 Well-balanced lunch with complex carbs",
            "📱 Plan new projects or activities"
        ]
        plan["evening"] = [
            "🎨 Creative activity or hobby",
            "🍽️ Dinner with whole grains and protein",
            "📚 Light reading or journaling"
        ]
        plan["throughout_day"] = ["Embrace your rising energy", "Try new activities", "Social time"]
        plan["avoid"] = ["Excessive caffeine", "Poor sleep habits"]
    
    # Ovulation phase
    elif phase == "ovulation":
        plan["morning"] = [
            "🌅 High-energy breakfast with protein",
            "🏋️ Peak workout time - high intensity OK",
            "✨ Confidence-building activity"
        ]
        plan["afternoon"] = [
            "💼 Focus on important tasks and goals",
            "🥗 Nutrient-dense lunch",
            "🎯 Peak productivity window"
        ]
        plan["evening"] = [
            "🎉 Social activities or celebrations",
            "💃 Dance or joyful movement",
            "🍽️ Hydrating drinks, moderate meals"
        ]
        plan["throughout_day"] = ["Peak confidence and energy", "Important communications", "Public speaking"]
        plan["avoid"] = ["Schedule major surgery", "Make large financial decisions", "Extreme exercise"]
    
    # Luteal phase
    else:
        plan["morning"] = [
            "🌅 Warming tea or warm milk",
            "🧘 Gentle yoga or stretching",
            "🌙 Acknowledge need for rest"
        ]
        plan["afternoon"] = [
            "🚶 Moderate, consistent activity",
            "🥗 Magnesium-rich foods: dark chocolate, almonds",
            "🧘 Meditation or mindful breathing"
        ]
        plan["evening"] = [
            "🛀 Warm bath or self-care ritual",
            "📖 Journaling or quiet time",
            "😴 10+ hours sleep when possible"
        ]
        plan["throughout_day"] = ["Prioritize self-care", "Say no to extra commitments", "Eat magnesium-rich foods"]
        plan["avoid"] = ["Major decisions", "Intense confrontations", "High-stress situations"]
    
    # Add symptom-specific recommendations
    if "Cramps" in symptoms:
        plan["throughout_day"].insert(0, "🔥 Apply heat to lower abdomen (15-20 min)")
    if "Headache" in symptoms:
        plan["avoid"].append("Bright light exposure")
        plan["throughout_day"].insert(0, "🌙 Rest in dark, quiet room")
    if "Fatigue" in symptoms:
        plan["hydration_goal"] = 3000
        plan["throughout_day"].insert(0, "😴 Allow extra rest - your body needs it")
    if "Anxious" in symptoms:
        plan["throughout_day"].insert(0, "🧘 Deep breathing exercises (4-7-8 technique)")
        plan["throughout_day"].insert(1, "🚶 Nature walk for grounding")
    
    return plan


def get_ai_instant_suggestions(partial_symptom):
    """Get AI suggestions for partial symptom input (autocomplete)."""
    if not AI_AVAILABLE or not partial_symptom:
        # Fallback: Exact matching
        matching = [s for s in REMEDIES.keys() if s.lower().startswith(partial_symptom.lower())]
        return matching[:5]
    
    try:
        vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(2, 3), lowercase=True)
        all_symptoms = list(REMEDIES.keys())
        
        tfidf_matrix = vectorizer.fit_transform([partial_symptom] + all_symptoms)
        similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
        
        ranked = sorted(zip(all_symptoms, similarities), key=lambda x: x[1], reverse=True)
        suggestions = [symptom for symptom, score in ranked[:5] if score > 0.15]
        
        return suggestions
    except:
        return []

# --- Routes ---

@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    latest_log = Period.query.filter_by(user_id=session['user_id']).order_by(Period.start_date.desc()).first()
    
    countdown_text = "No Data"
    sub_text = "Log a period to see forecast"
    insight_message = "Log your period dates to get personalized daily insights and cycle forecasts."
    
    if latest_log:
        prediction_date = latest_log.start_date + timedelta(days=28)
        prediction_dt = datetime.combine(prediction_date, datetime.min.time())
        now = datetime.now()
        diff = prediction_dt - now
        total_seconds = diff.total_seconds()

        if total_seconds > 86400:
            countdown_text = f"in {diff.days + 1} days"
            sub_text = f"Expected {prediction_date.strftime('%b %d')}"
        elif 0 < total_seconds <= 86400:
            hours = int(total_seconds // 3600)
            countdown_text = f"in {max(hours, 1)} hours"
            sub_text = "Starting soon"
        elif diff.days == 0:
            countdown_text = "Today"
            sub_text = "Cycle Day 1"
        else:
            countdown_text = "Late"
            sub_text = f"{abs(diff.days)} days overdue"

        insight_message = get_cycle_insight(latest_log)
        
    return render_template('home.html', last_log=latest_log, countdown_text=countdown_text, sub_text=sub_text, insight_message=insight_message)

@app.route('/log_period', methods=['POST'])
def log_period():
    if 'user_id' not in session: return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    try:
        start_dt = datetime.strptime(data.get('start'), '%Y-%m-%d').date()
        end_dt = datetime.strptime(data.get('end'), '%Y-%m-%d').date()
        new_log = Period(start_date=start_dt, end_date=end_dt, user_id=session['user_id'])
        db.session.add(new_log)
        db.session.commit()
        return jsonify({"message": "Success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/save_symptoms', methods=['POST'])
def save_symptoms():
    if 'user_id' not in session: 
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    symptoms_list = data.get('symptoms', [])
    
    if not symptoms_list:
        return jsonify({"error": "No symptoms selected"}), 400

    try:
        new_log = SymptomLog(
            user_id=session['user_id'],
            symptoms=", ".join(symptoms_list),
            date=date.today()
        )
        db.session.add(new_log)
        db.session.commit()
        return jsonify({"message": "Symptoms recorded successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/weight', methods=['GET', 'POST'])
def weight():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            entry_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            value = float(request.form.get('value'))
            if value <= 0:
                raise ValueError('Value must be greater than zero')
            db.session.add(WeightLog(date=entry_date, value=value, user_id=session['user_id']))
            db.session.commit()
            flash('Weight entry saved.', 'success')
            return redirect(url_for('weight'))
        except Exception as e:
            flash(str(e), 'error')

    logs = WeightLog.query.filter_by(user_id=session['user_id']).order_by(WeightLog.date.asc()).all()
    return render_template('weight.html', logs=logs, today_date=date.today().isoformat())

@app.route('/temperature', methods=['GET', 'POST'])
def temperature():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        try:
            entry_date = datetime.strptime(request.form.get('date'), '%Y-%m-%d').date()
            value = float(request.form.get('value'))
            if value <= 0:
                raise ValueError('Value must be greater than zero')
            db.session.add(TemperatureLog(date=entry_date, value=value, user_id=session['user_id']))
            db.session.commit()
            flash('Temperature entry saved.', 'success')
            return redirect(url_for('temperature'))
        except Exception as e:
            flash(str(e), 'error')

    logs = TemperatureLog.query.filter_by(user_id=session['user_id']).order_by(TemperatureLog.date.asc()).all()
    return render_template('temperature.html', logs=logs, today_date=date.today().isoformat())

@app.route('/remedies')
def remedies():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('ai_analyzer'))


@app.route('/ai-analyzer', methods=['GET', 'POST'])
def ai_analyzer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']
    ai_result = None
    user_symptoms = ""
    symptoms_list = []
    auto_analyzed = False
    wellness_plan = None
    severity = None
    patterns = None
    phase, cycle_day = get_cycle_phase(user_id)
    
    # Check for today's symptoms and auto-analyze if found
    today_symptoms = SymptomLog.query.filter_by(
        user_id=user_id, 
        date=date.today()
    ).first()
    
    if today_symptoms and today_symptoms.symptoms:
        user_symptoms = today_symptoms.symptoms
        symptoms_list = [s.strip() for s in user_symptoms.split(',') if s.strip()]
        
        # Get AI analysis with confidence scores
        ai_result = ai_enhanced_remedies(symptoms_list, user_id, phase)
        auto_analyzed = True
        
        # Get severity assessment
        severity = get_symptom_severity_assessment(symptoms_list)
        
        # Get personalized wellness plan
        wellness_plan = get_personalized_wellness_plan(user_id)
    
    # Handle manual analysis if POST request and not auto-analyzed
    if request.method == 'POST' and not auto_analyzed:
        user_symptoms = request.form.get('symptoms', '').strip()
        
        if user_symptoms:
            symptoms_list = [s.strip() for s in user_symptoms.split(',') if s.strip()]
            ai_result = ai_enhanced_remedies(symptoms_list, user_id, phase)
            severity = get_symptom_severity_assessment(symptoms_list)
            wellness_plan = get_personalized_wellness_plan(user_id)
    
    # Always get symptom patterns/trends for the user
    patterns = get_symptom_patterns(user_id)
    
    return render_template('ai_analyzer.html',
                         ai_available=AI_AVAILABLE,
                         ai_result=ai_result,
                         user_symptoms=user_symptoms,
                         symptoms_list=symptoms_list,
                         auto_analyzed=auto_analyzed,
                         wellness_plan=wellness_plan,
                         severity=severity,
                         patterns=patterns,
                         phase=phase,
                         cycle_day=cycle_day)

# --- Enhanced AI API Routes ---

@app.route('/api/symptom-suggestions', methods=['POST'])
def symptom_suggestions():
    """Get AI suggestions for partial symptom input."""
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    partial = data.get('query', '').strip()
    
    if not partial or len(partial) < 1:
        return jsonify({"suggestions": []})
    
    suggestions = get_ai_instant_suggestions(partial)
    return jsonify({"suggestions": suggestions})


@app.route('/api/symptom-patterns', methods=['GET'])
def symptom_patterns():
    """Get user's symptom patterns and trends."""
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    patterns = get_symptom_patterns(session['user_id'])
    return jsonify(patterns)


@app.route('/api/wellness-plan', methods=['GET'])
def wellness_plan():
    """Get personalized daily wellness plan."""
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    plan = get_personalized_wellness_plan(session['user_id'])
    return jsonify(plan)


@app.route('/api/symptom-severity', methods=['POST'])
def symptom_severity():
    """Assess severity of current symptoms."""
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    symptoms_list = data.get('symptoms', [])
    
    if not symptoms_list:
        return jsonify({"error": "No symptoms provided"}), 400
    
    severity = get_symptom_severity_assessment(symptoms_list)
    return jsonify(severity)


@app.route('/calendar')
def calendar_view():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_logs = Period.query.filter_by(user_id=session['user_id']).all()
    prediction = None
    latest_log = Period.query.filter_by(user_id=session['user_id']).order_by(Period.start_date.desc()).first()
    if latest_log:
        prediction = latest_log.start_date + timedelta(days=28)

    actual_period_days, predicted_period_days, fertile_days, ovulation_day = build_calendar_highlights(user_logs, latest_log)
    today_str = date.today().isoformat()

    return render_template('calendar.html', logs=user_logs, prediction=prediction,
                           actual_period_days=actual_period_days,
                           predicted_period_days=predicted_period_days,
                           fertile_days=fertile_days,
                           ovulation_day=ovulation_day,
                           today=today_str)

@app.route('/profile')
def profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    user = db.session.get(User, session['user_id'])
    log_count = Period.query.filter_by(user_id=user.id).count()
    return render_template('profile.html', user=user, log_count=log_count)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form.get('email')).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            session['user_id'] = user.id
            return redirect(url_for('home'))
        else:
            flash('Invalid email or password.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        hashed = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
        new_user = User(name=request.form.get('name'), email=email, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/symptoms')
def symptoms():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('symptoms.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/change_password', methods=['POST'])
def change_password():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json()
    new_password = data.get('new_password')
    if not new_password or len(new_password) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    user = db.session.get(User, session['user_id'])
    user.password = generate_password_hash(new_password, method='pbkdf2:sha256')
    db.session.commit()
    return jsonify({'message': 'Password updated successfully'})

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user = db.session.get(User, session['user_id'])
    db.session.delete(user)
    db.session.commit()
    session.clear()
    return '', 200

if __name__ == '__main__':
    app.run(debug=True)                  
