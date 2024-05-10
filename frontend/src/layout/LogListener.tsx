import { createContext, useEffect, useState } from "react";
import { getServerUrl } from "../api/getServerUrl";

const serverUrl = getServerUrl();

export const LogsContext = createContext<string[]>([]);

const LogListener = ({children}: {children: React.ReactNode | React.ReactNode[]}) => {
  const [logs, setLogs] = useState<string[]>([]);

  useEffect(() => {
    const evtSource = new EventSource(`${serverUrl}/logs`);
    evtSource.onmessage = (ev) => {
      setLogs((prev) => [...prev, ev.data]);
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