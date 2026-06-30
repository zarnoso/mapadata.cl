function format(level, message, meta = {}) {
  return JSON.stringify({
    ts: new Date().toISOString(),
    level,
    message,
    ...meta
  });
}

export const logger = {
  info(message, meta) {
    console.log(format('info', message, meta));
  },
  warn(message, meta) {
    console.warn(format('warn', message, meta));
  },
  error(message, meta) {
    console.error(format('error', message, meta));
  }
};
