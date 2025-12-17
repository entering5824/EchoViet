# Role-Based System Structure

## Tổng quan

Hệ thống đã được tổ chức lại theo 3 vai trò chính:
- **User**: Người dùng thường
- **AI Specialist**: Chuyên gia AI/ML
- **Admin/Manager**: Quản trị viên

## Cấu trúc đã triển khai

### 1. Authentication & Authorization (`core/auth/`)

#### `roles.py`
- Định nghĩa các roles: `USER`, `AI_SPECIALIST`, `ADMIN`, `MANAGER`
- Hệ thống permissions cho từng role
- Decorators: `@require_role()`, `@require_permission()`

#### `session.py`
- Quản lý session state
- User login/logout (demo mode)
- History management
- Session initialization

### 2. Pages đã tạo

#### ✅ `0_🏠_Home_Dashboard.py`
- Dashboard tổng quan cho tất cả users
- Quick stats và actions
- Recent transcripts
- Role-specific sections

#### ✅ `7_📚_History_Projects.py`
- Quản lý lịch sử transcripts
- Filter và search
- Export và delete
- Save current session

### 3. Components đã cập nhật

#### ✅ `app/components/sidebar.py`
- Role-based navigation
- Hiển thị user info và role
- Menu khác nhau theo role
- Dev mode role switcher

## Các trang cần tạo tiếp

### User Pages (MVP Priority)

#### 🔲 `8_✏️_Transcript_Editor.py` (High Priority)
- Inline editing với timestamps
- Speaker label editing
- Punctuation suggestions
- Export options (TXT, DOCX, PDF, SRT, JSON)

#### 🔲 `9_📊_Visualizer.py` (Medium Priority)
- Waveform và spectrogram
- Zoom và seek controls
- Timestamp markers
- Speaker turn visualization

#### 🔲 `10_❓_Help_Tutorials.py` (Low Priority)
- Hướng dẫn sử dụng
- Tips và best practices
- FAQ
- Video tutorials

### AI Specialist Pages

#### 🔲 `AI_Models.py`
- Model management dashboard
- Deploy/rollback models
- Set default models
- Upload custom models

#### 🔲 `AI_Model_Settings.py`
- Hyperparameter configuration
- Chunking strategy
- VAD thresholds
- Save presets

#### 🔲 `AI_Evaluation.py`
- WER/CER/SER metrics
- Confidence histograms
- Confusion matrices
- Test set evaluation

#### 🔲 `AI_Logs.py`
- Inference logs
- Performance metrics
- Error tracking
- Debugging tools

#### 🔲 `AI_Datasets.py`
- Dataset management
- Import/Export datasets
- Annotation tools
- Versioning

### Admin Pages

#### 🔲 `Admin_Dashboard.py`
- System KPIs
- Usage statistics
- Cost tracking
- Active users

#### 🔲 `Admin_Users.py`
- User management
- Role assignment
- Permissions
- SSO/OAuth settings

#### 🔲 `Admin_Billing.py`
- Cost breakdown
- Quotas management
- Alerts configuration
- Billing history

#### 🔲 `Admin_Logs.py`
- Audit logs
- Access logs
- Export logs
- Compliance tracking

#### 🔲 `Admin_Settings.py`
- System settings
- Default configurations
- Security settings
- Backup schedule

#### 🔲 `Admin_Health.py`
- System health monitoring
- Service status
- Error alerts
- Storage usage

## Permissions Matrix

| Permission | User | AI Specialist | Admin |
|------------|------|---------------|-------|
| upload_audio | ✅ | ✅ | ✅ |
| transcribe | ✅ | ✅ | ✅ |
| edit_transcript | ✅ | ✅ | ✅ |
| export_transcript | ✅ | ✅ | ✅ |
| view_history | ✅ | ✅ | ✅ |
| share_transcript | ✅ | ✅ | ✅ |
| manage_models | ❌ | ✅ | ✅ |
| configure_models | ❌ | ✅ | ✅ |
| evaluate_models | ❌ | ✅ | ✅ |
| manage_datasets | ❌ | ✅ | ✅ |
| view_logs | ❌ | ✅ | ✅ |
| manage_users | ❌ | ❌ | ✅ |
| view_analytics | ❌ | ❌ | ✅ |
| manage_settings | ❌ | ❌ | ✅ |
| view_audit_logs | ❌ | ❌ | ✅ |
| manage_billing | ❌ | ❌ | ✅ |

## Navigation Structure

### User Navigation
```
🏠 Home / Dashboard
📤 Upload & Record
🎧 Preprocessing
📝 Transcription
👥 Speaker Diarization
📊 Export & Statistics
📚 History / Projects
❓ Help & Tutorials
```

### AI Specialist Navigation
```
🏠 Home / Dashboard
📤 Upload & Record
📝 Transcription
📊 Export & Statistics

🤖 Model Management
⚙️ Model Settings
📈 Evaluation & Metrics
🔬 ASR Benchmark
📊 Inference Logs
📚 Datasets
```

### Admin Navigation
```
🏠 Home / Dashboard
📤 Upload & Record
📝 Transcription

🤖 Model Management
📈 Evaluation & Metrics

📊 Admin Dashboard
👥 User Management
💰 Billing & Costs
📋 Audit Logs
⚙️ System Settings
🏥 System Health
```

## Implementation Status

### ✅ Completed
- [x] Role-based authentication system
- [x] Session management
- [x] User Dashboard
- [x] History/Projects page
- [x] Role-based sidebar navigation
- [x] Permission system

### 🔄 In Progress
- [ ] Transcript Editor (advanced)
- [ ] Upload page improvements (presets)

### 📋 Planned (MVP)
- [ ] Transcript Editor with inline editing
- [ ] Visualizer improvements
- [ ] Help & Tutorials page

### 📋 Planned (Advanced)
- [ ] AI Specialist pages
- [ ] Admin pages
- [ ] API & Integrations page
- [ ] Settings page
- [ ] Notifications center

## Next Steps

1. **Immediate (MVP)**:
   - Improve Upload page with presets
   - Create advanced Transcript Editor
   - Add export formats (SRT, JSON)

2. **Short-term**:
   - Create AI Specialist pages (Model Management, Evaluation)
   - Add dataset management
   - Implement logging system

3. **Long-term**:
   - Create Admin pages
   - Add billing system
   - Implement audit logging
   - Add collaboration features

## Notes

- Role switching is available in dev mode only
- In production, implement proper authentication (OAuth, SSO)
- Session state is used for demo - consider database for production
- History is stored in session state (max 100 entries) - migrate to database








