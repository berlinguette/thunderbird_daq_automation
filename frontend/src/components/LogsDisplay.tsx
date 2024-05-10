import { Card, CardBody, VStack } from "@chakra-ui/react";
import { useContext, useEffect, useMemo, useRef } from "react";
import { LogsContext } from "../layout/LogListener";
import LogCard from "./LogCard";
import { LogLevels } from "../types/Log";
import { logLevelNumbers } from "../helpers/logging";

const LogsDisplay = ({ lowestLogLevel }: { lowestLogLevel: LogLevels }) => {
  const logs = useContext(LogsContext);
  const logWindowRef = useRef<HTMLDivElement>(null);

  const filteredLogs = useMemo(
    () => logs.filter((msg) => msg.logLevelNum >= logLevelNumbers[lowestLogLevel]),
    [logs, lowestLogLevel]
  );

  useEffect(() => {
    if (logWindowRef.current) {
      logWindowRef.current.scroll({
        behavior: "smooth",
        top: logWindowRef.current.scrollHeight
      });
    }
  }, [filteredLogs]);

  return (
    <Card variant="filled" flexGrow={1} minHeight={0} p="var(--card-padding)">
      <CardBody p={0} minHeight={0} overflowY="scroll" ref={logWindowRef}>
        <VStack spacing={3} align="stretch">
          {filteredLogs.
            map((msg) => <LogCard msg={msg} key={msg.timestamp + msg.message} />)}
        </VStack>
      </CardBody>
    </Card>
  )
};

export default LogsDisplay;