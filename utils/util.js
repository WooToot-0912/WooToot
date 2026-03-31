const formatTime = date => {
  const year = date.getFullYear()
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hour = date.getHours()
  const minute = date.getMinutes()
  const second = date.getSeconds()

  return `${[year, month, day].map(formatNumber).join('/')} ${[hour, minute, second].map(formatNumber).join(':')}`
}

const formatNumber = n => {
  n = n.toString()
  return n[1] ? n : `0${n}`
}

// URL 路径处理函数 - 避免/api重复
const joinUrl = (base, path) => {
  // 确保基础URL没有尾随斜杠
  if (base.endsWith('/')) {
    base = base.slice(0, -1);
  }
  
  // 确保路径以斜杠开头
  if (!path.startsWith('/')) {
    path = '/' + path;
  }
  
  // 避免/api重复
  if (base.endsWith('/api') && path.startsWith('/api')) {
    return base + path.substring(4);
  }
  
  return base + path;
}

module.exports = {
  formatTime,
  joinUrl
}
