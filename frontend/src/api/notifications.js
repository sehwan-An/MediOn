import client from './client'

// 알림 (F-1, F-2). 로그인한 사용자만
export const getNotifications = (params) => client.get('/notifications', { params }).then((r) => r.data)
export const getUnreadCount = () => client.get('/notifications/unread-count').then((r) => r.data)
export const markNotificationRead = (id) => client.patch(`/notifications/${id}/read`).then((r) => r.data)
export const markAllNotificationsRead = () => client.post('/notifications/read-all')
