import { useCallback, useEffect, useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getPharmacies, sendToPharmacy } from '../../api/payments'
import { DELIVERY_REASONS } from '../../constants/appointments'
import TopBar from '../../components/layout/TopBar'
import KakaoMap from '../../components/map/KakaoMap'
import Button from '../../components/ui/Button'
import Icon from '../../components/ui/Icon'
import TextField from '../../components/ui/TextField'
import { EmptyState, ErrorState, LoadingState } from '../../components/ui/States'

// 위치 권한이 없을 때 기준 위치 (M-6): 광주광역시청
const DEFAULT_CENTER = { lat: 35.160032, lng: 126.851338 }

// 위치 가져오기: 처음엔 null(확인 중), 허용하면 내 위치, 거부·실패하면 기본 위치 + denied
function useLocation() {
  // 위치 기능이 없는 브라우저는 처음부터 기본 위치
  const [state, setState] = useState(() => (navigator.geolocation ? null : { ...DEFAULT_CENTER, denied: true }))
  useEffect(() => {
    if (!navigator.geolocation) return undefined
    navigator.geolocation.getCurrentPosition(
      (pos) => setState({ lat: pos.coords.latitude, lng: pos.coords.longitude, denied: false }),
      () => setState({ ...DEFAULT_CENTER, denied: true }),
      { timeout: 5000, maximumAge: 10 * 60 * 1000 },
    )
    return undefined
  }, [])
  return state
}

