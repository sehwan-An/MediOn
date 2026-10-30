import { useEffect, useRef, useState } from 'react'
import { loadScript } from '../../utils/loadScript'

const KEY = import.meta.env.VITE_KAKAO_MAP_KEY

// 카카오맵 (M-1, 2차 병원 찾기에서도 재사용). 키가 없으면 지도 대신 안내만 보여준다
// markers: [{ id, lat, lng, title }], selectedId 는 마커를 크게 표시하지 않고 지도 중심만 옮긴다
export default function KakaoMap({ center, markers, selectedId, onSelect }) {
  const box = useRef(null)
  const map = useRef(null)
  const [error, setError] = useState(KEY ? '' : '카카오 JavaScript 키(VITE_KAKAO_MAP_KEY)를 넣으면 지도가 보여요')

  // 지도 만들기 + 마커 다시 그리기
  useEffect(() => {
    if (!KEY) return undefined
    let drawn = []
    let cancelled = false
    loadScript(`https://dapi.kakao.com/v2/maps/sdk.js?appkey=${KEY}&autoload=false`)
      .then(() => new Promise((resolve) => window.kakao.maps.load(resolve)))
      .then(() => {
        if (cancelled || !box.current) return
        const { maps } = window.kakao
        map.current ??= new maps.Map(box.current, { center: new maps.LatLng(center.lat, center.lng), level: 4 })
        drawn = markers.map((m) => {
          const marker = new maps.Marker({ map: map.current, position: new maps.LatLng(m.lat, m.lng), title: m.title })
          maps.event.addListener(marker, 'click', () => onSelect?.(m.id))
          return marker
        })
      })
      .catch(() => setError('지도를 불러오지 못했어요. 카카오 콘솔에 http://localhost:5173 도메인이 등록됐는지 확인해주세요'))
    return () => {
      cancelled = true
      drawn.forEach((m) => m.setMap(null))
    }
  }, [center.lat, center.lng, markers, onSelect])

  useEffect(() => {
    const target = markers.find((m) => m.id === selectedId)
    if (map.current && target) map.current.panTo(new window.kakao.maps.LatLng(target.lat, target.lng))
  }, [selectedId, markers])

  if (error) {
    return <div className="flex h-56 items-center justify-center bg-surface px-6 text-center text-[13px] text-ink-muted">{error}</div>
  }
  return <div ref={box} role="img" aria-label="근처 약국 지도" className="h-56 w-full bg-surface" />
}
