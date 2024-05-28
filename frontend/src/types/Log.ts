export type LogLevels = "NOTSET" | "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";

export type Log = {
  timestamp: string,
  /** Log level of message */
  level: LogLevels,
  /** Icon corresponding to loglevel */
  icon: string,
  /** Number corresponding to loglevel */
  logLevelNum: number,
  message: string
}