# 📚 baybayin_learning_app

**Baybayin Learning App** is an AI-powered web and mobile platform that promotes holistic Baybayin literacy through interactive, gamified learning. Designed for learners of all levels, the app adapts to each user's pace and performance using intelligent feedback and progression tracking. Mastery is reinforced through personalized challenges, dynamic quizzes, and modular content.

The system also integrates a robust **transliteration pipeline** between Baybayin and modern Latin-based Tagalog, enabling users to input content via:

- ✍️ Text input with a virtual Baybayin keyboard  
- 📷 Image upload  
- 📹 Real-time camera capture  

These inputs undergo OCR (Optical Character Recognition), binarization, and transliteration for accurate recognition and translation of the script.

---

## 🚀 Key Features

| Feature Category         | Description                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| 🔤 Transliteration       | Convert between Latin and Baybayin scripts                                  |
| 📷 OCR Input             | Recognizes latin or baybayin script from images                              |
| ⌨️ Virtual Keyboard       | Type in Baybayin using an intuitive, on-screen keyboard                    |
| 🧠 Adaptive Learning     | Adjusts difficulty and content based on learner’s pace and accuracy         |
| 🧩 Gamified Activities   | Interactive games and quizzes designed to reinforce learning in fun ways    |
| 🏆 Leaderboard & Rewards | Tracks progress and motivates learners via scores, ranks, and achievements |
| 📖 Spell Checker         | Tagalog-aware          spelling correction and suggestions                 |
| 📊 Dashboard Analytics   | Visual reports on learning progress and transliteration history             |
| 📊 Baybayin History     | Page that illustrates baybayin history, writing system, etc.          |

---

## 🗂️ Project Structure

### 🔧 Backend (`baybayin_backend/`)
```bash
baybayin_backend/
├── baybayin_backend/ 
├── common/
├── data/                        
├── preprocessing/          
├── tagalog_spelling_checker/ 
├── transliteration/
└── manage.py
└── requirements.txt
```

### 🌐 Frontend (`baybayin_frontend/`)
```bash
baybayin_frontend/
src/
│
├── app/
│   │
│   ├── core/                    
│   │   ├── services/
│   │   │   ├── auth.service.ts
│   │   │   ├── transliteration.service.ts
│   │   │   ├── firestore.service.ts
│   │   │   ├── user.service.ts
│   │   │   ├── quiz.service.ts
│   │   │   ├── spelling.service.ts
│   │   │   ├── history.service.ts
│   │   │   └── admin.service.ts
│   │   ├── interceptors/
│   │   │   └── auth-token.interceptor.ts
│   │   ├── guards/
│   │   │   ├── auth.guard.ts
│   │   │   └── admin.guard.ts
│   │   └── core.module.ts
│   ├── tabs/
│   │   ├── tabs.page.ts
│   │   ├── tabs.page.html
│   │   └── tabs-routing.module.ts
│   ├── features/
│   │   ├── auth/               
│   │   ├── user/
│   │   │   ├── home/
│   │   │   ├── lessons/
│   │   │   ├── quiz/
│   │   │   ├── transliteration/
│   │   │   ├── spelling-checker/
│   │   │   ├── profile/
│   │   │   └── history/       
│   │   ├── admin/  
│   │   │   ├── dashboard/      
│   │   │   ├── users/
│   │   │   ├── lessons/ 
│   │   │   ├── quizzes/
│   │   │   ├── history/  
│   │   │   └── reports/
│   ├── assets/               
│   ├── environments/
│   │   ├── environment.ts
│   │   └── environment.prod.ts
│   └── app.module.ts
│
├── theme/      
├── index.html
└── main.ts
