# GULA Learning Platform

## 1. Learning Platform Architecture

The GULA Learning Platform is a microservices-based intelligent learning ecosystem
integrated into the GULA healthcare platform. It enables continuous professional
development, certification management, and competency tracking for all healthcare
personnel across Iraqi medical laboratories and affiliated institutions.

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         API Gateway (nginx)                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │   LMS    │ │   CMS    │ │Assessment│ │   Cert   │ │  Analytics│ │
│  │  Core    │ │          │ │ Engine   │ │  Engine  │ │& Reporting│ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       │            │            │            │            │        │
│  ┌────┴────────────┴────────────┴────────────┴────────────┴─────┐ │
│  │                    Recommendation Engine (AI)                 │ │
│  └────────────────────────────┬─────────────────────────────────┘ │
│                               │                                    │
│  ┌────────────────────────────┴─────────────────────────────────┐ │
│  │                Social Learning Features                      │ │
│  └────────────────────────────┬─────────────────────────────────┘ │
│                               │                                    │
│  ┌────────────────────────────┴─────────────────────────────────┐ │
│  │                  Mobile Learning Support                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│                    Common Services Layer                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │  Auth    │ │  Search  │ │Storage   │ │Notification│ │  Cache   │
│  │ (SSO)    │ │ (ES)     │ │ (S3)     │ │(Push/SMS) │ │ (Redis)  │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
├─────────────────────────────────────────────────────────────────────┤
│                      GULA Core Integration                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ User    │ │ Patient  │ │  Order   │ │  Result  │ │  Audit   │ │
│  │ Service │ │ Service  │ │  Service │ │  Service │ │  Service │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### Microservice Components

| Service | Responsibility | Technology |
|---------|---------------|------------|
| **LMS Core** | Course management, enrollment, scheduling, progress tracking | FastAPI, PostgreSQL 16 |
| **Content Management System** | Content creation, versioning, localization, media management | FastAPI, S3-compatible storage |
| **Assessment Engine** | Quiz/exam creation, delivery, scoring, proctoring | FastAPI, PostgreSQL 16 |
| **Certification Engine** | Certificate issuance, verification, revocation | FastAPI, Blockchain anchoring |
| **Analytics & Reporting** | Learning analytics, dashboards, export | FastAPI, ClickHouse, Redis 7 |
| **Recommendation Engine** | AI-powered path generation, content recommendations | FastAPI, ML models (ONNX) |
| **Social Learning** | Forums, discussion, peer review, mentorship | FastAPI, WebSockets |
| **Mobile Learning** | Offline sync, mobile-optimized content delivery | FastAPI, React Native |

### Data Flow

```
User Action → API Gateway → Auth Validation → Service Router → 
Business Logic → Event Emission → Async Processing → Notification
```

### Key Design Decisions

1. **Arabic-first schema**: All content tables use `citext` with Arabic collation,
   RTL-aware text indexing, and bidirectional string support.
2. **Offline-capable**: Mobile learning uses a CRDT-based sync protocol for
   offline content consumption and progress synchronization.
3. **Event-driven**: All learning events (enrollment, completion, assessment
   passing) are published to the GULA EventBus for cross-platform reactions.
4. **Tenant-isolated**: All learning data is scoped by `lab_id` with
   cross-tenant admin visibility for platform administrators.
5. **Audit-everywhere**: Every learning action is logged through the GULA
   AuditService with immutable hash-chain integrity.

---

## 2. User Personas

### Doctors

| Attribute | Detail |
|-----------|--------|
| **Role** | Physicians, specialists, consultants |
| **Learning Needs** | Clinical updates, diagnostic guidelines, AI-assisted diagnosis training, drug interaction alerts, evidence-based medicine |
| **Pain Points** | Limited CME access in Iraq, outdated protocols, language barriers with English-only resources |
| **Preferred Format** | Video lectures (15-20 min), case-based simulations, mobile-accessible microlearning |
| **Assessment** | Case-based MCQ, simulated diagnostic reasoning |
| **CME Requirements** | 50 CME hours/year (Iraqi MoH requirement) |
| **GULA Modules** | Clinical Decision Support, AI Diagnostics, Result Interpretation, Patient Card System |

