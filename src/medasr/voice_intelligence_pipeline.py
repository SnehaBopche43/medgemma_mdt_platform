"""Complete Voice Intelligence Pipeline"""

import sys
sys.path.append('src')

from medasr.medical_transcription import MedASRTranscriber
from medasr.phi_redaction import PHIRedactor
from datetime import datetime
import json
from pathlib import Path

class VoiceIntelligencePipeline:
    def __init__(self):
        print("\n" + "="*80)
        print("🏥 VOICE INTELLIGENCE PIPELINE")
        print("="*80 + "\n")
        
        self.transcriber = MedASRTranscriber()
        self.phi_redactor = PHIRedactor()
        
        Path("outputs/voice_intelligence").mkdir(parents=True, exist_ok=True)
        
        print("="*80)
        print("✅ PIPELINE READY")
        print("="*80 + "\n")
    
    def process_audio(self, audio_path, case_id):
        print(f"\n{'='*80}")
        print(f"🎤 PROCESSING: {case_id}")
        print(f"{'='*80}\n")
        
        # Step 1: Transcribe
        transcription = self.transcriber.transcribe(audio_path, case_id)
        
        # Step 2: Redact PHI
        redacted = self.phi_redactor.redact(transcription['transcript'])
        
        # Results
        results = {
            'case_id': case_id,
            'timestamp': datetime.now().isoformat(),
            'transcription': {
                'redacted': redacted['redacted_transcript'],
                'word_count': transcription['word_count'],
                'phi_redacted': redacted['redaction_count']
            }
        }
        
        # Save
        output_file = Path(f"outputs/voice_intelligence/{case_id}_complete.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"{'='*80}")
        print(f"✅ COMPLETE")
        print(f"{'='*80}\n")
        print(f"📊 Words: {results['transcription']['word_count']}")
        print(f"🔒 PHI Redacted: {results['transcription']['phi_redacted']}")
        print(f"💾 Saved: {output_file}\n")
        
        return results

if __name__ == "__main__":
    pipeline = VoiceIntelligencePipeline()
    results = pipeline.process_audio("test.wav", "DEMO_001")
    print("✅ Test complete!")
