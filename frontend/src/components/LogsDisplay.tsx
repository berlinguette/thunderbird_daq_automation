import { Card, CardBody, VStack } from "@chakra-ui/react";
import { useContext, useEffect, useRef } from "react";
import { LogsContext } from "../layout/LogListener";
import LogCard from "./LogCard";

const LogsDisplay = () => {
  const logs = useContext(LogsContext);
  const logWindowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (logWindowRef.current) {
      logWindowRef.current.scroll({
        behavior: "smooth",
        top: logWindowRef.current.scrollHeight
      });
    }
  }, [logs]);

  return (
    <Card variant="filled" flexGrow={1} minHeight={0} p="var(--card-padding)">
      <CardBody p={0} minHeight={0} overflowY="scroll" ref={logWindowRef}>
        <VStack spacing={3} align="stretch">
          {logs.map((msg) => <LogCard msg={msg} />)}
        </VStack>
      </CardBody>
    </Card>
  )
};

export default LogsDisplay;