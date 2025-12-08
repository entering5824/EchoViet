Topic 7. Designing and Developing a Vietnamese Speech to Text System for
Automatic Meeting Transcription
Problem description
Develop an intelligent Vietnamese speech to text system capable of converting
spoken audio from meetings, discussions, interviews, or presentations into accurate and
structured text transcripts. The system should support audio upload, noise handling,
speech segmentation, and transcription using machine learning or deep learning models.
Students may experiment with cloud based APIs, pretrained models, or open source
speech recognition frameworks. The system must allow users to upload or record
Vietnamese audio files, visualize waveform or spectrogram representations, generate
transcripts, and provide options to edit or export the final text. The application should
also support detecting speaker turns if possible, handling long audio sessions, and
producing clean, readable output suitable for business, academic, or administrative use.
Technology Usage Policy
Students may select one of the following implementation approaches depending
on resource availability:
a. GCP based implementation (recommended):
Students with a Visa enabled bank card may activate a Google Cloud Platform
account and utilize services such as Cloud Speech to Text API, Cloud Storage, BigQuery,
AutoML Natural Language, and Cloud Run for processing, transcribing, and deploying
the Vietnamese speech to text system.
b. Open source implementation (alternative):
Students without Visa enabled cards may develop the entire system using
open source technologies. Suitable tools include Vosk, Whisper, Mozilla DeepSpeech,
Librosa, PyDub, and deployment frameworks such as Streamlit, FastAPI, Docker,
Hugging Face Spaces, Render, or Railway.
Both approaches are acceptable, and students may choose the method that best
fits their financial and technical conditions.

Page 15/16
BM03/QT01/K.IT
Objectives
Academic: Strengthen understanding of speech processing concepts, including
signal processing, feature extraction, acoustic modeling, language modeling, and
evaluation metrics for transcription quality.
Practical skills: Develop skills in processing Vietnamese audio data, applying
speech recognition techniques, visualizing waveforms and spectrograms, generating text
transcripts, and deploying speech to text applications.
Real world application: Build a practical Vietnamese meeting transcription system
that supports businesses, classrooms, customer service centers, and administrative tasks
by converting spoken content into structured and searchable text.
Requirements
1. Technologies used
Programming Language: Python
Speech Processing Libraries: Librosa, PyDub, SoundFile
Speech Recognition Libraries: Vosk, Whisper, Mozilla DeepSpeech, or Cloud
Speech to Text
Machine Learning Libraries: TensorFlow, Keras, Scikit learn (optional)
Visualization Tools: Matplotlib, Seaborn
Application/Deployment: Streamlit, FastAPI, or cloud platforms
Version Control: Git/GitHub/GitLab
Optional Tools: Docker, Hugging Face Spaces, Joblib for model serialization,
NLTK or SpaCy for text post processing
2. Main Functions
a. Basic Functions
- Audio Input and Management
+ Upload Vietnamese audio files in WAV, MP3, or FLAC format.
+ Visualize waveform and spectrogram.
+ Perform audio preprocessing such as noise reduction or normalization.
- Speech Recognition
+ Convert speech to text using selected speech recognition models or APIs.
+ Support different lengths of audio, including long meeting recordings.
+ Display real time or batch transcription output.
- Transcript Editing and Formatting
+ Allow users to edit, clean, and format transcription results.
+ Support punctuation insertion, text segmentation, and timestamping.
- Exporting and Reporting
+ Export transcripts in TXT, DOCX, or PDF format.
+ Provide summary statistics such as word counts or speaking duration.
b. Advanced Functions
- Speaker Diarization
+ Detect and label different speakers (Speaker 1, Speaker 2, etc.).
+ Visualize speaker turns along the timeline.
- Real time Streaming Transcription
+ Support live audio input through microphone streaming.
+ Display real time speech to text results.

Page 16/16
BM03/QT01/K.IT
- AI based Text Enhancement
+ Apply language models to improve grammar, punctuation, and text readability.
+ Provide keyword extraction or topic summarization.
- API Integration
+ Provide an API endpoint for uploading audio files and receiving transcripts.
+ Support JSON output for external applications (optional)
- Deployment
+ Deploy the complete system using Cloud Run, Streamlit Cloud, or Hugging Face
Spaces