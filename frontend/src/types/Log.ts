import { z } from "zod";

export const LogLevels = z.enum(["NOTSET", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]);

export type LogLevels = z.infer<typeof LogLevels>;

export const RawLog = z.object({
  text: z.string(),
  record: z.object({
    elapsed: z.object({
      repr: z.string(),
      seconds: z.number()
    }),
    exception: z.any(),
    extra: z.record(z.any()),
    file: z.object({
      name: z.string(),
      path: z.string()
    }),
    function: z.string(),
    level: z.object({
      icon: z.string(),
      name: LogLevels,
      no: z.number()
    }),
    line: z.number(),
    message: z.string(),
    module: z.string(),
    name: z.string(),
    process: z.object({
      id: z.number(),
      name: z.string(),
    }),
    thread: z.object({
      id: z.number(),
      name: z.string()
    }),
    time: z.object({
      repr: z.string(),
      timestamp: z.number()
    })
  })
});

export type RawLog = z.infer<typeof RawLog>;

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