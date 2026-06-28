function startOfToday() {
  const date = new Date()
  date.setHours(0, 0, 0, 0)
  return date
}

function addDays(date: Date, days: number) {
  const next = new Date(date)
  next.setDate(next.getDate() + days)
  return next
}

export function formatLocalDate(date: Date) {
  const year = date.getFullYear()
  const month = `${date.getMonth() + 1}`.padStart(2, '0')
  const day = `${date.getDate()}`.padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function recentDateRange(days: number): [string, string] {
  const end = startOfToday()
  const start = addDays(end, -(days - 1))
  return [formatLocalDate(start), formatLocalDate(end)]
}

function lastMonthRange() {
  const today = startOfToday()
  const start = new Date(today.getFullYear(), today.getMonth() - 1, 1)
  const end = new Date(today.getFullYear(), today.getMonth(), 0)
  return [start, end]
}

export const dateRangeShortcuts = [
  {
    text: '过去7天',
    value: () => {
      const end = startOfToday()
      return [addDays(end, -6), end]
    }
  },
  {
    text: '过去30天',
    value: () => {
      const end = startOfToday()
      return [addDays(end, -29), end]
    }
  },
  {
    text: '上个月',
    value: lastMonthRange
  }
]
