import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { signupDoctor } from '../../api/auth'
import { DEPARTMENTS } from '../../constants/departments'
import useAuth from '../../context/useAuth'
import { homePathFor } from '../../routes/homePath'
import TopBar from '../../components/layout/TopBar'
import Button from '../../components/ui/Button'
import Chip from '../../components/ui/Chip'
import Icon from '../../components/ui/Icon'
import TextField from '../../components/ui/TextField'
import { LoadingState } from '../../components/ui/States'

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/
const MAX_BYTES = 5 * 1024 * 1024
const ACCEPT = 'image/jpeg,image/png,image/webp,application/pdf'

// 인증 서류 (A-9). 면허증만 필수
const DOCUMENTS = [
  { key: 'license', label: '의사 면허증', required: true },
  { key: 'specialist', label: '전문의 자격증', required: false },
  { key: 'employment', label: '재직 증명서', required: false },
]

// 백엔드 schemas/auth.py DoctorSignupRequest 와 같은 규칙. 최종 검사는 서버가 한다
function validate(form, files) {
  const errors = {}
  if (!EMAIL_PATTERN.test(form.email.trim())) errors.email = '이메일 형식을 확인해주세요'
  if (form.password.length < 8 || !/[A-Za-z]/.test(form.password) || !/\d/.test(form.password)) {
    errors.password = '비밀번호는 8자 이상, 영문과 숫자를 섞어주세요'
  }
  const name = form.name.trim()
  if (name.length < 2 || name.length > 20) errors.name = '이름은 2~20자로 입력해주세요'
  if (!/^\d{1,10}$/.test(form.licenseNumber.trim())) errors.licenseNumber = '면허번호는 숫자로 입력해주세요'
  if (!form.department) errors.department = '전문과를 선택해주세요'
  const hospital = form.hospital.trim()
  if (hospital.length < 2 || hospital.length > 50) errors.hospital = '소속 병원은 2~50자로 입력해주세요'
  if (!files.license) errors.license = '의사 면허증을 올려주세요'
  for (const doc of DOCUMENTS) {
    if (files[doc.key]?.size > MAX_BYTES) errors[doc.key] = '서류 파일은 5MB 이하로 올려주세요'
  }
  if (!form.agreeTerms || !form.agreePrivacy) errors.agreement = '필수 약관에 동의해주세요'
  return errors
}

