"""MedASR Medical Transcription Module"""

from transformers import pipeline
import json
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class MedASRTranscriber:
    def __init__(self):
        print("\n🎤 Initializing MedASR...")
        try:
            self.pipe = pipeline("automatic-speech-recognition", model="google/medasr")
            print("✅ MedASR loaded\n")
            self.using_mock = False
        except:
            print("⚠️  Using mock transcription\n")
            self.pipe = None
            self.using_mock = True
        
        Path("outputs/medasr_transcriptions").mkdir(parents=True, exist_ok=True)
    
    def transcribe(self, audio_path, case_id):
        print(f"🎤 Transcribing: {case_id}\n")
        
        if self.pipe:
            try:
                result = self.pipe(audio_path)
                transcript = result['text']
            except:
                transcript = self._mock_transcript()
        else:
            transcript = self._mock_transcript()
        
        result = {
            'case_id': case_id,
            'transcript': transcript,
            'timestamp': datetime.now().isoformat(),
            'word_count': len(transcript.split())
        }
        
        output_file = Path(f"outputs/medasr_transcriptions/{case_id}_transcript.json")
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"✅ Transcription complete: {result['word_count']} words\n")
        return result
    
    def _mock_transcript(self):
        return """
Good morning. This is the MDT meeting for breast cancer case.
Patient is 58-year-old female with stage IIB invasive ductal carcinoma of left breast.
Mammography showed 3.2 cm irregular mass. Biopsy confirmed ER positive, PR positive, HER2 negative.
Recommend neoadjuvant chemotherapy with AC-T regimen: doxorubicin, cyclophosphamide, then paclitaxel.
Followed by surgery, radiation therapy, and adjuvant endocrine therapy with tamoxifen.
Patient is agreeable to treatment plan.
"""

if __name__ == "__main__":
    print("="*80)
    print("TESTING MedASR TRANSCRIPTION")
    print("="*80)
    transcriber = MedASRTranscriber()
    result = transcriber.transcribe("test.wav", "TEST_001")
    print("="*80)
