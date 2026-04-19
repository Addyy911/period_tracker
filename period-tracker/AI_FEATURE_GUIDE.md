# 🧠 AI Remedy Analyzer - Emerging Tech Feature

## Overview
FlowGreen now includes an **AI-powered Intelligent Remedy Analyzer** - your period tracker's emerging technology feature. This system uses machine learning to provide personalized wellness recommendations based on your symptoms.

## What It Does

### 1. **Intelligent Symptom Matching**
- Uses TF-IDF (Term Frequency-Inverse Document Frequency) vectorization from scikit-learn
- Performs cosine similarity analysis to match user symptoms with our comprehensive remedy database
- Provides confidence scores (0-100%) for each recommendation

### 2. **Dual-Layer Analysis**
- **Direct Matches**: Exact symptom matches from the traditional database
- **AI-Powered Recommendations**: Machine learning-based fuzzy matching for symptom variations
- Both layers are combined for comprehensive coverage

### 3. **Cycle-Phase Aware**
- Analyzes your current cycle phase (menstruation, follicular, ovulation, luteal)
- Provides phase-specific insights alongside remedies
- Tailors recommendations based on hormonal patterns

### 4. **Multi-Path Solutions**
Each recommendation includes:
- 💊 Primary Treatment/Advice
- 🔄 Alternative Options
- 🥗 Nutritional Support
- Severity Classification (mild, moderate, common, etc.)

## How to Use

### Access the AI Analyzer:
1. Click the **🧠 AI** button in the top navigation
2. Or go directly to `/ai-analyzer`

### Using the Analyzer:
1. Enter your symptoms in the textarea
2. Separate multiple symptoms with commas
   - Example: `Cramps, Bloating, Headache, Fatigue`
3. Click "🔍 Analyze with AI"
4. View comprehensive recommendations with confidence scores

### View AI Results on Remedies Page:
If you log symptoms for today:
1. Go to the **REMEDIES** page
2. View both recognized and AI-recommended solutions
3. Click **🧠 AI Analyzer** for in-depth analysis

## Technical Details

### Machine Learning Algorithm
- **Vectorization**: TF-IDF with character-level n-grams (2-3 character sequences)
- **Similarity Metric**: Cosine Similarity (0.0 to 1.0 scale)
- **Confidence Threshold**: 20% minimum match confidence
- **Top Results**: Returns up to 10 recommendations per query

### Why This Approach?
- **No External API**: All processing happens locally on your device
- **Privacy-First**: Your symptoms never leave your computer
- **Fast Processing**: Instant analysis without network delays
- **Adaptable**: Can learn from new symptoms as the database grows

### Symptom Database
The AI has access to 25+ symptom categories including:
- Physical symptoms (cramps, bloating, headache, fatigue, etc.)
- Mood changes (irritable, anxious, sad, happy)
- Discharge variations (dry, creamy, egg white, spotting)
- Cravings (sweet, salty)
- Energy levels and more

## AI Accuracy & Limitations

### Strengths ✓
- Excellent at partial/misspelled symptom matching
- Considers character similarity and phonetic closeness
- Works with singular/plural variations
- Handles abbreviations and informal language

### Limitations ⚠️
- Works best with 1-3 symptom queries
- May suggest unrelated remedies for very vague symptoms
- Requires somewhat descriptive symptom names (single letters won't work well)
- Always consult a healthcare provider for serious symptoms

## Tips for Better Results

1. **Be Specific**: "Heavy bloating" works better than "bloating"
2. **Use Common Terms**: Stick to symptom names in our database when possible
3. **Separate Clearly**: Use commas to separate each symptom
4. **Multiple Queries**: Try running analysis 2-3 different ways for comprehensive results
5. **Trust Direct Matches More**: Symptoms with 80%+ confidence are most reliable

## Example Queries

✅ **Good Queries**:
- "Cramps, Heavy bleeding, Iron deficiency"
- "Mood swings, Anxiety, Irritability"
- "Bloating, Water retention, Weight gain"

❌ **Less Effective Queries**:
- "Stuff hurts"
- "Feel weird"
- "Help"

## Settings & Configuration

The AI analyzer is enabled and configured with:
- **TF-IDF Parameters**: Character n-grams (2,3) for flexible matching
- **Minimum Confidence**: 20% threshold
- **Max Recommendations**: 10 per analysis
- **Processing**: Local machine learning (no cloud/API required)

## Privacy & Security

✓ **Your data is safe**:
- All AI processing happens locally on your device
- No symptoms are sent to external servers
- No AI training on personal data
- Completely private analysis

## Future Enhancements

Planned improvements:
- Pattern recognition across multiple days
- Predictive symptom forecasting
- Personalized remedy effectiveness tracking
- Integration with weight/temperature logs
- Custom remedy suggestions based on user preferences

## Troubleshooting

**Q: AI Analyzer shows "System Loading"**
- A: Scikit-learn is initializing. Refresh the page in a moment.

**Q: No matches found for my symptoms**
- A: Try alternative symptom names or check the symptoms guide.

**Q: Confidence scores seem low**
- A: The symptoms might be quite different from our database. Consider checking the direct matches.

**Q: I want to disable AI**
- A: The AI is optional. Use the traditional remedies page if you prefer.

---

**Last Updated**: April 2026 | **Version**: 1.0 | **Status**: Active & Monitoring Performance
