import { Route, Routes } from 'react-router-dom'
import AppLayout from './components/layout/AppLayout'
import TabLayout from './components/layout/TabLayout'
import RoleRoute from './routes/RoleRoute'
import StartGate from './routes/StartGate'

import WelcomePage from './pages/welcome/WelcomePage'
import LoginPage from './pages/login/LoginPage'
import SignupPage from './pages/signup/SignupPage'
import DoctorSignupPage from './pages/signup/DoctorSignupPage'
import HomePage from './pages/home/HomePage'
import DoctorListPage from './pages/doctors/DoctorListPage'
import DoctorDetailPage from './pages/doctors/DoctorDetailPage'
import BookPage from './pages/doctors/BookPage'
import AppointmentsPage from './pages/appointments/AppointmentsPage'
import AppointmentDetailPage from './pages/appointments/AppointmentDetailPage'
import ReviewPage from './pages/appointments/ReviewPage'
import PaymentPage from './pages/payments/PaymentPage'
import PaymentResultPage from './pages/payments/PaymentResultPage'
import PrescriptionPage from './pages/prescriptions/PrescriptionPage'
import PharmacyPage from './pages/prescriptions/PharmacyPage'
import MyPage from './pages/my/MyPage'
import FamilyPage from './pages/my/FamilyPage'
import PaymentsPage from './pages/my/PaymentsPage'
import NotificationsPage from './pages/notifications/NotificationsPage'
import QnaFeedPage from './pages/qna/QnaFeedPage'
import QuestionDetailPage from './pages/question/QuestionDetailPage'
import QuestionWritePage from './pages/question/QuestionWritePage'
import MyQuestionsPage from './pages/my/MyQuestionsPage'
import DoctorInboxPage from './pages/doctor/DoctorInboxPage'
import DoctorAnswerPage from './pages/doctor/DoctorAnswerPage'
import DoctorAnswersPage from './pages/doctor/DoctorAnswersPage'
import DoctorSchedulePage from './pages/doctor/DoctorSchedulePage'
import DoctorTimetablePage from './pages/doctor/DoctorTimetablePage'
import DoctorAppointmentPage from './pages/doctor/DoctorAppointmentPage'
import DoctorCompletePage from './pages/doctor/DoctorCompletePage'
import DoctorMyPage from './pages/doctor/DoctorMyPage'
import DoctorPendingPage from './pages/doctor/DoctorPendingPage'
import AdminDoctorsPage from './pages/admin/AdminDoctorsPage'
import NotFoundPage from './pages/NotFoundPage'

// 화면 목록: docs/requirements.md 4. 화면 목록 (1차)
// 2차(질문·답변, 근처 병원) 화면 파일은 pages/question, pages/hospitals 등에 남겨두고 2차에서 라우트를 연결한다
export default function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        {/* 시작 · 가입 */}
        <Route path="/welcome" element={<WelcomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/signup/doctor" element={<DoctorSignupPage />} />

        {/* 환자 · 게스트 (처음 방문한 게스트는 시작 화면으로, 의사·관리자는 각자의 첫 화면으로) */}
        <Route element={<StartGate />}>
          <Route element={<TabLayout role="patient" />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/doctors" element={<DoctorListPage />} />
            <Route path="/qna" element={<QnaFeedPage />} />
            <Route path="/my" element={<MyPage />} />
            <Route element={<RoleRoute roles={['patient']} />}>
              <Route path="/appointments" element={<AppointmentsPage />} />
            </Route>
          </Route>
          <Route path="/doctors/:id" element={<DoctorDetailPage />} />
          <Route path="/questions/:id" element={<QuestionDetailPage />} />
          <Route element={<RoleRoute roles={['patient']} />}>
            <Route path="/doctors/:id/book" element={<BookPage />} />
            <Route path="/appointments/:id" element={<AppointmentDetailPage />} />
            <Route path="/appointments/:id/pay" element={<PaymentPage />} />
            <Route path="/appointments/:id/review" element={<ReviewPage />} />
            <Route path="/appointments/:id/prescription" element={<PrescriptionPage />} />
            <Route path="/appointments/:id/pharmacy" element={<PharmacyPage />} />
            <Route path="/payments/success" element={<PaymentResultPage key="success" result="success" />} />
            <Route path="/payments/fail" element={<PaymentResultPage key="fail" result="fail" />} />
            <Route path="/my/family" element={<FamilyPage />} />
            <Route path="/my/payments" element={<PaymentsPage />} />
            <Route path="/my/questions" element={<MyQuestionsPage />} />
            <Route path="/questions/new" element={<QuestionWritePage />} />
          </Route>
        </Route>

        <Route element={<RoleRoute roles={['patient', 'doctor', 'admin']} />}>
          <Route path="/notifications" element={<NotificationsPage />} />
        </Route>

        {/* 의사: 인증 승인 전에는 심사 중 화면과 마이만 */}
        <Route element={<RoleRoute roles={['doctor']} />}>
          <Route path="/doctor/pending" element={<DoctorPendingPage />} />
          <Route element={<TabLayout role="doctor" />}>
            <Route path="/doctor/my" element={<DoctorMyPage />} />
          </Route>
        </Route>
        <Route element={<RoleRoute roles={['doctor']} requireVerified />}>
          <Route element={<TabLayout role="doctor" />}>
            <Route path="/doctor" element={<DoctorSchedulePage />} />
            <Route path="/doctor/qna" element={<DoctorInboxPage />} />
          </Route>
          <Route path="/doctor/questions/:id/answer" element={<DoctorAnswerPage />} />
          <Route path="/doctor/answers" element={<DoctorAnswersPage />} />
          <Route path="/doctor/schedule" element={<DoctorTimetablePage />} />
          <Route path="/doctor/appointments/:id" element={<DoctorAppointmentPage />} />
          <Route path="/doctor/appointments/:id/complete" element={<DoctorCompletePage />} />
        </Route>

        {/* 관리자 */}
        <Route element={<RoleRoute roles={['admin']} />}>
          <Route path="/admin/doctors" element={<AdminDoctorsPage />} />
        </Route>

        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
