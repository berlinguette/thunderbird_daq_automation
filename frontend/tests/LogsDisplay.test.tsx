import React from "react";
import { describe, expect, it } from "vitest";
import { render, screen } from "./testUtils";
import { LogsContext } from "../src/layout/LogListener";
import LogsDisplay from "../src/components/logs/LogsDisplay";
import { Log } from "../src/types/Log";
import { logLevelNumbers, orderedLogLevels } from "../src/helpers/logging";

const fakeLogs: Log[] = orderedLogLevels.map((level, i) => {
  return {
    message: `fake log ${i}`,
    level: level,
    logLevelNum: logLevelNumbers[level],
    timestamp: (i*100).toString(),
    icon: ""
  }
});

describe("LogsDisplay", () => {
  it("can filter logs by minimum log level", () => {
    // Fake scroll function so LogsDisplay won't error
    window.HTMLElement.prototype.scroll = () => {};

    render(
      <LogsContext.Provider value={fakeLogs}>
        <LogsDisplay lowestLogLevel="INFO" />
      </LogsContext.Provider>
    );

    // everything that is >= INFO loglevel
    orderedLogLevels.slice(0, 4).forEach((level) => {
      expect(screen.getByText(level)).toBeInTheDocument();
    });
    // everything that is < INFO loglevel
    orderedLogLevels.slice(4).forEach((level) => {
      expect(screen.queryByText(level)).not.toBeInTheDocument();
    });
  });
});