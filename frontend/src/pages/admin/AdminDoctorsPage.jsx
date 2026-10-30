import { useId, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getDoctorApplications, getDoctorDocument, reviewDoctor } from '../../api/admin'
import { departmentName } from '../../constants/departments'
import useAuth from '../../context/useAuth'
import { formatDateTime } from '../../utils/format'
import BottomSheet from '../../components/ui/BottomSheet'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'
import Icon from '../../components/ui/Icon'
import Pill from '../../components/ui/Pill'
import TextField from '../../components/ui/TextField'
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States'

const TABS = [
  { key: 'pending', label: '심사 중' },
  { key: 'approved', label: '승인' },
  { key: 'rejected', label: '반려' },
]
const DOC_LABEL = { license: '의사 면허증', specialist: '전문의 자격증', employment: '재직 증명서' }

// 관리자 의사 인증 심사 (A-11). 서류를 보고 승인/반려(사유 입력), 결과는 의사에게 알림으로 간다
export default function AdminDoctorsPage() {
  const navigate = useNavigate()
  const { logout } = useAuth()
  const [tab, setTab] = useState('pending')
  const [rejecting, setRejecting] = useState(null) // 반려할 신청
  const list = useQuery({ queryKey: ['admin-doctors', tab], queryFn: () => getDoctorApplications({ status: tab }) })

  const handleLogout = () => {
    logout()
    navigate('/welcome', { replace: true })
  }

  return (
    <div className="flex flex-1 flex-col">
      <header className="sticky top-7 z-20 flex h-14 items-center justify-between bg-white pr-2 pl-5">
        <h1 className="text-xl font-bold">의사 인증 심사</h1>
        <button type="button" onClick={handleLogout} aria-label="로그아웃" className="flex size-11 items-center justify-center text-ink">
          <Icon name="logout" />
        </button>
      </header>
      <div role="tablist" className="grid grid-cols-3 bg-white px-5">
        {TABS.map((t) => (
          <button key={t.key} type="button" role="tab" aria-selected={tab === t.key} onClick={() => setTab(t.key)}
            className={`min-h-11 border-b-2 text-[15px] ${tab === t.key ? 'border-doctor font-bold text-doctor' : 'border-transparent font-medium text-ink-muted'}`}>
            {t.label}
          </button>
        ))}
      </div>

      <div className="flex flex-1 flex-col gap-3 p-5">
        {list.isPending && <LoadingState />}
        {list.isError && <ErrorState message={list.error.message} onRetry={list.refetch} />}
        {list.isSuccess && list.data.length === 0 && <EmptyState title="신청이 없어요" />}
        {list.data?.map((a) => <Application key={a.user_id} application={a} onReject={() => setRejecting(a)} />)}
      </div>

      <RejectSheet application={rejecting} onClose={() => setRejecting(null)} />
    </div>
  )
}

function Application({ application: a, onReject }) {
  const queryClient = useQueryClient()
  const [docError, setDocError] = useState('')
  const approve = useMutation({
    mutationFn: () => reviewDoctor(a.user_id, { action: 'approve' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-doctors'] }),
  })

  // 서류는 공개 주소가 없어서 Blob 으로 받아 새 탭에서 연다. 창은 클릭 순간에 먼저 열어야 팝업 차단에 안 걸린다
  const openDocument = async (doc) => {
    setDocError('')
    const win = window.open('', '_blank')
    try {
      const blob = await getDoctorDocument(a.user_id, doc.id)
      const url = URL.createObjectURL(blob)
      if (win) win.location.href = url
      else window.location.assign(url)
      setTimeout(() => URL.revokeObjectURL(url), 60 * 1000)
    } catch {
      win?.close()
      setDocError('서류를 열지 못했어요. 잠시 후 다시 시도해주세요')
    }
  }

  return (
    <Card>
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-0.5">
          <h2 className="text-[17px] font-bold">{a.name}</h2>
          <p className="text-[13px] text-ink-muted">{a.email}</p>
        </div>
        <Pill tone={a.verification_status === 'pending' ? 'wait' : a.verification_status === 'approved' ? 'done' : 'muted'}>
          {TABS.find((t) => t.key === a.verification_status)?.label}
        </Pill>
      </div>
      <dl className="grid grid-cols-[5.5rem_1fr] gap-y-1.5 text-sm">
        <dt className="text-ink-muted">전문과</dt><dd>{departmentName(a.department_code)}</dd>
        <dt className="text-ink-muted">소속 병원</dt><dd>{a.hospital_name}</dd>
        <dt className="text-ink-muted">면허번호</dt><dd>{a.license_number}</dd>
        <dt className="text-ink-muted">신청</dt><dd>{formatDateTime(a.submitted_at) || '-'}</dd>
        {a.reviewed_at && <><dt className="text-ink-muted">심사</dt><dd>{formatDateTime(a.reviewed_at)}</dd></>}
        {a.rejected_reason && <><dt className="text-ink-muted">반려 사유</dt><dd>{a.rejected_reason}</dd></>}
      </dl>
      <div className="flex flex-col gap-2">
        {a.documents.length === 0 && <p className="text-[13px] text-ink-muted">제출한 서류가 없어요</p>}
        {a.documents.map((doc) => (
          <button key={doc.id} type="button" onClick={() => openDocument(doc)}
            className="flex min-h-11 items-center gap-2 rounded-xl bg-surface px-3.5 text-left text-sm font-medium">
            <Icon name="file" size={18} className="text-doctor" />
            <span className="flex-1">{DOC_LABEL[doc.type] ?? doc.type}</span>
            <span className="text-[13px] font-bold text-doctor">보기</span>
          </button>
        ))}
        {docError && <p role="alert" className="text-[13px] text-wait">{docError}</p>}
      </div>
      {a.verification_status === 'pending' && (
        <div className="grid grid-cols-2 gap-2">
          <Button variant="secondary" onClick={onReject}>반려</Button>
          <Button variant="doctor" disabled={approve.isPending} onClick={() => approve.mutate()}>
            {approve.isPending ? '처리 중…' : '승인'}
          </Button>
        </div>
      )}
      {approve.isError && <p role="alert" className="text-[13px] text-wait">{approve.error.message}</p>}
    </Card>
  )
}

function RejectSheet({ application, onClose }) {
  const titleId = useId()
  const queryClient = useQueryClient()
  const [reason, setReason] = useState('')
  const [error, setError] = useState('')
  const reject = useMutation({
    mutationFn: () => reviewDoctor(application.user_id, { action: 'reject', reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin-doctors'] })
      close()
    },
    onError: (e) => setError(e.message),
  })

  function close() {
    setReason('')
    setError('')
    onClose()
  }

  const submit = () => {
    if (!reason.trim()) return setError('반려 사유를 입력해주세요')
    reject.mutate()
  }

  return (
    <BottomSheet open={Boolean(application)} onClose={close} titleId={titleId}>
      <h2 id={titleId} className="text-lg font-bold">{application?.name} 의사 인증 반려</h2>
      <p className="text-sm text-ink-muted">반려 사유는 의사에게 알림으로 전달돼요</p>
      <TextField label="반려 사유" placeholder="예: 면허증 사진이 흐려서 확인할 수 없어요" maxLength={200}
        value={reason} onChange={(e) => setReason(e.target.value)} error={error} />
      <div className="mt-2 grid grid-cols-2 gap-2">
        <Button variant="secondary" onClick={close}>취소</Button>
        <Button variant="doctor" disabled={reject.isPending} onClick={submit}>
          {reject.isPending ? '처리 중…' : '반려하기'}
        </Button>
      </div>
    </BottomSheet>
  )
}