// 약국 선택·처방전 전송 (M-1~M-3, M-6). 기본은 방문 수령, 배송은 제도상 대상자만 (M-2). 실제 약국에는 전송되지 않는다
export default function PharmacyPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const location = useLocation()
  const [selectedId, setSelectedId] = useState(null)
  const [method, setMethod] = useState('pickup')
  const [reason, setReason] = useState(null)
  const [address, setAddress] = useState('')
  const [formError, setFormError] = useState('')

  const pharmacies = useQuery({
    queryKey: ['pharmacies', location?.lat.toFixed(3), location?.lng.toFixed(3)],
    queryFn: () => getPharmacies(location.lat, location.lng),
    enabled: Boolean(location),
  })
  const list = useMemo(() => pharmacies.data ?? [], [pharmacies.data])
  const markers = useMemo(() => list.map((p) => ({ id: p.ext_id, lat: p.lat, lng: p.lng, title: p.name })), [list])
  const select = useCallback((ext) => setSelectedId(ext), [])
  const selected = list.find((p) => p.ext_id === selectedId)

  const send = useMutation({
    mutationFn: (payload) => sendToPharmacy(id, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointment', id] })
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
      navigate(`/appointments/${id}`, { replace: true })
    },
    onError: (error) => setFormError(error.message),
  })

  const handleSend = () => {
    if (!selected) return setFormError('약국을 골라주세요')
    if (method === 'delivery' && (!reason || !address.trim())) return setFormError('배송 대상 여부와 배송지를 입력해주세요')
    setFormError('')
    const { ext_id, name, address: pharmacyAddress, tel, lat, lng } = selected
    send.mutate({
      pharmacy: { ext_id, name, address: pharmacyAddress, tel, lat, lng },
      receive_method: method,
      delivery_reason: method === 'delivery' ? reason : null,
      delivery_address: method === 'delivery' ? address : null,
    })
  }

  return (
    <div className="flex flex-1 flex-col">
      <TopBar title="약국 선택" />
      {location ? <KakaoMap center={location} markers={markers} selectedId={selectedId} onSelect={select} /> : <div className="h-56 bg-surface" />}

      <div className="flex flex-col gap-4 p-5">
        {location?.denied && (
          <Notice tone="wait">위치 권한이 없어서 광주광역시청 기준으로 보여드려요. 브라우저 설정에서 위치 권한을 허용하면 내 주변 약국을 볼 수 있어요.</Notice>
        )}

        <div role="radiogroup" aria-label="수령 방법" className="grid grid-cols-2 gap-1 rounded-xl bg-surface p-1">
          {[
            ['pickup', '방문 수령', 'store'],
            ['delivery', '배송 (대상자만)', 'truck'],
          ].map(([value, label, icon]) => (
            <button
              key={value}
              type="button"
              role="radio"
              aria-checked={method === value}
              onClick={() => setMethod(value)}
              className={`flex h-10 items-center justify-center gap-1.5 rounded-[10px] text-sm ${method === value ? 'bg-white font-bold text-primary' : 'font-medium text-ink-muted'}`}
            >
              <Icon name={icon} size={18} />
              {label}
            </button>
          ))}
        </div>

        {method === 'delivery' && (
          <>
            <Notice tone="wait">약 배송은 제도상 섬·벽지 거주자, 장기요양 수급자, 장애인, 희귀질환자만 받을 수 있어요. 해당하지 않으면 방문 수령을 선택해주세요.</Notice>
            <fieldset className="flex flex-col gap-2">
              <legend className="mb-2 text-base font-bold">배송 대상 확인</legend>
              {DELIVERY_REASONS.map((r) => (
                <label key={r.value} className={`flex min-h-14 items-center gap-3 rounded-[14px] border px-4 py-2.5 ${reason === r.value ? 'border-2 border-primary bg-primary-soft' : 'border-line bg-white'}`}>
                  <input type="radio" name="delivery-reason" className="size-5 accent-primary" checked={reason === r.value} onChange={() => setReason(r.value)} />
                  <span className="flex flex-col">
                    <span className="text-[15px] font-bold">{r.label}</span>
                    <span className="text-xs text-ink-muted">{r.description}</span>
                  </span>
                </label>
              ))}
            </fieldset>
            <TextField label="배송지" placeholder="받으실 주소를 입력해주세요" maxLength={200} value={address} onChange={(e) => setAddress(e.target.value)} />
          </>
        )}

        <div className="flex items-center justify-between">
          <h2 className="text-[17px] font-bold">가까운 약국 {list.length || ''}</h2>
          <span className="text-[13px] font-medium text-ink-muted">거리순</span>
        </div>
        {(!location || pharmacies.isPending) && <LoadingState message="근처 약국을 찾는 중이에요" />}
        {pharmacies.isError && <ErrorState message={pharmacies.error.message} onRetry={pharmacies.refetch} />}
        {pharmacies.isSuccess && list.length === 0 && <EmptyState title="근처에 약국이 없어요" />}
        {list[0]?.is_sample && <Notice tone="info">공공데이터 인증키가 없어서 가상의 샘플 약국을 보여드려요.</Notice>}

        <div role="radiogroup" aria-label="약국" className="flex flex-col gap-2.5">
          {list.map((p) => {
            const on = p.ext_id === selectedId
            return (
              <button
                key={p.ext_id}
                type="button"
                role="radio"
                aria-checked={on}
                onClick={() => setSelectedId(p.ext_id)}
                className={`flex items-center gap-3 rounded-2xl px-4 py-3.5 text-left ${on ? 'border-2 border-primary bg-primary-soft' : 'border border-line bg-white'}`}
              >
                <span className={`flex size-10 shrink-0 items-center justify-center rounded-full ${on ? 'bg-white text-primary' : 'bg-surface text-ink-muted'}`}>
                  <Icon name="store" size={20} />
                </span>
                <span className="flex flex-1 flex-col gap-0.5">
                  <span className="text-[15px] font-bold">{p.name}</span>
                  <span className="text-[13px] text-ink-muted">{p.address}</span>
                  <span className="text-[13px]">
                    <b className="text-primary">{p.distance_m < 1000 ? `${p.distance_m}m` : `${(p.distance_m / 1000).toFixed(1)}km`}</b>
                    {p.open_hours && <span className="text-ink-muted"> · 오늘 {p.open_hours}</span>}
                  </span>
                </span>
                <span className={`flex size-[22px] shrink-0 items-center justify-center rounded-full ${on ? 'bg-primary text-white' : 'border-2 border-line'}`}>
                  {on && <Icon name="checkMark" size={14} />}
                </span>
              </button>
            )
          })}
        </div>
        <p className="text-xs text-ink-muted">데모라서 실제 약국에는 처방전이 전송되지 않아요</p>
      </div>

      <div className="sticky bottom-0 mt-auto flex flex-col gap-2 border-t border-line bg-white px-5 pt-3 pb-6">
        {formError && <p role="alert" className="text-[13px] text-wait">{formError}</p>}
        <Button className="w-full" disabled={send.isPending} onClick={handleSend}>
          {send.isPending ? '보내는 중…' : selected ? `${selected.name}으로 처방전 보내기` : '처방전 보내기'}
        </Button>
      </div>
    </div>
  )
}

function Notice({ tone, children }) {
  return (
    <p className={`flex gap-2 rounded-xl px-3.5 py-3 text-[13px] font-medium ${tone === 'wait' ? 'bg-wait-soft text-wait' : 'bg-primary-soft text-primary'}`}>
      <Icon name="info" size={18} className="shrink-0" />
      {children}
    </p>
  )
}