### Nurses

| Attribute | Detail |
|-----------|--------|
| **Role** | Registered nurses, practical nurses, nursing assistants |
| **Learning Needs** | Patient care protocols, lab sample collection techniques, critical value response, infection control |
| **Pain Points** | Shift-based schedules make synchronous learning difficult, varied educational backgrounds |
| **Preferred Format** | Short videos (5-10 min), interactive checklists, mobile-friendly quick references |
| **Assessment** | Procedural checklists, scenario-based questions |
| **CME Requirements** | 30 CME hours/year |
| **GULA Modules** | Sample Collection & Handling, Critical Value Management, Patient Identity Management |

### Laboratory Staff

| Attribute | Detail |
|-----------|--------|
| **Role** | Medical laboratory scientists, technicians, phlebotomists |
| **Learning Needs** | Instrument operation, quality control procedures, result interpretation, LOINC coding, ISO 15189 compliance |
| **Pain Points** | High employee turnover, varying instrument models across labs, Arabic terminology gaps |
| **Preferred Format** | Interactive simulations, step-by-step instrument guides, QC troubleshooting scenarios |
| **Assessment** | Practical exams on instrument operation, QC data interpretation |
| **CME Requirements** | 40 CME hours/year |
| **GULA Modules** | Full Clinical Laboratory Track (20+ modules) |

### Pharmacists

| Attribute | Detail |
|-----------|--------|
| **Role** | Hospital pharmacists, clinical pharmacists, community pharmacists |
| **Learning Needs** | Drug interactions, therapeutic drug monitoring, formulary management, medication safety |
| **Pain Points** | Limited integration between lab results and pharmacy systems |
| **Preferred Format** | Case studies, interaction databases, mobile reference tools |
| **Assessment** | Drug interaction identification, TDM interpretation |
| **CME Requirements** | 40 CME hours/year |
| **GULA Modules** | Clinical Decision Support, AI Diagnostics |

### Radiology Staff

| Attribute | Detail |
|-----------|--------|
| **Role** | Radiologists, radiologic technologists, MRI technicians |
| **Learning Needs** | Imaging protocols, AI-assisted reading, contrast safety, radiation dose management |
| **Pain Points** | Rapidly evolving AI tools, protocol standardization across facilities |
| **Preferred Format** | Image-rich modules, side-by-side AI comparison, video demonstrations |
| **Assessment** | Image interpretation, protocol selection exams |
| **CME Requirements** | 50 CME hours/year |
| **GULA Modules** | AI-Assisted Diagnostics, Clinical Documentation |

### Administrators

| Attribute | Detail |
|-----------|--------|
| **Role** | Lab managers, hospital administrators, system admins |
| **Learning Needs** | Platform management, user/role administration, compliance training, reporting, subscription management |
| **Pain Points** | Need to train entire staff, audit preparation, regulatory compliance burden |
| **Preferred Format** | Documentation, video walkthroughs, administrative playbooks |
| **Assessment** | Platform administration practical exam |
| **CME Requirements** | 20 CME hours/year (management track) |
| **GULA Modules** | Full Administrator Track (15+ modules) |

### Researchers

| Attribute | Detail |
|-----------|--------|
| **Role** | Clinical researchers, public health analysts, data scientists |
| **Learning Needs** | Population health analytics, clinical trial management, data science tools, research ethics |
| **Pain Points** | Need access to de-identified datasets, complex analytics tools |
| **Preferred Format** | Interactive notebooks, statistical tool tutorials, research methodology modules |
| **Assessment** | Research protocol design, data analysis exercises |
| **CME Requirements** | N/A (research track) |
| **GULA Modules** | Population Health Analytics, National Health Oversight |

### Students

| Attribute | Detail |
|-----------|--------|
| **Role** | Medical students, nursing students, lab science students, interns |
| **Learning Needs** | Medical/lab science curriculum, internship training, GULA platform orientation |
| **Pain Points** | Limited practical exposure, theory-practice gap |
| **Preferred Format** | Structured curriculum, interactive simulations, mentor-guided learning |
| **Assessment** | Progressive exams, practical assessments, portfolio |
| **CME Requirements** | N/A (student track) |
| **GULA Modules** | Intro to GULA LIMS, Lab Order Management, Sample Collection & Handling |

