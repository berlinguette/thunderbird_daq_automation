export type Log = {
  timestamp: string,
  level: "NOTSET" | "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL",
  message: string
}