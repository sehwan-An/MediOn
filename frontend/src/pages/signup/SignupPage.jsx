import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { signup as signupApi } from '../../api/auth'
import useAuth from '../../context/useAuth'
import { homePathFor } from '../../routes/homePath'
import { safeReturnPath } from '../../utils/format'
import TopBar from '../../components/layout/TopBar'
import Button from '../../components/ui/Button'
import Chip from '../../components/ui/Chip'
import Icon from '../../components/ui/Icon'
import TextField from '../../components/ui/TextField'
import { LoadingState } from '../../components/ui/States'

const GENDERS = [
  { value: 'M', label: '남성' },
  { value: 'F', label: '여성' },
  { value: null, label: '선택 안 함' },
]

const EMAIL_PATTERN = /^[^@\s]+@[^@\s]+\.[^@\s]+$/
const THIS_YEAR = new Date().getFullYear()

// 백엔드 schemas/auth.py 와 같은 규칙. 화면에서 먼저 알려주고, 최종 검사는 서버가 한다
function validate(form) {
  const errors = {}
  if (!EMAIL_PATTERN.test(form.email.trim())) errors.email = '이메일 형식을 확인해주세요'
  if (form.password.length < 8 || !/[A-Za-z]/.test(form.password) || !/\d/.test(form.password)) {
    errors.password = '비밀번호는 8자 이상, 영문과 숫자를 섞어주세요'
  }
  const nickname = form.nickname.trim()
  if (nickname.length < 2 || nickname.length > 20) errors.nickname = '닉네임은 2~20자로 입력해주세요'
  if (form.birthYear) {
    const year = Number(form.birthYear)
    if (!Number.isInteger(year) || year < 1900 || year > THIS_YEAR) errors.birthYear = '출생연도를 확인해주세요'
  }
  if (!form.agreeTerms || !form.agreePrivacy) errors.agreement = '필수 약관에 동의해주세요'
  return errors
}

// 일반 회원가입 (A-7). 가입하면 바로 로그인되고, 로그인 안내에서 왔으면 보던 화면으로 돌아간다
export default function SignupPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, loading, login } = useAuth()
  const from = safeReturnPath(location.state?.from)

  const [form, setForm] = useState({
    email: '',
    password: '',
    nickname: '',
    birthYear: '',
    gender: null,
    agreeTerms: false,
    agreePrivacy: false,
  })
  const [errors, setErrors] = useState({})
  const [formError, setFormError] = useState('')

  const mutation = useMutation({
    mutationFn: signupApi,
    onSuccess: (data) => {
      login(data.access_token, data.user)
      navigate(from ?? '/', { replace: true })
    },
    onError: (error) => {
      if (error.code === 'EMAIL_TAKEN') setErrors({ email: error.message })
      else setFormError(error.message)
    },
  })

  if (loading) return <LoadingState />
  if (user && !mutation.isSuccess) return <Navigate to={homePathFor(user)} replace />

  const update = (key) => (event) => setForm((f) => ({ ...f, [key]: event.target.value }))
  const allAgreed = form.agreeTerms && form.agreePrivacy

  const handleSubmit = (event) => {
    event.preventDefault()
    const nextErrors = validate(form)
    setErrors(nextErrors)
    setFormError('')
    if (Object.keys(nextErrors).length > 0) return
    mutation.mutate({
      email: form.email,
      password: form.password,
      nickname: form.nickname,
      birth_year: form.birthYear ? Number(form.birthYear) : null,
      gender: form.gender,
      agree_terms: form.agreeTerms,
      agree_privacy: form.agreePrivacy,
    })
  }

  return (
    <div className="flex flex-1 flex-col">
      <TopBar title="회원가입" />
      <form onSubmit={handleSubmit} noValidate className="flex flex-1 flex-col">
        <div className="flex flex-col gap-5 px-5 py-6">
          <TextField
            label="이메일"
            type="email"
            autoComplete="email"
            placeholder="example@email.com"
            value={form.email}
            onChange={update('email')}
            error={errors.email}
          />
          <TextField
            label="비밀번호"
            type="password"
            autoComplete="new-password"
            placeholder="비밀번호를 입력해주세요"
            value={form.password}
            onChange={update('password')}
            hint="8자 이상, 영문과 숫자를 섞어주세요"
            error={errors.password}
          />
          <TextField
            label="닉네임"
            autoComplete="nickname"
            placeholder="닉네임을 입력해주세요"
            maxLength={20}
            value={form.nickname}
            onChange={update('nickname')}
            hint="후기에는 일부만 가려서 보여요 (예: 홍*동)"
            error={errors.nickname}
          />
          <TextField
            label="출생연도"
            optional
            inputMode="numeric"
            placeholder="예: 1995"
            maxLength={4}
            value={form.birthYear}
            onChange={(e) => setForm((f) => ({ ...f, birthYear: e.target.value.replace(/\D/g, '') }))}
            hint="의사에게는 나이대(30대 등)로만 보여요. 본인 진료를 예약할 때 필요해요"
            error={errors.birthYear}
          />

          <fieldset className="flex flex-col gap-2">
            <legend className="mb-2 flex items-center gap-1 text-sm font-bold">
              성별 <span className="font-normal text-ink-muted">선택</span>
            </legend>
            <div className="flex gap-2">
              {GENDERS.map((g) => (
                <Chip
                  key={g.label}
                  selected={form.gender === g.value}
                  onClick={() => setForm((f) => ({ ...f, gender: g.value }))}
                  className="flex-1"
                >
                  {g.label}
                </Chip>
              ))}
            </div>
          </fieldset>

          <fieldset className="flex flex-col rounded-2xl bg-white px-4 py-2">
            <legend className="sr-only">약관 동의</legend>
            <label className="flex min-h-11 items-center gap-3 border-b border-line text-[15px] font-bold">
              <input
                type="checkbox"
                className="size-5 accent-primary"
                checked={allAgreed}
                onChange={(e) => setForm((f) => ({ ...f, agreeTerms: e.target.checked, agreePrivacy: e.target.checked }))}
              />
              전체 동의
            </label>
            <label className="flex min-h-11 items-center gap-3 text-sm">
              <input
                type="checkbox"
                className="size-5 accent-primary"
                checked={form.agreeTerms}
                onChange={(e) => setForm((f) => ({ ...f, agreeTerms: e.target.checked }))}
              />
              [필수] 서비스 이용약관 동의
            </label>
            <label className="flex min-h-11 items-start gap-3 py-2 text-sm">
              <input
                type="checkbox"
                className="mt-0.5 size-5 accent-primary"
                checked={form.agreePrivacy}
                onChange={(e) => setForm((f) => ({ ...f, agreePrivacy: e.target.checked }))}
              />
              <span className="flex flex-col">
                [필수] 개인정보 수집·이용 동의
                <span className="text-xs text-ink-muted">증상 메모, 처방전 등 건강 정보가 포함돼요</span>
              </span>
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
          <Button type="submit" className="w-full" disabled={mutation.isPending}>
            {mutation.isPending ? '가입하는 중…' : '가입하기'}
          </Button>
          <p className="flex items-center justify-center gap-1.5 text-[13px] text-ink-muted">
            의사이신가요?
            <Link to="/signup/doctor" className="inline-flex min-h-11 items-center font-bold text-doctor">
              의사 회원가입
            </Link>
          </p>
        </div>
      </form>
    </div>
  )
}