### Developers

| Attribute | Detail |
|-----------|--------|
| **Role** | Third-party developers, integration partners, open-source contributors |
| **Learning Needs** | Platform SDK, API usage, extension/plugin development, custom integration |
| **Pain Points** | Need sandbox environment, comprehensive API documentation, SDK examples |
| **Preferred Format** | Interactive API playgrounds, SDK tutorials, code samples, hackathons |
| **Assessment** | Build-and-submit (practical project), API proficiency exam |
| **CME Requirements** | N/A (developer track) |
| **GULA Modules** | Full Developer Track (15+ modules) |

### Engineers

| Attribute | Detail |
|-----------|--------|
| **Role** | DevOps engineers, system administrators, infrastructure teams |
| **Learning Needs** | Deployment guide, Docker/containerization, monitoring/alerting, disaster recovery, scaling |
| **Pain Points** | Complex deployment topology, production incident response |
| **Preferred Format** | Hands-on labs, runbooks, infrastructure-as-code workshops |
| **Assessment** | Deployment simulation, incident response drill |
| **CME Requirements** | N/A (infrastructure track) |
| **GULA Modules** | Full Infrastructure Track (10+ modules) |

---

## 3. Personalized Learning Paths

### AI-Driven Path Generation

The Recommendation Engine generates personalized learning paths using:

1. **Input Signals**:
   - User role and seniority level
   - Pre-assessment scores (baseline competency)
   - Performance gaps identified from platform usage patterns
   - Historical learning data and preferences
   - Manager/supervisor recommendations
   - Regulatory deadline requirements (CME accrual)

2. **Path Generation Algorithm**:

```
Input → Role Analysis → Competency Gap Analysis → 
Prerequisite Resolution → Learning Object Selection → 
Sequence Optimization → Personalized Path Output
```

3. **Path Types**:

| Path Type | Description | Duration |
|-----------|-------------|----------|
| **Onboarding Path** | New user orientation to GULA platform | 1-2 weeks |
| **Competency Path** | Fill identified competency gaps | 2-8 weeks |
| **Certification Path** | Prepare for specific certification | 4-16 weeks |
| **CME Path** | Annual continuing education requirements | 12 months |
| **Advanced Path** | Deep dive into specialized topics | 4-12 weeks |
| **Refresh Path** | Periodic knowledge refresh | 1-2 weeks |

4. **Adaptive Learning**: Paths adjust in real-time based on:
   - Assessment performance (mastery-based progression)
   - Time spent on learning objects
   - Engagement patterns
   - New regulatory requirements

### Path Visualization

```
User Dashboard → My Learning Path
├── In Progress (current path with progress bar)
├── Recommended (AI-generated suggestions)
├── Completed (historical paths with certificates)
└── Available (certifications, electives)
```

---

## 4. Competency Framework Integration

The Learning Platform is tightly coupled with the GULA Competency Framework
(see `COMPETENCY_FRAMEWORK.md`).

### Mapping Architecture

```
Competency Framework → Learning Platform
├── Competency Dimensions → Module Categories
├── Proficiency Levels → Path Milestones
├── Role Requirements → Required Learning Paths
├── Assessment Methods → Assessment Engine Configuration
├── Certification Paths → Certification Engine Workflows
└── CME Requirements → Recurring Learning Plans
```

### Integration Points

| Framework Element | Platform Implementation |
|-------------------|------------------------|
| Competency Dimensions | Module category tags, content metadata |
| Proficiency Levels | Pre-assessment → level placement → learning path |
| Role Competency Matrix | Role-based learning path templates |
| Assessment Methods | Configurable assessment templates |
| Certification Paths | Automated certification workflows |
| CME Requirements | Annual learning plan generation, reminders |

---

## 5. Training Modules

### Module Types

