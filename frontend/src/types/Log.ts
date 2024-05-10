export type Log = {
  timestamp: string,
  level: "NOTSET" | "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL",
  icon: string,
  message: string
}