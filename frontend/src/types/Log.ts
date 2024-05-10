export type LogLevels = "NOTSET" | "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";

export type Log = {
  timestamp: string,
  level: LogLevels,
  icon: string,
  logLevelNum: number,
  message: string
}