| Type | Description | Delivery | Interactivity |
|------|-------------|----------|---------------|
| **Video** | Pre-recorded lectures, demonstrations, screencasts | Streaming (HLS) | Low |
| **Interactive** | Click-through tutorials, branching scenarios | Web-based | High |
| **Simulation** | Virtual lab instrument operation, diagnostic reasoning | Web-based with 3D/2D | Very High |
| **Assessment** | Quizzes, exams, practical evaluations | Web-based | Medium |
| **Document** | PDF guides, reference manuals, SOP documents | Download/View | Low |
| **Webinar** | Live instructor-led sessions | Video conferencing | Medium |
| **Microlearning** | 3-5 minute focused learning nuggets | Mobile/web | Medium |
| **Case Study** | Real-world clinical scenarios with analysis | Web-based | High |
| **Hands-on Lab** | Sandbox environment for practical exercises | Cloud-based environment | Very High |
| **Social** | Discussion-based learning, peer review | Web-based | Medium |

### Module Structure

```json
{
  "module_id": "CL-TRAIN-001",
  "title_ar": "مقدمة في نظام جولا للمختبرات",
  "title_en": "Introduction to GULA LIMS",
  "type": "interactive",
  "duration_minutes": 45,
  "languages": ["ar", "en"],
  "prerequisites": [],
  "learning_objectives": [
    "Understand GULA platform architecture",
    "Navigate the main dashboard",
    "Perform basic patient search"
  ],
  "content": { ... },
  "assessment": { "type": "quiz", "pass_threshold": 80 },
  "competency_mapping": ["TECH-01", "TECH-02"],
  "certification_credit": 1.5
}
```

---

## 6. Certification Exams

### Exam Design

| Component | Description |
|-----------|-------------|
| **Question Bank** | Tagged, versioned, reviewed by subject matter experts |
| **Question Types** | MCQ, true/false, matching, drag-and-drop, fill-in-blank, case-based, simulation |
| **Exam Blueprint** | Content distribution by competency, difficulty level |
| **Adaptive Testing** | Computer-adaptive testing (CAT) for advanced certifications |
| **Time Limits** | Configurable per exam, with accommodations |
| **Pass Threshold** | Varies by certification (typically 70-85%) |
| **Attempts** | 3 attempts per exam, 30-day cooldown between attempts |

### Delivery

| Mode | Description |
|------|-------------|
| **Online Proctored** | AI proctoring with live human review |
| **In-Person** | At GULA training centers or partner facilities |
| **Self-Paced** | Non-proctored practice exams |
| **On-Site** | At customer lab locations for group certifications |

### Proctoring

The online proctoring system includes:

1. **Identity Verification**: Photo capture, ID document scan, liveness detection
2. **Environment Scan**: 360-degree room scan via webcam
3. **Behavior Monitoring**: Gaze detection, multiple face detection, audio monitoring
4. **Screen Monitoring**: Application detection, browser lockdown
5. **AI Flagging**: Suspicious behavior alerts for human review
6. **Recording**: Full session recording for audit

### Certification Exam Workflow

```
User Enrolls → Prerequisites Verified → Exam Scheduled → 
Identity Check → Environment Scan → Exam Delivery → 
AI Proctoring → Human Review (if flagged) → 
Score Calculation → Result Notification → Certificate Issuance
```

---

## 7. Skill Assessment

### Pre-Assessment

Conducted at the beginning of a learning path to establish baseline competency:

- **Diagnostic Quiz**: 10-20 questions covering path objectives
- **Self-Assessment**: User rates their confidence per competency
- **Manager Assessment**: Supervisor evaluates current competency level
- **Platform Analytics**: Automated analysis of platform usage patterns

### Post-Assessment

Conducted after learning path completion to measure growth:

- **Summative Exam**: Comprehensive assessment of all path objectives
- **Practical Demonstration**: Hands-on task completion
- **Case Study Analysis**: Applied knowledge assessment
- **Peer Review**: Colleague evaluation (for soft skills)

### Gap Analysis

```
Pre-Assessment Result → Competency Target → Gap Identification → 
Learning Path Adjustment → Post-Assessment → Growth Measurement
```

### Reporting

