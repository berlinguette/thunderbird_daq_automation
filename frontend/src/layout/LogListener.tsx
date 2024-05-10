import { createContext, useEffect, useState } from "react";
import { getServerUrl } from "../api/getServerUrl";
import { Log } from "../types/Log";

const serverUrl = getServerUrl();

export const LogsContext = createContext<Log[]>([]);

const LogListener = ({ children }: { children: React.ReactNode | React.ReactNode[] }) => {
  const [logs, setLogs] = useState<Log[]>([]);

  useEffect(() => {
    const evtSource = new EventSource(`${serverUrl}/logs`);
    evtSource.onmessage = (ev) => {
      const data = JSON.parse(ev.data).record;
      const timestamp = data.time.repr;
      const level = data.level.name;
      const icon = data.level.icon;
      const logLevelNum = data.level.no;
      const message = `${data.name}:${data.module}:${data.line} - ${data.message}`;

      const log: Log = {
        timestamp,
        level,
        icon,
        logLevelNum,
        message
      }
      setLogs((prev) => [...prev, log]);
    };

    return () => evtSource.close();
  }, []);

  return (
    <LogsContext.Provider value={logs}>
      {children}
    </LogsContext.Provider>
  );
};

export default LogListener;