// 의사 회원가입 신청 (A-9). 가입하면 바로 로그인되고 심사 중 화면(A-10)으로 간다
export default function DoctorSignupPage() {
  const navigate = useNavigate()
  const { user, loading, login } = useAuth()
  const [form, setForm] = useState({
    email: '',
    password: '',
    name: '',
    licenseNumber: '',
    department: null,
    hospital: '',
    agreeTerms: false,
    agreePrivacy: false,
  })
  const [files, setFiles] = useState({})
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')

  const mutation = useMutation({
    mutationFn: signupDoctor,
    onSuccess: (data) => {
      login(data.access_token, data.user)
      navigate('/doctor/pending', { replace: true })
    },
    onError: (error) => {
      if (error.code === 'EMAIL_TAKEN') setErrors({ email: error.message })
      else setFormError(error.message)
    },
  })

  if (loading) return <LoadingState />
  if (user && !mutation.isSuccess) return <Navigate to={homePathFor(user)} replace />

  const update = (key) => (event) => setForm((f) => ({ ...f, [key]: event.target.value }))

  const handleSubmit = (event) => {
    event.preventDefault()
    const nextErrors = validate(form, files)
    setErrors(nextErrors)
    setFormError('')
    if (Object.keys(nextErrors).length > 0) return
    const body = new FormData()
    body.append('email', form.email)
    body.append('password', form.password)
    body.append('name', form.name)
    body.append('license_number', form.licenseNumber.trim())
    body.append('department_code', form.department)
    body.append('hospital_name', form.hospital)
    body.append('agree_terms', String(form.agreeTerms))
    body.append('agree_privacy', String(form.agreePrivacy))
    for (const doc of DOCUMENTS) {
      if (files[doc.key]) body.append(doc.key, files[doc.key])
    }
    mutation.mutate(body)
  }

  return (
    <div className="flex flex-1 flex-col">
      <TopBar title="의사 회원가입" />
      <form onSubmit={handleSubmit} noValidate className="flex flex-1 flex-col">
        <div className="flex flex-col gap-5 px-5 py-6">
          <p className="flex gap-2 rounded-xl bg-doctor-soft px-3.5 py-3 text-[13px] font-medium text-doctor">
            <Icon name="info" size={18} className="shrink-0" />
            관리자가 면허 서류를 확인한 뒤 승인하면 진료를 시작할 수 있어요. 데모라서 실제 서류 대신 예시 이미지를 올려주세요.
          </p>

          <TextField label="이메일" type="email" autoComplete="email" placeholder="example@email.com"
            value={form.email} onChange={update('email')} error={errors.email} />
          <TextField label="비밀번호" type="password" autoComplete="new-password" placeholder="비밀번호를 입력해주세요"
            value={form.password} onChange={update('password')} hint="8자 이상, 영문과 숫자를 섞어주세요" error={errors.password} />
          <TextField label="이름" autoComplete="name" placeholder="실명을 입력해주세요" maxLength={20}
            value={form.name} onChange={update('name')} hint="환자에게 '○○○ 의사'로 보여요" error={errors.name} />
          <TextField label="면허번호" inputMode="numeric" placeholder="숫자만 입력" maxLength={10}
            value={form.licenseNumber} onChange={(e) => setForm((f) => ({ ...f, licenseNumber: e.target.value.replace(/\D/g, '') }))}
            error={errors.licenseNumber} />

          <fieldset className="flex flex-col gap-2">
            <legend className="mb-2 text-sm font-bold">전문과</legend>
            <div className="flex flex-wrap gap-2">
              {DEPARTMENTS.map((d) => (
                <Chip key={d.code} tone="doctor" selected={form.department === d.code}
                  onClick={() => setForm((f) => ({ ...f, department: d.code }))}>
                  {d.name}
                </Chip>
              ))}
            </div>
            {errors.department && <p className="text-[13px] text-wait">{errors.department}</p>}
          </fieldset>

          <TextField label="소속 병원" placeholder="예: 가온내과의원" maxLength={50}
            value={form.hospital} onChange={update('hospital')} error={errors.hospital} />

          <fieldset className="flex flex-col gap-2">
            <legend className="mb-2 text-sm font-bold">인증 서류</legend>
            {DOCUMENTS.map((doc) => (
              <FileRow key={doc.key} doc={doc} file={files[doc.key]} error={errors[doc.key]}
                onChange={(file) => setFiles((f) => ({ ...f, [doc.key]: file }))} />
            ))}
            <p className="text-xs text-ink-muted">JPG, PNG, WEBP, PDF · 5MB 이하. 서류는 관리자만 볼 수 있어요</p>
          </fieldset>

          <fieldset className="flex flex-col rounded-2xl bg-white px-4 py-2">
            <legend className="sr-only">약관 동의</legend>
            <label className="flex min-h-11 items-center gap-3 border-b border-line text-[15px] font-bold">
              <input type="checkbox" className="size-5 accent-doctor" checked={form.agreeTerms && form.agreePrivacy}
                onChange={(e) => setForm((f) => ({ ...f, agreeTerms: e.target.checked, agreePrivacy: e.target.checked }))} />
              전체 동의
            </label>
            <label className="flex min-h-11 items-center gap-3 text-sm">
              <input type="checkbox" className="size-5 accent-doctor" checked={form.agreeTerms}
                onChange={(e) => setForm((f) => ({ ...f, agreeTerms: e.target.checked }))} />
              [필수] 서비스 이용약관 동의
            </label>
            <label className="flex min-h-11 items-center gap-3 text-sm">
              <input type="checkbox" className="size-5 accent-doctor" checked={form.agreePrivacy}
                onChange={(e) => setForm((f) => ({ ...f, agreePrivacy: e.target.checked }))} />
              [필수] 개인정보 수집·이용 동의 (면허 서류 포함)
            </label>
          </fieldset>
          {errors.agreement && <p className="-mt-3 text-[13px] text-wait">{errors.agreement}</p>}
        </div>

        <div className="sticky bottom-0 mt-auto flex flex-col gap-2 border-t border-line bg-white px-5 pt-3 pb-6">
          {formError && (
            <p role="alert" className="flex items-center gap-1.5 text-[13px] text-wait">
              <Icon name="alert" size={16} />
              {formError}
            </p>
          )}
          <Button type="submit" variant="doctor" className="w-full" disabled={mutation.isPending}>
            {mutation.isPending ? '신청하는 중…' : '인증 신청하기'}
          </Button>
        </div>
      </form>
    </div>
  )
}

function FileRow({ doc, file, error, onChange }) {
  return (
    <div className="flex flex-col gap-1">
      <label className={`flex min-h-14 cursor-pointer items-center gap-3 rounded-[14px] border bg-white px-4 py-2.5 ${error ? 'border-wait' : 'border-line'}`}>
        <Icon name="file" size={20} className={file ? 'text-doctor' : 'text-ink-muted'} />
        <span className="flex min-w-0 flex-1 flex-col">
          <span className="text-[15px] font-bold">
            {doc.label} {!doc.required && <span className="font-normal text-ink-muted">선택</span>}
          </span>
          <span className="truncate text-xs text-ink-muted">{file ? file.name : '파일을 선택해주세요'}</span>
        </span>
        <span className="text-[13px] font-bold text-doctor">{file ? '변경' : '선택'}</span>
        <input type="file" accept={ACCEPT} className="sr-only" onChange={(e) => onChange(e.target.files?.[0] ?? null)} />
      </label>
      {error && <p className="text-[13px] text-wait">{error}</p>}
    </div>
  )
}