| Report | Description | Audience |
|--------|-------------|----------|
| Individual Progress | Personal competency growth over time | Learner |
| Team Dashboard | Aggregate team competency levels | Manager |
| Organizational Heat Map | Department/role competency gaps | Administrator |
| Compliance Report | Mandatory training completion status | Compliance Officer |

---

## 8. Continuous Education (CME/CPD)

### CME Tracking

| Feature | Description |
|---------|-------------|
| **Credit Accrual** | Automatic tracking of completed learning hours |
| **Credit Categories** | Category 1 (formal), Category 2 (self-directed) |
| **Annual Targets** | Configurable by role, regulatory body |
| **Pro-Rata Tracking** | Monthly progress toward annual target |
| **Multi-Source** | GULA learning + external CME (manual entry) |
| **Approval Workflow** | External CME submission → manager approval |

### Automated Reminders

| Trigger | Notification | Channel |
|---------|--------------|---------|
| CME target behind schedule | "You are X hours behind your CME target" | Email, SMS, In-app |
| Certification expiring | "Your X certification expires in Y days" | Email, In-app |
| New relevant content | "New module matches your learning profile" | In-app, Push |
| Upcoming deadline | "CME reporting deadline in 30 days" | Email, SMS |
| Learning inactivity | "You haven't logged learning time in 14 days" | Email |

### CME Reporting

Annual CME reports are auto-generated for:

- Individual practitioners (for license renewal)
- Lab managers (for staff compliance)
- Hospital administrators (for accreditation)
- Ministry of Health (institutional reporting)

---

## 9. Gamification

### Badges

| Badge Category | Examples | Criteria |
|----------------|----------|----------|
| **Achievement** | First Course, Perfect Score, Speed Learner | Milestone completion |
| **Competency** | QC Master, LOINC Expert, ISO Pro | Competency level attainment |
| **Social** | Mentor, Discussion Leader, Peer Reviewer | Social contribution |
| **Streak** | 7-Day Streak, 30-Day Streak, Year of Learning | Consecutive learning days |
| **Certification** | GULA Certified, Gold Lab, Platinum Operator | Certification attainment |

### Leaderboards

| Leaderboard | Scope | Metrics |
|-------------|-------|---------|
| Department | Team members | CME hours, course completions |
| Lab | All lab staff | Aggregate competency score |
| National | All GULA users | Certifications earned |
| Developer | Third-party developers | Apps published, API proficiency |

### Challenges

- Monthly clinical case challenges with leaderboard rankings
- Speed-run challenges for instrument operation
- Team-based quality control competitions
- Hackathons for developer track

### Points & Levels

| Level | Title | Points Required | Benefits |
|-------|-------|----------------|----------|
| 1-5 | Novice | 0-500 | Basic access |
| 6-10 | Practitioner | 501-2000 | Advanced modules unlocked |
| 11-15 | Specialist | 2001-5000 | Mentorship eligibility |
| 16-20 | Expert | 5001-10000 | Beta feature access |
| 21-25 | Master | 10001+ | Trainer status, certification fee waiver |

---

## 10. Arabic-First Design

### RTL Support

All learning content supports full bidirectional (BiDi) text rendering:

- **UI Framework**: CSS logical properties, `dir="auto"` detection
- **Content Editor**: RTL-aware WYSIWYG editor with Arabic typography tools
- **Media**: Right-aligned diagrams, mirror-flipped demonstration videos
- **PDF Generation**: Arabic PDF rendering with proper glyph shaping
- **Assessment**: RTL-compatible question layouts, answer choices

### Arabic Content Creation Tools

| Tool | Description |
|------|-------------|
| **Arabic Text Editor** | RTL-aware editor with Arabic spell-check, diacritic support |
| **Medical Terminology Manager** | Arabic medical term database with English mapping |
| **Voiceover Studio** | Arabic text-to-speech for video narration |
| **Translation Workflow** | Source (Arabic) → Translation Memory → Review → Publish |
| **Localization Dashboard** | Per-language content completion status |

### Content Localization

Content is authored in Arabic as primary, with English as secondary:

1. **Original**: Arabic (primary authoring language)
2. **Translation**: English (professional medical translation)
3. **Review**: Subject matter expert bilingual review
4. **Regional Variants**: Iraqi dialect notes, terminology preferences

### Arabic Medical Terminology

The platform includes a comprehensive Arabic medical terminology database:

- 50,000+ Arabic medical terms with definitions
- English → Arabic mapping with Iraqi dialect preferences
- LOINC term translations to Arabic
- ICD-10/ICD-11 Arabic code descriptions
- Drug name transliterations

---

## 11. Integration Points

### Single Sign-On (SSO)

| Feature | Description |
|---------|-------------|
| **Authentication** | Learning platform uses GULA JWT tokens for authentication |
| **Role Sync** | User roles sync from GULA RBAC to learning platform |
| **Profile Sync** | Name, title, department, lab_id synced from GULA core |
| **Session Management** | Unified session across learning and core platform |

### Data Sync

| Data Element | Direction | Frequency | Mechanism |
|-------------|-----------|-----------|-----------|
| User Profile | GULA Core → Learning | Real-time | EventBus |
| User Roles | GULA Core → Learning | On change | EventBus |
| Lab Configuration | GULA Core → Learning | Daily | Batch sync |
| Patient Data | GULA Core → Learning (anonymized) | On demand | API call |
| Assessment Results | Learning → GULA Core | Real-time | EventBus |
| Certificates | Learning → GULA Core | On issuance | API callback |
| CME Records | Learning → GULA Core | Weekly | Batch export |
| Audit Events | Learning → GULA Audit | Real-time | AuditService API |

### API Endpoints

The Learning Platform exposes the following API groups:

| Prefix | Description | Auth Required |
|--------|-------------|---------------|
| `/api/v1/learning/courses` | Course CRUD | Yes |
| `/api/v1/learning/modules` | Module delivery | Yes |
| `/api/v1/learning/enrollments` | Enrollment management | Yes |
| `/api/v1/learning/assessments` | Assessment delivery & scoring | Yes |
| `/api/v1/learning/certificates` | Certificate management | Yes |
| `/api/v1/learning/progress` | Progress tracking | Yes |
| `/api/v1/learning/cme` | CME tracking | Yes |
| `/api/v1/learning/gamification` | Badges, points, leaderboards | Yes |
| `/api/v1/learning/social` | Forums, discussions | Yes |
| `/api/v1/learning/recommendations` | AI recommendations | Yes |
| `/api/v1/learning/admin` | Admin functions | Yes (admin role) |

### Notification Integration

Learning events trigger GULA Notification Service:

| Event | Channel | Template |
|-------|---------|----------|
| Course enrollment confirmation | Email, In-app | enrollment_confirmation |
| Assessment scheduled | Email, SMS | assessment_reminder |
| Certificate issued | Email, In-app | certificate_issued |
| CME target reminder | Email, SMS | cme_reminder |
| Badge earned | In-app, Push | badge_earned |
| Course recommended | In-app, Email | course_recommendation |

### Embedding in GULA UI

Learning content can be embedded in the main GULA dashboard:

- **Contextual Learning**: Help icons link to relevant modules
- **Just-in-Time Training**: Instrument operation guide opens when user first uses device bridge
- **Inline Assessments**: Quick knowledge checks during platform workflows
- **Progress Widget**: Dashboard widget showing learning progress

---

## Appendix: Technology Stack

| Component | Technology |
|-----------|------------|
| Backend Framework | FastAPI (Python 3.11+) |
| Database | PostgreSQL 16 with `citext`, Arabic collation |
| Cache | Redis 7 |
| Search | Elasticsearch (Arabic analyzer) |
| Storage | S3-compatible (MinIO) |
| Streaming | HLS (video), WebRTC (live) |
| AI/ML | ONNX Runtime, scikit-learn |
| Mobile | React Native |
| Frontend | React (Arabic-first) |
| Real-time | WebSockets, SSE |
| Queue | RabbitMQ |
| Monitoring | Prometheus + Grafana |
| Containerization | Docker + Kubernetes |

## Appendix: Database Schema (Core Tables)

