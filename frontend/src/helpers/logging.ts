import { LogLevels } from "../types/Log";

type LevelColors = {
  colorScheme: string,
  background: string,
  textColor: string
}

type LogColors = {
  "CRITICAL": LevelColors
  "ERROR": LevelColors,
  "WARNING": LevelColors,
  "INFO": LevelColors,
  "DEBUG": LevelColors,
  "NOTSET": LevelColors
}

const logBaseColors = {
  "CRITICAL": "red",
  "ERROR": "orange",
  "WARNING": "yellow",
  "INFO": "white",
  "DEBUG": "gray",
  "NOTSET": "blue"
};

export const logColors = Object.entries(logBaseColors).reduce((acc, [level, color]) => {
  return {
    ...acc,
    [level]: {
      colorScheme: color,
      background: color === "white" ? color : `${color}.50`,
      textColor: color === "white" ? "black" : `${color}.700`
    }
  };
}, {} as LogColors);

export const orderedLogLevels: LogLevels[] = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"];

export const logLevelNumbers = {
  "CRITICAL": 50,
  "ERROR": 40,
  "WARNING": 30,
  "INFO": 20,
  "DEBUG": 10,
  "NOTSET": 0
}