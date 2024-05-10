import { createContext, useEffect, useState } from "react";
import { getServerUrl } from "../api/getServerUrl";
import { Log } from "../types/Log";

const serverUrl = getServerUrl();

export const LogsContext = createContext<Log[]>([]);

const LogListener = ({children}: {children: React.ReactNode | React.ReactNode[]}) => {
  const [logs, setLogs] = useState<Log[]>([]);

  useEffect(() => {
    const evtSource = new EventSource(`${serverUrl}/logs`);
    evtSource.onmessage = (ev) => {
      const data = JSON.parse(ev.data).record;
      const timestamp = new Date(data.time.repr).toLocaleString();
      const level = data.level.name;
      const message = `${data.name}:${data.module}:${data.line} - ${data.message}`;

      const log: Log = {
        timestamp,
        level,
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
  )
}

export default LogListener;