```sql
-- Learning Platform Core Schema
CREATE TABLE lp_courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    title_ar TEXT NOT NULL,
    title_en TEXT,
    description_ar TEXT,
    description_en TEXT,
    category VARCHAR(100),
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5),
    estimated_hours DECIMAL(5,1),
    language VARCHAR(10) DEFAULT 'ar',
    is_mandatory BOOLEAN DEFAULT false,
    status VARCHAR(20) DEFAULT 'draft',
    created_by UUID REFERENCES lab_users(id),
    lab_id UUID REFERENCES labs(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE lp_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID REFERENCES lp_courses(id) ON DELETE CASCADE,
    title_ar TEXT NOT NULL,
    title_en TEXT,
    module_type VARCHAR(50),
    content_url TEXT,
    duration_minutes INTEGER,
    sort_order INTEGER,
    is_required BOOLEAN DEFAULT true,
    competencies TEXT[], -- competency dimension IDs
    prerequisites UUID[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE lp_enrollments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES lab_users(id),
    course_id UUID REFERENCES lp_courses(id),
    path_type VARCHAR(50), -- onboarding, competency, certification
    enrolled_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active',
    progress_percent DECIMAL(5,2) DEFAULT 0,
    UNIQUE(user_id, course_id)
);

CREATE TABLE lp_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID REFERENCES lp_modules(id),
    assessment_type VARCHAR(50), -- pre, post, summative, formative
    question_count INTEGER,
    pass_threshold DECIMAL(5,2),
    time_limit_minutes INTEGER,
    is_proctored BOOLEAN DEFAULT false,
    max_attempts INTEGER DEFAULT 3
);

CREATE TABLE lp_assessment_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assessment_id UUID REFERENCES lp_assessments(id),
    user_id UUID REFERENCES lab_users(id),
    score DECIMAL(5,2),
    passed BOOLEAN,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    proctoring_log JSONB,
    attempt_number INTEGER
);

CREATE TABLE lp_certificates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES lab_users(id),
    certification_type VARCHAR(100),
    certificate_number VARCHAR(100) UNIQUE,
    issued_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'active',
    blockchain_hash VARCHAR(128),
    metadata JSONB,
    revoked_at TIMESTAMPTZ,
    revocation_reason TEXT
);

CREATE TABLE lp_cme_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES lab_users(id),
    activity_type VARCHAR(50),
    category VARCHAR(20), -- cat1, cat2
    hours DECIMAL(5,1),
    description TEXT,
    completed_at TIMESTAMPTZ,
    source VARCHAR(50), -- gula, external
    approved_by UUID REFERENCES lab_users(id),
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE lp_gamification (
    user_id UUID PRIMARY KEY REFERENCES lab_users(id),
    total_points INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    badges TEXT[],
    streak_days INTEGER DEFAULT 0,
    last_activity_date DATE,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Appendix: Security Considerations

1. **Data Protection**: All learner data encrypted at rest (AES-256) and in transit (TLS 1.3)
2. **Privacy**: Learning records stored separately from clinical data, no PII in analytics
3. **Access Control**: RBAC extended to learning platform with `learning_admin`, `learning_manager`, `learner` roles
4. **Proctoring Data**: Recording retention: 90 days, auto-deleted after appeals window
5. **GDPR Compliance**: Right to deletion of learning records, data portability
6. **Audit Trail**: All learning actions logged with immutable audit trail
7. **Rate Limiting**: API endpoints protected against abuse
8. **Content Security**: DRM for premium video content, watermarking for certificates

---

## Appendix: Implementation Roadmap

| Phase | Features | Timeline |
|-------|----------|----------|
| **Phase 1** | LMS Core, CMS, basic assessments, role-based paths | Q3 2026 |
| **Phase 2** | Certification Engine, proctoring, digital certificates | Q4 2026 |
| **Phase 3** | AI Recommendation Engine, adaptive learning | Q1 2027 |
| **Phase 4** | Gamification, social learning, mobile apps | Q2 2027 |
| **Phase 5** | Advanced analytics, CME integration, national rollout | Q3 2027 |
