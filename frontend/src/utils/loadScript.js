// 외부 SDK(<script>)를 한 번만 불러온다. npm 패키지를 추가하지 않고 공식 CDN 주소를 그대로 쓴다 (토스 결제창, 카카오맵)
const loading = {}

export function loadScript(src) {
  loading[src] ??= new Promise((resolve, reject) => {
    const script = document.createElement('script')
    script.src = src
    script.async = true
    script.onload = resolve
    script.onerror = () => {
      delete loading[src]
      reject(new Error('외부 스크립트를 불러오지 못했어요. 네트워크를 확인해주세요'))
    }
    document.head.appendChild(script)
  })
  return loading[src]
}
