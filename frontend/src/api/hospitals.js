import client from './client'

// params: { department, lat, lng, radius }
export const getHospitals = (params) => client.get('/hospitals', { params }).then((r) => r.data)
